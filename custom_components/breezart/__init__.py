"""Custom integration for Breezart ventilation systems."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MODEL,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_MODEL,
    DEFAULT_MODEL,
    DOMAIN,
)
from .coordinator import BreezartDataCoordinator, BreezartTCPClient

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
    client = BreezartTCPClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        password=entry.data[CONF_PASSWORD],
        model=model_id,
    )
    coordinator = BreezartDataCoordinator(hass, client, model=model_id)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        DATA_MODEL: model_id,
    }

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data[DATA_CLIENT].disconnect()
    return unload_ok
