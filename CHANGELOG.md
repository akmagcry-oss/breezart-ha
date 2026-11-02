# Changelog

All notable changes to [breezart-ha](https://github.com/akmagcry-oss/breezart-ha) are documented in this file.

## [1.0.0] - 2026-11-02

### Added
- **Initial Release (`v1.0.0`)**: Native TCP protocol (port 1560) Home Assistant integration for Breezart ventilation systems (`VPr07`, `VSt07`, `VSens`, `VWPwr`, `VWTmp`, `VWSpd`, `VWFtr`).
- **Centralized Constants (`custom_components/breezart/const.py`)**: All protocol commands, packet indices, bitmask offsets, sentinel values, polling intervals, coordinator dictionary keys, filter pollution thresholds, and translation keys defined in a single module.
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
