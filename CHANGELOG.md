# Changelog

All notable changes to [breezart-ha](https://github.com/akmagcry-oss/breezart-ha) are documented in this file.

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

