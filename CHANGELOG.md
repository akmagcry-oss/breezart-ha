# Changelog

All notable changes to [breezart-ha](https://github.com/akmagcry-oss/breezart-ha) are documented in this file.

## [1.4.0]

### Added
- **VAV Zoning Support (`custom_components/breezart/coordinator.py`, `custom_components/breezart/number.py`, `custom_components/breezart/binary_sensor.py`, `custom_components/breezart/config_flow.py`, `tests/`)**:
  - Added `decode_vav_properties()` and `decode_vav_zones_response()` to decode hardware VAV capability (`IsVAV` bit 15 and `MaxNVAV` bits 8..12 in `VPr07`), active VAV mode (`VSt07` `BitMode` bit 13 / Modbus `INPUT[11]` bit 9), and per-zone airflow speeds (`VZLst` on Native TCP and `HOLDING[100..119]` on Modbus TCP).
  - Added `set_vav_zone_speed(zone, speed)` on both `BreezartTCPClient` (`VWZSp_<pass>_<((speed<<8)|zone)_hex>`) and `BreezartModbusClient` (`HOLDING[100 + zone - 1] = % × 100`).
  - Added dynamic per-zone number entities `BreezartVavZoneSpeed` (`number.breezart_vav_zone_1`..`number.breezart_vav_zone_20`, range `0..speed_max`) created automatically when VAV zoning is detected or configured (`vav_zones` in `OptionsFlow`).
  - Added diagnostic binary sensor `BreezartVavBinarySensor` (`binary_sensor.breezart_vav_mode`) with `has_vav`, `vav_zones`, and `zone_speeds` attributes.

## [1.3.0]

### Added
- **Automatic Local Network Discovery During Setup (`custom_components/breezart/coordinator.py`, `custom_components/breezart/config_flow.py`, `tests/test_protocol.py`, `tests/test_config_flow.py`)**:
  - Added `async_discover_breezart_devices()`, `build_subnet_hosts()`, and `DiscoveredBreezartDevice` to scan the local `/24` IPv4 subnet concurrently (ports `502` Modbus TCP and `1560` Native TCP) while skipping already-configured entries.
  - Each open port is verified with a real Breezart protocol handshake on a single TCP connection (`get_properties()`, including recognizing `VEPas_` password-protected Native TCP units), pre-filling `host`, `port`, and `protocol` in the setup form and providing a `discovered_device` selector when one or more units are found on the LAN.
- **Home Assistant Repairs Panel Integration (`custom_components/breezart/coordinator.py`, `custom_components/breezart/__init__.py`, `tests/test_entities.py`)**:
  - Added `evaluate_repair_issues()` and `issue_registry` synchronization (`_sync_repair_issues()`, `clear_repair_issues()`) to automatically create localized **Home Assistant Repairs** issues for `overheat_hazard` (`CRITICAL`), `freeze_hazard` (`CRITICAL`), `filter_replacement` (`WARNING`, with current `{pollution}%`), and `controller_error` (`ERROR` / `WARNING`, with `{message}`), and automatically clear them as soon as the condition resolves.
- **Cumulative Energy Sensor (kWh) for Home Assistant Energy Dashboard (`custom_components/breezart/sensor.py`, `custom_components/breezart/coordinator.py`, `tests/test_entities.py`)**:
  - Added `BreezartEnergySensor` (`sensor.breezart_energy_consumption`, `SensorDeviceClass.ENERGY`, `UnitOfEnergy.KILO_WATT_HOUR`, `SensorStateClass.TOTAL_INCREASING`) with `RestoreEntity` state persistence across Home Assistant restarts and monotonic Riemann integration (`integrate_energy_kwh()`) from instantaneous power (`power_consumption`, W) for direct integration with the **Home Assistant Energy Dashboard**.
- **Wall-Panel Schedule / Scenario & Timer Reading (`custom_components/breezart/coordinator.py`, `custom_components/breezart/sensor.py`, `custom_components/breezart/binary_sensor.py`, `tests/test_entities.py`)**:
  - Added `decode_native_schedule_state()`, `decode_modbus_schedule_state()`, and `ScheduleTimerState` to decode active scenario (`1..8`), timer standby state, schedule activation source (`timer_1`, `timer_2`, `manual`, `external`, `off`), and controller clock (`HH:MM`) from Native TCP (`VSt07` `BitMode` bits `2`, `6..9`, `10..12`, and `Time` word `parts[7]`) and Modbus TCP (`HOLDING[3]`, `HOLDING[8]`, `INPUT[10]`, `INPUT[11]` bit 6, `INPUT[12]`).
  - Added enum sensor `BreezartScenarioSensor` (`sensor.breezart_active_scenario` with states `off`, `scenario_1`..`scenario_8`, `standby` and attributes `scenario_number`, `schedule_enabled`, `activation_source`, `controller_time`) and diagnostic binary sensor `binary_sensor.breezart_schedule_active`.
- **Target Humidity Control (`custom_components/breezart/climate.py`, `custom_components/breezart/number.py`, `custom_components/breezart/sensor.py`, `custom_components/breezart/coordinator.py`, `tests/`)**:
  - Added `ClimateEntityFeature.TARGET_HUMIDITY` (`target_humidity`, `current_humidity`, `min_humidity`, `max_humidity`, `async_set_humidity` with optimistic hold and rollback on failure) to `BreezartClimate`.
  - Added `BreezartTargetHumidity` (`number.breezart_target_humidity`, `NumberDeviceClass.HUMIDITY`, `%`) and diagnostic sensor `sensor.breezart_humidity_target`.
  - Implemented reading and writing of target relative humidity across both protocols: Native TCP (`VPr07` `parts[3]` min/max humidity bounds, `VSt07` `parts[4]` high byte target humidity, and `VWHum` command) and Modbus TCP (`HOLDING[2]` `h_task`, `% × 10`).
- **1-Click Device Diagnostics Download (`custom_components/breezart/diagnostics.py`, `tests/test_diagnostics.py`)**:
  - Added `async_get_config_entry_diagnostics` to export a structured JSON snapshot of the integration configuration, controller firmware/protocol version, hardware capabilities (`temp_min`, `temp_max`, `speed_min`, `speed_max`, `has_heater`, `has_cooler`, `has_humidifier`, `has_vav`, disabled optional Modbus blocks), and live coordinator state/sensor values directly from the Home Assistant Device page.
  - Sensitive configuration fields (`host`, `password`, `unique_id`) are automatically redacted via `async_redact_data`.
- **GitHub Actions CI Workflow & Repository License (`.github/workflows/validate.yml`, `LICENSE`, `tests/test_init.py`)**:
  - Added automated CI pipeline running the `pytest` test suite, official Home Assistant `hassfest` validation (`home-assistant/actions/hassfest`), and `HACS` validation (`hacs/action`) on every push and pull request.
  - Added root `LICENSE` (MIT), sorted `custom_components/breezart/manifest.json` keys, and cleaned up `hacs.json` schema for strict `hassfest` and HACS compliance.

## [1.2.4]

### Fixed
- **Options Probe on Single-Client Controllers (`config_flow.py`, `coordinator.py`)**:
  - The options-flow connection test now runs with the integration's own connection closed and polling paused (`async_release_connection()`), so controllers that accept only one TCP client no longer report `cannot_connect` when the protocol or slave ID is changed.
- **Native TCP Probe Port After Switching From Modbus (`coordinator.py`, `__init__.py`)**:
  - Switching a Modbus (502) entry to Native TCP now probes port 1560 instead of sending the text protocol to 502. Explicit-protocol probes share the auto-detection loop and `resolve_port()` (moved from `__init__.py` to `coordinator.py`), which also closes the probe socket when reading device properties fails.

### Added
- **Tests (`tests/`)**:
  - 9 new tests (55 in total) for explicit-protocol port mapping, auto-detection fallback order, probe socket cleanup, and the options probe releasing the running connection.

## [1.2.3]

### Fixed
- **Options Dialog Crash on Home Assistant 2025.12+ (`config_flow.py`)**:
  - Opening the integration options raised `AttributeError` because the options flow assigned the now read-only `config_entry` property. Settings can be changed again.
- **Verified Protocol Changes in Options (`config_flow.py`, `__init__.py`)**:
  - Changing the protocol or Modbus slave ID now probes the controller and stores the protocol and port that answered in the options (read by setup before the original port). Failures are shown in the form (`cannot_connect`, `invalid_auth`, `unknown`). `_resolve_port()` remains as a fallback for entries switched earlier.
- **Optional Modbus Registers (`coordinator.py`, `const.py`)**:
  - Fan power (10001), filter pollution (12005/12205) and system info (65000) blocks that a controller does not provide stop being polled (immediately on an "illegal function/address" reply, after 3 consecutive failures otherwise) instead of costing a timeout and reconnect on every poll. Modbus exception replies raise `ModbusExceptionError` with the exception code.
- **Command Errors (`number.py`, `switch.py`, `climate.py`, `coordinator.py`)**:
  - Failed commands from number and switch entities show a translated error (`command_failed`, en/ru) via `BreezartDataCoordinator.async_command()` instead of an unknown error; the climate entity uses the same translated error.

### Added
- **Test Suite (`tests/`, `requirements_test.txt`, `pyproject.toml`)**:
  - 46 pytest tests based on `pytest-homeassistant-custom-component` for the protocol clients (fake TCP servers), setup and reload, config and options flows, and entity commands.

## [1.2.2]

### Fixed
- **TCP Stream Desynchronization & Modbus Transaction Verification (`coordinator.py`)**:
  - Added `_drop_connection()` in both `BreezartModbusClient` and `BreezartTCPClient` so timeouts and transport errors immediately close the socket, preventing late responses from being read as the answer to the next request.
  - Unified Modbus TCP reads (`FC 0x03`, `0x04`) and writes (`FC 0x06`) through `_transact(frame, tx_id)` with strict MBAP transaction ID (`tx_id`) validation while keeping the connection intact on valid Modbus exception frames.
  - Added `_read_response()` in `BreezartTCPClient` to accumulate multi-segment TCP replies until the device goes idle (`READ_DELAY_SECONDS`), preventing truncated responses on fragmented packets.
  - Added automatic `client.disconnect()` on unparseable/corrupted poll responses in `BreezartDataCoordinator._async_update_data` so the next poll cleanly reconnects.
- **Sensor Decoding & Climate State Accuracy (`coordinator.py`, `climate.py`)**:
  - Fixed native `VSens` room (`VSENS_IDX_TEMP_ROOM`) and water (`VSENS_IDX_TEMP_WATER`) temperature decoding in `BreezartTCPClient.get_sensors()` to parse signed `× 10` values (`is_temp=True`) like supply and outdoor temperatures.
  - Stopped falling back to `temp_target` in `BreezartModbusClient.get_state()` when the current temperature sensor (`cur_t`) is unavailable, returning `None` instead.
  - Raised `HomeAssistantError` in `climate.py` when setting temperature, HVAC mode, fan speed, or power fails so Home Assistant surfaces the error in the UI and immediately rolls back optimistic state.
- **Live Options Reload & Protocol Port Resolution (`__init__.py`, `const.py`, `switch.py`)**:
  - Replaced the single-shot `DATA_SKIP_RELOAD` flag with a configuration snapshot (`DATA_RELOAD_SNAPSHOT` via `_reload_snapshot`) so toggling notification settings from either device switches or `OptionsFlow` applies live without reloading the integration.
  - Added `_resolve_port(protocol, port)` in `__init__.py` to automatically switch between default ports `502` (Modbus TCP) and `1560` (Native TCP) when the protocol is changed in `OptionsFlow`.

## [1.2.1]

### Added
- **Integration Brand Icon & Logo (`custom_components/breezart/`, `assets/breezart.png`)**:
  - Added official Breezart icon and logo (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png` in `custom_components/breezart/` and `custom_components/breezart/brand/`, plus `assets/breezart.png`) for display in Home Assistant and HACS.

### Fixed
- **Duplicate Mobile Push Notifications & Event Debounce/Throttle (`coordinator.py`, `const.py`)**:
  - Fixed duplicate push notifications on mobile devices where calling both `notify.notify` (which in Home Assistant already broadcasts to all `notify.mobile_app_*` services) and `notify.mobile_app_<phone>` caused 2 identical notifications per event. Added `_resolve_notify_targets()` so `notify.mobile_app_*` targets are called directly without also invoking the `notify.notify` broadcast group.
  - Added consecutive failure debounce (`NOTIFY_OFFLINE_FAILURE_THRESHOLD = 2`) before transitioning `_was_online` to `False` and sending `notify_offline`, preventing false offline/online notification pairs on single transient TCP/Modbus timeouts.
  - Added per-event cooldown/throttle (`NOTIFY_COOLDOWN_SECONDS = 30.0`, `NOTIFY_POWER_COOLDOWN_SECONDS = 10.0`) and `asyncio.Lock` poll serialization (`_update_lock`) across all 7 notification types (`overheat`, `freeze`, `filter`, `offline`, `online`, `power`, `other_errors`) so concurrent refreshes or sensor jitter cannot trigger duplicate notifications.
  - Updated `_async_update_data` to refresh `get_sensors()` before `get_state()` on initial/reconnect polls so supply/outdoor/water temperatures and filter pollution are populated before evaluating `danger_freeze` and `change_filter`, and stabilized `HOLDING[3]` power state detection during damper transitions.

## [1.2.0]

### Added
- **Important Event Notifications with Mobile Push Delivery (`notify.*` / `notify.mobile_app_*`)**:
  - Added automatic edge-triggered notification dispatch in `custom_components/breezart/coordinator.py` (`_async_evaluate_notifications` and `_async_send_notification`) for 7 key device events:
    1. **Overheat hazard** (`notify_overheat` — `danger_overheat` transitions to `True`)
    2. **Freeze hazard** (`notify_freeze` — `danger_freeze` transitions to `True`)
    3. **Filter replacement warning** (`notify_filter` — `change_filter` transitions to `True` or filter pollution reaches `replace_soon` / `clogged`, `≥ 60%`)
    4. **Device offline** (`notify_offline` — controller loses network/power connectivity)
    5. **Device back online** (`notify_online` — controller reconnects after being offline)
    6. **Device power on/off** (`notify_power` — ventilation unit turns on or off)
    7. **Other device errors & warnings** (`notify_other_errors` — `is_fatal_err`, `is_warn_err`, or controller text fault `msg` not covered by overheat/freeze/filter)
  - Automatic delivery to the configured Home Assistant notification service (`notify.notify` by default), all discovered Home Assistant Companion App mobile devices (`notify.mobile_app_*`), `persistent_notification.create`, and the `breezart_notification` Home Assistant event bus.
- **Individual Per-Event Notification Toggles in Device Settings (`switch.py` & `config_flow.py`)**:
  - Added 7 `EntityCategory.CONFIG` switches (`BreezartNotificationSwitch` in `custom_components/breezart/switch.py`) so each notification type can be enabled or disabled individually directly from the Home Assistant Device page (**Настройки / Configuration**) without reloading the integration (`DATA_SKIP_RELOAD`).
  - Added all 7 notification switches and `notify_service` target configuration to `OptionsFlow` in `custom_components/breezart/config_flow.py`.
  - Added full Russian and English translations for all notification switches, options, and notification messages in `const.py`, `strings.json`, `translations/ru.json`, and `translations/en.json`.

## [1.1.2]

### Added
- **Freeze Hazard Diagnostic Indicator (`binary_sensor.breezart_danger_freeze`)**:
  - Added `KEY_DANGER_FREEZE` (`danger_freeze`) binary sensor (`BinarySensorDeviceClass.COLD`, `EntityCategory.DIAGNOSTIC`) in `custom_components/breezart/binary_sensor.py` and `custom_components/breezart/const.py`.
  - Added `_detect_freeze_hazard` in `custom_components/breezart/coordinator.py` for both **Modbus TCP (`JL204c7`)** and **Native TCP (`VSt07`)**, triggering on hardware freeze alarms (`MODBUS_ALARM_BIT_FREEZE = 4` in `INPUT[19]` / `INPUT[21]` or `BIT_DANGER_FREEZE = 4` in `VSt07`) as well as low temperature conditions (supply/control/water temperature below `+5.0 °C`, or sub-zero outdoor temperature `< 0.0 °C` when the unit runs without heating).
  - Separated `MODBUS_ALARM_BIT_FREEZE` from `danger_overheat` so overheat and freeze hazards are reported independently.
  - Added Russian (`"Угроза обморожения"`) and English (`"Freeze hazard"`) translations in `const.py`, `strings.json`, `translations/ru.json`, and `translations/en.json`.

## [1.1.1]

### Added
- **Configurable Fan Speeds (`1–10`) & Heating Temperature Bounds (`5–35 °C`)**:
  - Added user-configurable `speed_max` (`1..10`, default `10`), `temp_min` (`5..44 °C`, default `5 °C`), and `temp_max` (`6..45 °C`, default `35 °C`) fields in both initial setup (`ConfigFlow`) and `OptionsFlow` ("Configure") in `custom_components/breezart/config_flow.py` and `custom_components/breezart/__init__.py`.
  - Added automatic reading of hardware temperature bounds from `INPUT[70..71]` (`Min_task` / `Max_task` on Modbus TCP `JL204c7`) and `VPr07` (on Native TCP) in `custom_components/breezart/coordinator.py` when not overridden by the user.
  - Updated Russian and English translations for `speed_max`, `temp_min`, and `temp_max` in `strings.json`, `translations/ru.json`, and `translations/en.json`.

### Changed
- **JLV135 / JL204c7 Default Alignment & Dynamic Entity Bounds**:
  - Updated default fan speeds to `10` (`1..10`) and heating temperature limits to `5–35 °C` (`DEFAULT_SPEED_MAX = 10`, `DEFAULT_TEMP_MIN = 5`, `DEFAULT_TEMP_MAX = 35`) across `MODEL_PRESETS` in `custom_components/breezart/const.py` so `HOLDING[0]` (`10%..100%`) maps `1:1` with the 10-speed **JLV135** control panel.
  - Converted `min_temp`, `max_temp`, `fan_modes` in `custom_components/breezart/climate.py` and `native_min_value`, `native_max_value` in `custom_components/breezart/number.py` to dynamic `@property` methods reading live bounds from the coordinator client.

## [1.1.0]

### Added
- **Modbus TCP Protocol Support (`port 502`)**:
  - Added `BreezartModbusClient` in `custom_components/breezart/coordinator.py` with pure `asyncio` MBAP + PDU framing (`FC 0x03`, `FC 0x04`, `FC 0x06`) and zero external dependencies.
  - Full register map support for **JLV135** Wi-Fi control panels (Espressif) and **JetLogic JL204c7 (SW v1.7.x / 1.7.14)** controllers in `custom_components/breezart/const.py`:
    - `HOLDING[0..8]`: target fan performance (`fan_task`, `% × 100`), target temperature (`t_task`, `°C × 10`), target humidity (`h_task`, `% × 10`), unit power (`on_off`), and heating/cooling mode (`mode_hc`).
    - `INPUT[10..23]`: unit work state (`Cur_mode`), 32-bit status bitmap (`Status`), 2-register `IO_DATA` control point readings (`Cur_t`, `Cur_h`, `Cur_f`), and `Errors`/`Warnings` alarm bitmaps.
    - `INPUT[50..71]`: physical `IO_DATA` sensors (supply, room, and outdoor temperature/humidity, water temperature, `CO2`, `VOC`).
    - `INPUT[10004]` (`Fan0_power` power consumption in W), `INPUT[12005]` / `INPUT[12205]` (filter 1 & 2 pollution %), and `INPUT[65000..65014]` (controller hardware ID and firmware version `1.7.14`).
- **Automatic Protocol Detection (`auto`)**:
  - Added `async_detect_and_connect_client` to automatically probe and fall back between **Modbus TCP (`port 502`)** and **Native TCP (`port 1560`)** during integration setup and startup.
- **Configuration Flow & Localization Enhancements**:
  - Added `protocol` selector (`auto`, `modbus_tcp`, `native_tcp`) and `slave_id` setting (default `1`) in both initial setup and `OptionsFlow` in `config_flow.py`.
  - Made the `password` field optional for Modbus TCP connections (not required by `JLV135` / `JL204c7`).
  - Added Russian and English translations for all new protocol and Modbus fields in `strings.json`, `translations/ru.json`, and `translations/en.json`.
- **Dual-Protocol Diagnostic Utility (`test_connection.py`)**:
  - Updated `test_connection.py` to test both Modbus TCP (`port 502`) and Native TCP (`port 1560`) with automatic fallback and detailed register decoding.

## [1.0.0]

### Added
- **Initial Release (`v1.0.0`)**: Full-featured Home Assistant integration for Breezart ventilation systems over the native TCP protocol (`port 1560`).
- **Centralized Constants (`custom_components/breezart/const.py`)**: All protocol commands (`VPr07`, `VSt07`, `VSens`, `VWPwr`, `VWTmp`, `VWSpd`, `VWFtr`), packet indices, bitmask offsets, sentinel values, polling intervals, coordinator dictionary keys, filter pollution thresholds, and translation keys defined in a single module.
- **Model Configuration Presets (`MODEL_PRESETS`)**: Built-in presets in `const.py` and `config_flow.py` (with `OptionsFlow` support) for:
  - `Breezart 400 Lux` (Electric heater, 10–30°C, speeds 1–8)
  - `Breezart 550 Lux` (Electric heater, 10–30°C, speeds 1–8)
  - `Breezart 550 Aqua` (Water heater + humidifier, 15–30°C, speeds 1–8)
  - `Breezart 700 Lux` (Electric heater + cooler, 10–30°C, speeds 1–8)
  - `Breezart 1000 Lux` (Electric heater + cooler, 10–30°C, speeds 1–10)
  - `Breezart 1000 Aqua` (Water heater + cooler + humidifier, 15–30°C, speeds 1–10)
  - `Breezart 2000 Lux` (Commercial electric + cooler + humidifier + CO₂, 10–30°C, speeds 1–10)
  - `Custom / Auto-detect` (`VPr07` hardware auto-detection)
- **Full Russian & English Internationalization (RU / EN)**:
  - Complete entity localization via `_attr_translation_key` across `climate.py`, `sensor.py`, `binary_sensor.py`, `number.py`, and `switch.py`.
  - Enum state sensors (`unit_state`, `mode`, `mode_set`, `color_ind`, `color_msg`) and localized filter pollution statuses (`no_data`, `excellent`, `good`, `replace_soon`, `clogged`) in `strings.json`, `translations/ru.json`, and `translations/en.json`.

