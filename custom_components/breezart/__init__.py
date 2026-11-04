"""Custom integration for Breezart ventilation systems (Native TCP 1560 & Modbus TCP 502)."""
from __future__ import annotations

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
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_MODEL,
    DATA_PROTOCOL,
    DATA_SKIP_RELOAD,
    DEFAULT_MODEL,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    NOTIFICATION_SETTING_KEYS,
)
from .coordinator import BreezartDataCoordinator, create_breezart_client

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Breezart from a config entry."""
    hass.data.setdefault(DOMAIN, {})
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

    speed_max = int(raw_speed_max) if raw_speed_max is not None else None
    temp_min = int(raw_temp_min) if raw_temp_min is not None else None
    temp_max = int(raw_temp_max) if raw_temp_max is not None else None

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

    port = int(entry.data.get(CONF_PORT, DEFAULT_PORT))
    password = entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)

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
        DATA_SKIP_RELOAD: False,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if entry_data and entry_data.get(DATA_SKIP_RELOAD):
        entry_data[DATA_SKIP_RELOAD] = False
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data[DATA_CLIENT].disconnect()
    return unload_ok
