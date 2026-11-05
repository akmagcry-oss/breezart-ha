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


def test_evaluate_repair_issues_pure_logic() -> None:
    """Pure repair issue evaluation maps unit flags and filter pollution to RepairIssueSpec."""
    from custom_components.breezart.const import (
        ISSUE_CONTROLLER_ERROR,
        ISSUE_FILTER,
        ISSUE_FREEZE,
        ISSUE_OVERHEAT,
        KEY_CHANGE_FILTER,
        KEY_DANGER_FREEZE,
        KEY_DANGER_OVERHEAT,
        KEY_FILTER_DUST,
        KEY_IS_FATAL_ERR,
        KEY_MSG,
    )
    from custom_components.breezart.coordinator import evaluate_repair_issues

    # Healthy state -> no repair issues
    assert (
        evaluate_repair_issues(
            {KEY_FILTER_DUST: 20, KEY_DANGER_OVERHEAT: False},
            device_name="Breezart 550 Lux",
            host="192.168.1.121",
        )
        == {}
    )

    # Filter pollution >= 85% and overheat hazard -> 2 active issues
    issues = evaluate_repair_issues(
        {
            KEY_FILTER_DUST: 92,
            KEY_CHANGE_FILTER: True,
            KEY_DANGER_OVERHEAT: True,
            KEY_DANGER_FREEZE: True,
        },
        device_name="Breezart 550 Lux",
        host="192.168.1.121",
    )
    assert set(issues.keys()) == {ISSUE_FILTER, ISSUE_OVERHEAT, ISSUE_FREEZE}
    assert issues[ISSUE_FILTER].severity == "warning"
    assert issues[ISSUE_FILTER].placeholders["pollution"] == "92"
    assert issues[ISSUE_OVERHEAT].severity == "critical"
    assert issues[ISSUE_FREEZE].severity == "critical"

    # Generic fatal controller error when specific hazards are off
    err_issues = evaluate_repair_issues(
        {
            KEY_IS_FATAL_ERR: True,
            KEY_MSG: "Sensor fault E04",
        },
        device_name="Breezart 550 Lux",
        host="192.168.1.121",
    )
    assert set(err_issues.keys()) == {ISSUE_CONTROLLER_ERROR}
    assert err_issues[ISSUE_CONTROLLER_ERROR].severity == "error"
    assert err_issues[ISSUE_CONTROLLER_ERROR].placeholders["message"] == "Sensor fault E04"


async def test_repairs_issues_created_and_cleared_on_poll(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """Coordinator creates Repairs issues when alarms occur and deletes them when resolved."""
    from homeassistant.helpers import issue_registry as ir

    from custom_components.breezart.const import (
        DATA_COORDINATOR,
        DOMAIN,
        ISSUE_FILTER,
        ISSUE_OVERHEAT,
        KEY_CHANGE_FILTER,
        KEY_DANGER_OVERHEAT,
        KEY_FILTER_DUST,
    )
    from .conftest import HOST

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    registry = ir.async_get(hass)

    assert registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_FILTER}") is None
    assert registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_OVERHEAT}") is None

    # Trigger filter replacement and overheat alarm
    fake_client.state[KEY_CHANGE_FILTER] = True
    fake_client.state[KEY_FILTER_DUST] = 90
    fake_client.state[KEY_DANGER_OVERHEAT] = True
    await coordinator.async_refresh()

    filter_issue = registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_FILTER}")
    overheat_issue = registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_OVERHEAT}")
    assert filter_issue is not None
    assert filter_issue.severity == ir.IssueSeverity.WARNING
    assert overheat_issue is not None
    assert overheat_issue.severity == ir.IssueSeverity.CRITICAL

    # Clear alarms -> issues are automatically removed from Repairs panel
    fake_client.state[KEY_CHANGE_FILTER] = False
    fake_client.state[KEY_FILTER_DUST] = 10
    fake_client.state[KEY_DANGER_OVERHEAT] = False
    await coordinator.async_refresh()

    assert registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_FILTER}") is None
    assert registry.async_get_issue(DOMAIN, f"{HOST}_{ISSUE_OVERHEAT}") is None


def test_integrate_energy_kwh_pure_logic() -> None:
    """Pure Riemann integration accumulates Watt-seconds into kWh monotonically."""
    from custom_components.breezart.coordinator import integrate_energy_kwh

    # 1800 W for 60 seconds = 1800 * 60 / 3_600_000 = 0.03 kWh
    val = integrate_energy_kwh(0.0, 1800, 60.0)
    assert val == pytest.approx(0.03, rel=1e-5)

    # Zero or None power keeps cumulative total unchanged (monotonic)
    assert integrate_energy_kwh(val, 0, 60.0) == pytest.approx(0.03, rel=1e-5)
    assert integrate_energy_kwh(val, None, 60.0) == pytest.approx(0.03, rel=1e-5)
    assert integrate_energy_kwh(val, 1800, -5.0) == pytest.approx(0.03, rel=1e-5)


