# Changelog

All notable changes to [breezart-ha](https://github.com/akmagcry-oss/breezart-ha) are documented in this file.

## [1.1.0] - 2026-11-04

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
  - Added `protocol` selector (`auto`, `modbus_tcp`, `native_tcp`) and `slave_id` (default `1`) to initial setup and `OptionsFlow` in `config_flow.py`.
  - Made the `password` field optional for Modbus TCP connections (not required by `JLV135` / `JL204c7`).
  - Added Russian and English translations for protocol options and `slave_id` in `strings.json`, `translations/ru.json`, and `translations/en.json`.
- **Dual-Protocol Diagnostic Utility (`test_connection.py`)**:
  - Updated `test_connection.py` to test both Modbus TCP (`port 502`) and Native TCP (`port 1560`) with automatic fallback and detailed register decoding.

## [1.0.0] - 2026-11-02

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

