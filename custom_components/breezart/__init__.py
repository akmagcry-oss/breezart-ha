"""Custom integration for Breezart ventilation systems (Native TCP 1560 & Modbus TCP 502)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MODEL,
    CONF_NOTIFY_SERVICE,
    CONF_PROTOCOL,
    CONF_SLAVE_ID,
    CONF_SPEED_MAX,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_VAV_ZONES,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_MODEL,
    DATA_PROTOCOL,
    DATA_RELOAD_SNAPSHOT,
    DEFAULT_MODEL,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    NOTIFICATION_SETTING_KEYS,
)
from .coordinator import BreezartDataCoordinator, create_breezart_client, resolve_port

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]

BLUEPRINT_FILENAMES: tuple[str, ...] = (
    "breezart_co2_boost.yaml",
    "breezart_night_quiet_mode.yaml",
    "breezart_away_eco_mode.yaml",
    "breezart_window_open_pause.yaml",
)


def parse_blueprint_metadata(raw_yaml: str) -> dict[str, Any]:
    """Extract and validate structural metadata from a Home Assistant blueprint YAML string."""
    name = ""
    description = ""
    domain = ""
    mode = "single"
    has_trigger = False
    has_action = False
    inputs: list[str] = []
    in_blueprint = False
    in_input = False
    in_description = False

    for line in raw_yaml.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0:
            in_blueprint = stripped == "blueprint:"
            in_input = False
            in_description = False
            if stripped.startswith(("trigger:", "triggers:")):
                has_trigger = True
            elif stripped.startswith(("action:", "actions:")):
                has_action = True
            elif stripped.startswith("mode:"):
                mode = stripped.split(":", 1)[1].strip().strip("\"'")
            continue

        if in_blueprint:
            if indent == 2:
                in_input = stripped == "input:"
                in_description = False
                if stripped.startswith("name:"):
                    name = stripped.split(":", 1)[1].strip().strip("\"'")
                elif stripped.startswith("domain:"):
                    domain = stripped.split(":", 1)[1].strip().strip("\"'")
                elif stripped.startswith("description:"):
                    val = stripped.split(":", 1)[1].strip()
                    if val in {">", "|", ">-", "|-"}:
                        in_description = True
                    else:
                        description = val.strip("\"'")
            elif in_description and indent >= 4 and not description:
                description = stripped
            elif in_input and indent == 4 and stripped.endswith(":"):
                inputs.append(stripped[:-1].strip())

    return {
        "name": name,
        "description": description,
        "domain": domain,
        "mode": mode,
        "inputs": inputs,
        "has_trigger": has_trigger,
        "has_action": has_action,
    }


def install_blueprints(
    config_dir: Path, source_dir: Path | None = None
) -> list[Path]:
    """Idempotently copy bundled automation blueprints into `<config>/blueprints/automation/breezart/`."""
    src_base = source_dir or (
        Path(__file__).resolve().parent / "blueprints" / "automation" / DOMAIN
    )
    target_base = Path(config_dir) / "blueprints" / "automation" / DOMAIN
    target_base.mkdir(parents=True, exist_ok=True)

    installed: list[Path] = []
    for filename in BLUEPRINT_FILENAMES:
        src_file = src_base / filename
        if not src_file.is_file():
            continue
        dst_file = target_base / filename
        content = src_file.read_text(encoding="utf-8")
        if not dst_file.is_file() or dst_file.read_text(encoding="utf-8") != content:
            dst_file.write_text(content, encoding="utf-8")
        installed.append(dst_file)
    return installed


async def async_install_blueprints(hass: HomeAssistant) -> None:
    """Install bundled Breezart automation blueprints in the Home Assistant config directory."""
    config = getattr(hass, "config", None)
    path_fn = getattr(config, "path", None)
    if not callable(path_fn) or not hasattr(hass, "async_add_executor_job"):
        return
    try:
        config_dir = Path(path_fn())
        await hass.async_add_executor_job(install_blueprints, config_dir)
    except OSError as err:
        _LOGGER.debug("Skipping blueprint auto-installation: %s", err)


def _reload_snapshot(entry: ConfigEntry) -> dict:
    """Return the merged entry settings that require a reload when changed.

    Notification toggles are excluded: they are applied live by the coordinator.
    """
    merged = {**entry.data, **entry.options}
    return {k: v for k, v in merged.items() if k not in NOTIFICATION_SETTING_KEYS}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Breezart from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await async_install_blueprints(hass)
    model_id = entry.options.get(
        CONF_MODEL, entry.data.get(CONF_MODEL, DEFAULT_MODEL)
    )
    protocol = entry.options.get(
        CONF_PROTOCOL, entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
    )
    slave_id = int(
        entry.options.get(
            CONF_SLAVE_ID, entry.data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
        )
    )
    raw_speed_max = entry.options.get(CONF_SPEED_MAX, entry.data.get(CONF_SPEED_MAX))
    raw_temp_min = entry.options.get(CONF_TEMP_MIN, entry.data.get(CONF_TEMP_MIN))
    raw_temp_max = entry.options.get(CONF_TEMP_MAX, entry.data.get(CONF_TEMP_MAX))
    raw_vav_zones = entry.options.get(CONF_VAV_ZONES, entry.data.get(CONF_VAV_ZONES))

    speed_max = int(raw_speed_max) if raw_speed_max is not None else None
    temp_min = int(raw_temp_min) if raw_temp_min is not None else None
    temp_max = int(raw_temp_max) if raw_temp_max is not None else None
    vav_zones = int(raw_vav_zones) if raw_vav_zones is not None and int(raw_vav_zones) > 0 else None

    notify_service = str(
        entry.options.get(
            CONF_NOTIFY_SERVICE,
            entry.data.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
        )
    )
    notify_settings: dict[str, bool] = {
        key: bool(entry.options.get(key, entry.data.get(key, True)))
        for key in NOTIFICATION_SETTING_KEYS
    }

    # The options flow stores the port it verified; older entries only have it in data.
    port = resolve_port(
        protocol,
        int(entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))),
    )
    password = entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)

    kw_args = {}
    if vav_zones is not None:
        kw_args["vav_zones"] = vav_zones

    client = create_breezart_client(
        host=entry.data[CONF_HOST],
        port=port,
        password=password,
        model=model_id,
        protocol=protocol,
        slave_id=slave_id,
        speed_max=speed_max,
        temp_min=temp_min,
        temp_max=temp_max,
        **kw_args,
    )
    coordinator = BreezartDataCoordinator(
        hass,
        client,
        model=model_id,
        notify_settings=notify_settings,
        notify_service=notify_service,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        DATA_MODEL: model_id,
        DATA_PROTOCOL: client.protocol_type,
        DATA_RELOAD_SNAPSHOT: _reload_snapshot(entry),
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload on connection/model changes; apply notification toggles live."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not entry_data or entry_data[DATA_RELOAD_SNAPSHOT] != _reload_snapshot(entry):
        await hass.config_entries.async_reload(entry.entry_id)
        return

    coordinator: BreezartDataCoordinator = entry_data[DATA_COORDINATOR]
    for key in NOTIFICATION_SETTING_KEYS:
        coordinator.set_notification_enabled(
            key, bool(entry.options.get(key, entry.data.get(key, True)))
        )
    coordinator.async_update_listeners()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        data[DATA_COORDINATOR].clear_repair_issues()
        await data[DATA_CLIENT].disconnect()
    return unload_ok