async def test_energy_consumption_sensor_accumulates_kwh(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """Energy sensor is created with TOTAL_INCREASING kWh and accumulates energy on polls."""
    from custom_components.breezart.const import (
        DATA_COORDINATOR,
        DOMAIN,
        KEY_ENERGY_CONSUMPTION,
        KEY_POWER_CONSUMPTION,
    )

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entity_id = entity_id_for(hass, "sensor", KEY_ENERGY_CONSUMPTION)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "kWh"
    assert state.attributes.get("device_class") == "energy"
    assert state.attributes.get("state_class") == "total_increasing"

    # Seed 1.5 kWh and simulate 60s elapsed at 1800 W (+0.03 kWh -> 1.53 kWh)
    coordinator.seed_energy_kwh(1.5)
    fake_client.sensors[KEY_POWER_CONSUMPTION] = 1800
    coordinator._cached_sensors = {}
    coordinator._last_energy_ts -= 60.0
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    updated = hass.states.get(entity_id)
    assert float(updated.state) == pytest.approx(1.53, rel=1e-2)


def test_decode_schedule_and_timer_pure_logic() -> None:
    """Pure decoders extract active scenario, timer/schedule flags, source, and HH:MM time."""
    from custom_components.breezart.const import SCENARIO_STANDBY
    from custom_components.breezart.coordinator import (
        decode_modbus_schedule_state,
        decode_native_schedule_state,
    )

    # Native VSt07: bit 2 (ScenAllow=1) | bits 6..9 (scen=3 -> 3<<6) | bits 10..12 (Timer1=1 -> 1<<10)
    bit_mode = (1 << 2) | (3 << 6) | (1 << 10)
    # Time field: hours=14 (high byte), minutes=35 (low byte) -> (14 << 8) | 35
    time_word = (14 << 8) | 35
    nat = decode_native_schedule_state(format(bit_mode, "x"), format(time_word, "x"))
    assert nat.active_scenario == 3
    assert nat.schedule_enabled is True
    assert nat.activation_source == "timer_1"
    assert nat.controller_time == "14:35"

    # Native VSt07: manual mode, no scenario
    nat_off = decode_native_schedule_state("1", None)
    assert nat_off.active_scenario == 0
    assert nat_off.schedule_enabled is False
    assert nat_off.activation_source == "off"
    assert nat_off.controller_time is None

    # Modbus JL204c7: scenario 2 active by schedule bit (bit 6 of status_low)
    mb_scen = decode_modbus_schedule_state(
        power_reg=1, cur_mode_reg=1, status_low=(1 << 6), status_high=0, hr_scen_reg=2
    )
    assert mb_scen.active_scenario == 2
    assert mb_scen.schedule_enabled is True
    assert mb_scen.activation_source == "timer_1"

    # Modbus JL204c7: standby by timer (power_reg=2 / cur_mode_reg=2)
    mb_standby = decode_modbus_schedule_state(
        power_reg=2, cur_mode_reg=2, status_low=0, status_high=0, hr_scen_reg=0
    )
    assert mb_standby.active_scenario == SCENARIO_STANDBY
    assert mb_standby.schedule_enabled is True
    assert mb_standby.activation_source == "timer_1"


async def test_schedule_and_scenario_entities(
    hass: HomeAssistant, setup_integration, fake_client
) -> None:
    """Active scenario sensor and schedule_active binary sensor reflect panel schedule/timer state."""
    from custom_components.breezart.const import (
        ATTR_ACTIVATION_SOURCE,
        ATTR_CONTROLLER_TIME,
        ATTR_SCENARIO_NUMBER,
        ATTR_SCHEDULE_ENABLED,
        DATA_COORDINATOR,
        DOMAIN,
        KEY_ACTIVE_SCENARIO,
        KEY_CONTROLLER_TIME,
        KEY_SCENARIO_SOURCE,
        KEY_SCHEDULE_ACTIVE,
        KEY_SCHEDULE_ENABLED,
    )

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    scen_entity_id = entity_id_for(hass, "sensor", KEY_ACTIVE_SCENARIO)
    bin_entity_id = entity_id_for(hass, "binary_sensor", KEY_SCHEDULE_ACTIVE)

    assert hass.states.get(scen_entity_id).state == "off"
    assert hass.states.get(bin_entity_id).state == "off"

    # Simulate Scenario 4 activated by Timer 1 at 08:15 on the wall panel
    fake_client.state[KEY_ACTIVE_SCENARIO] = 4
    fake_client.state[KEY_SCHEDULE_ENABLED] = True
    fake_client.state[KEY_SCHEDULE_ACTIVE] = True
    fake_client.state[KEY_SCENARIO_SOURCE] = "timer_1"
    fake_client.state[KEY_CONTROLLER_TIME] = "08:15"
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    scen_state = hass.states.get(scen_entity_id)
    assert scen_state.state == "scenario_4"
    assert scen_state.attributes[ATTR_SCENARIO_NUMBER] == 4
    assert scen_state.attributes[ATTR_SCHEDULE_ENABLED] is True
    assert scen_state.attributes[ATTR_CONTROLLER_TIME] == "08:15"
    assert ATTR_ACTIVATION_SOURCE in scen_state.attributes
    assert hass.states.get(bin_entity_id).state == "on"
