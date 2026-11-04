"""Setup, reload, and port-resolution tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.breezart.const import (
    CONF_PROTOCOL,
    DATA_COORDINATOR,
    DOMAIN,
    KEY_NOTIFY_POWER,
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
    TRANSLATION_KEY_CLIMATE,
)
from custom_components.breezart.coordinator import resolve_port

from .conftest import entity_id_for


async def test_setup_and_unload(hass: HomeAssistant, setup_integration, fake_client) -> None:
    """The entry loads, creates entities, and disconnects on unload."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id_for(hass, "climate", TRANSLATION_KEY_CLIMATE)) is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not fake_client.is_connected


@pytest.mark.parametrize(
    ("protocol", "port", "expected"),
    [
        (PROTOCOL_MODBUS_TCP, 1560, 502),
        (PROTOCOL_NATIVE_TCP, 502, 1560),
        (PROTOCOL_MODBUS_TCP, 502, 502),
        (PROTOCOL_NATIVE_TCP, 1560, 1560),
        (PROTOCOL_MODBUS_TCP, 5020, 5020),  # custom ports are kept
        (PROTOCOL_AUTO, 1560, 1560),
    ],
)
def test_resolve_port(protocol: str, port: int, expected: int) -> None:
    """Default ports follow the protocol; custom ports are left alone."""
    assert resolve_port(protocol, port) == expected


async def test_legacy_protocol_option_uses_matching_port(
    hass: HomeAssistant, config_entry, mock_create_client
) -> None:
    """An entry switched to Modbus in options before the fix connects on 502."""
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_PROTOCOL: PROTOCOL_MODBUS_TCP}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    kwargs = mock_create_client.call_args.kwargs
    assert kwargs["protocol"] == PROTOCOL_MODBUS_TCP
    assert kwargs["port"] == 502


async def test_port_from_options_takes_precedence(
    hass: HomeAssistant, config_entry, mock_create_client
) -> None:
    """The port verified by the options flow overrides the original one."""
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_PROTOCOL: PROTOCOL_MODBUS_TCP, CONF_PORT: 5020}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_create_client.call_args.kwargs["port"] == 5020


async def test_notification_toggle_does_not_reload(
    hass: HomeAssistant, setup_integration
) -> None:
    """Toggling a notification switch applies live without reloading."""
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id_for(hass, "switch", KEY_NOTIFY_POWER)}, blocking=True
        )
        await hass.async_block_till_done()

    mock_reload.assert_not_called()
    assert entry.options[KEY_NOTIFY_POWER] is False
    assert coordinator.is_notification_enabled(KEY_NOTIFY_POWER) is False
    assert hass.states.get(entity_id_for(hass, "switch", KEY_NOTIFY_POWER)).state == "off"


async def test_noop_toggle_does_not_swallow_next_reload(
    hass: HomeAssistant, setup_integration
) -> None:
    """Regression: turning on an already-on switch must not skip the next real reload."""
    entry = setup_integration
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id_for(hass, "switch", KEY_NOTIFY_POWER)}, blocking=True
    )
    await hass.async_block_till_done()

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_PROTOCOL: PROTOCOL_MODBUS_TCP}
        )
        await hass.async_block_till_done()

    mock_reload.assert_called_once_with(entry.entry_id)


async def test_notification_toggle_from_options_applies_live(
    hass: HomeAssistant, setup_integration
) -> None:
    """Changing only a toggle via options updates the coordinator and the switch."""
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, KEY_NOTIFY_POWER: False}
        )
        await hass.async_block_till_done()

    mock_reload.assert_not_called()
    assert coordinator.is_notification_enabled(KEY_NOTIFY_POWER) is False
    assert hass.states.get(entity_id_for(hass, "switch", KEY_NOTIFY_POWER)).state == "off"
