"""Diagnostics support for Breezart ventilation systems."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import BreezartClientType, BreezartDataCoordinator

TO_REDACT: set[str] = {
    CONF_HOST,
    CONF_PASSWORD,
    "unique_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a Breezart config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: BreezartDataCoordinator = entry_data[DATA_COORDINATOR]
    client: BreezartClientType = entry_data[DATA_CLIENT]

    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "device": {
            "model_id": coordinator.model,
            "model_name": coordinator.model_name,
            "protocol_type": client.protocol_type,
            "protocol_version": getattr(client, "protocol_ver", None),
            "firmware_version": getattr(client, "firmware_ver", None),
            "port": getattr(client, "port", None),
            "slave_id": getattr(client, "slave_id", None),
            "connected": client.is_connected,
            "capabilities": {
                "temp_min": client.temp_min,
                "temp_max": client.temp_max,
                "humid_min": getattr(client, "humid_min", None),
                "humid_max": getattr(client, "humid_max", None),
                "speed_min": client.speed_min,
                "speed_max": client.speed_max,
                "has_heater": getattr(client, "has_heater", None),
                "has_cooler": getattr(client, "has_cooler", None),
                "has_humidifier": getattr(client, "has_humidifier", None),
                "has_vav": getattr(client, "has_vav", None),
                "vav_zones": getattr(client, "vav_zones", 0),
                "unsupported_modbus_blocks": sorted(
                    getattr(client, "_unsupported_blocks", set())
                ),
            },
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "consecutive_failures": coordinator._consecutive_failures,
            "was_online": coordinator._was_online,
            "notify_service": coordinator.notify_service,
            "notify_settings": dict(coordinator.notify_settings),
            "data": dict(coordinator.data) if coordinator.data else None,
        },
    }
