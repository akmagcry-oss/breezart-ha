"""Diagnostics tests: sensitive fields are redacted and state snapshot is returned."""
from __future__ import annotations

from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from custom_components.breezart.const import PROTOCOL_NATIVE_TCP
from custom_components.breezart.diagnostics import async_get_config_entry_diagnostics

from .conftest import HOST


async def test_config_entry_diagnostics_redacts_secrets_and_includes_snapshot(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """Diagnostics redacts host/password and exposes device & coordinator state."""
    entry = setup_integration
    fake_client._unsupported_blocks = {12205}

    diag = await async_get_config_entry_diagnostics(hass, entry)

    # Sensitive fields must be redacted
    assert diag["entry"]["data"][CONF_PASSWORD] == REDACTED
    assert diag["entry"]["data"][CONF_HOST] == REDACTED
    assert HOST not in str(diag["entry"])
    assert "21579" not in str(diag)

    # Device capabilities and protocol info must be present
    device = diag["device"]
    assert device["protocol_type"] == PROTOCOL_NATIVE_TCP
    assert device["connected"] is True
    assert device["capabilities"]["temp_min"] == 5
    assert device["capabilities"]["temp_max"] == 35
    assert device["capabilities"]["speed_max"] == 10
    assert device["capabilities"]["unsupported_modbus_blocks"] == [12205]

    # Coordinator snapshot must include current polled data and notification settings
    coord = diag["coordinator"]
    assert coord["last_update_success"] is True
    assert coord["data"]["temperature"] == 21.0
    assert coord["data"]["temp_room"] == 22.5
    assert coord["notify_settings"]["notify_overheat"] is True
