"""Entity command tests: success refreshes state, failures surface to the user."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.breezart.const import (
    TRANSLATION_KEY_CLIMATE,
    TRANSLATION_KEY_FAN_SPEED,
    TRANSLATION_KEY_POWER_SWITCH,
)

from .conftest import entity_id_for

# number.py builds this unique_id suffix by hand (not from the translation key);
# it must stay stable so existing entities keep their IDs.
TARGET_TEMP_UID = "target_temp"

# (platform, key, service, service data, client method, expected call args)
COMMANDS = [
    ("number", TARGET_TEMP_UID, "set_value", {"value": 24}, "set_temperature", (24,)),
    ("number", TRANSLATION_KEY_FAN_SPEED, "set_value", {"value": 5}, "set_fan_speed", (5,)),
    ("switch", TRANSLATION_KEY_POWER_SWITCH, "turn_off", {}, "set_power", (False,)),
    ("switch", TRANSLATION_KEY_POWER_SWITCH, "turn_on", {}, "set_power", (True,)),
    ("climate", TRANSLATION_KEY_CLIMATE, "set_temperature", {"temperature": 23}, "set_temperature", (23,)),
    ("climate", TRANSLATION_KEY_CLIMATE, "set_fan_mode", {"fan_mode": "4"}, "set_fan_speed", (4,)),
    ("climate", TRANSLATION_KEY_CLIMATE, "turn_off", {}, "set_power", (False,)),
]
IDS = [f"{c[0]}.{c[2]}" for c in COMMANDS]


@pytest.mark.parametrize(("platform", "key", "service", "data", "method", "args"), COMMANDS, ids=IDS)
async def test_command_success(
    hass: HomeAssistant, setup_integration, fake_client, platform, key, service, data, method, args
) -> None:
    """Commands reach the client with the right arguments."""
    await hass.services.async_call(
        platform, service, {"entity_id": entity_id_for(hass, platform, key), **data}, blocking=True
    )
    getattr(fake_client, method).assert_awaited_once_with(*args)


@pytest.mark.parametrize(("platform", "key", "service", "data", "method", "args"), COMMANDS, ids=IDS)
async def test_command_failure_raises_translated_error(
    hass: HomeAssistant, setup_integration, fake_client, platform, key, service, data, method, args
) -> None:
    """Device errors become a translated HomeAssistantError, not an unknown error."""
    getattr(fake_client, method).side_effect = TimeoutError("No response")

    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            platform, service, {"entity_id": entity_id_for(hass, platform, key), **data}, blocking=True
        )

    assert exc_info.value.translation_domain == "breezart"
    assert exc_info.value.translation_key == "command_failed"
    assert exc_info.value.translation_placeholders == {"error": "No response"}


async def test_climate_failure_reverts_optimistic_state(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """A failed set_temperature restores the device's real target."""
    entity_id = entity_id_for(hass, "climate", TRANSLATION_KEY_CLIMATE)
    fake_client.set_temperature.side_effect = ConnectionError("down")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "climate", "set_temperature", {"entity_id": entity_id, "temperature": 30}, blocking=True
        )

    assert hass.states.get(entity_id).attributes["temperature"] == 22.0
