import constPy from '../../custom_components/breezart/const.py?raw';
import initPy from '../../custom_components/breezart/__init__.py?raw';
import configFlowPy from '../../custom_components/breezart/config_flow.py?raw';
import coordinatorPy from '../../custom_components/breezart/coordinator.py?raw';
import climatePy from '../../custom_components/breezart/climate.py?raw';
import sensorPy from '../../custom_components/breezart/sensor.py?raw';
import binarySensorPy from '../../custom_components/breezart/binary_sensor.py?raw';
import numberPy from '../../custom_components/breezart/number.py?raw';
import switchPy from '../../custom_components/breezart/switch.py?raw';
import stringsJson from '../../custom_components/breezart/strings.json?raw';
import ruJson from '../../custom_components/breezart/translations/ru.json?raw';
import enJson from '../../custom_components/breezart/translations/en.json?raw';
import manifestJson from '../../custom_components/breezart/manifest.json?raw';
import testConnectionPy from '../../test_connection.py?raw';

export interface RepoFileEntry {
  path: string;
  filename: string;
  language: 'python' | 'json';
  content: string;
  summary: {
    ru: string;
    en: string;
  };
  highlights: {
    ru: string[];
    en: string[];
  };
}

export const REPO_FILES: readonly RepoFileEntry[] = [
  {
    path: 'custom_components/breezart/const.py',
    filename: 'const.py',
    language: 'python',
    content: constPy,
    summary: {
      ru: 'Единый файл всех констант протоколов (Modbus TCP 502 и Native TCP 1560), карты регистров JL204c7, пресетов моделей (400 Lux — 2000 Lux) и таблиц перевода RU/EN.',
      en: 'Centralized constants for both Modbus TCP (502) and Native TCP (1560), JL204c7 register map, model presets (400 Lux — 2000 Lux), and RU/EN translation tables.',
    },
    highlights: {
      ru: [
        'Карта регистров Modbus TCP для JLV135 / JL204c7 (ПО 1.7.x): HOLDING[0..8], INPUT[10..23], INPUT[50..71], INPUT[10004], INPUT[12005]',
        'Вынесены все TCP-команды, индексы пакетов VPr07/VSt07/VSens и битовые смещения',
        'Добавлены преднастройки MODEL_PRESETS для 400 Lux, 550 Lux, 550 Aqua, 700 Lux, 1000 Lux, 1000 Aqua, 2000 Lux и Custom',
      ],
      en: [
        'Modbus TCP register map for JLV135 / JL204c7 (SW 1.7.x): HOLDING[0..8], INPUT[10..23], INPUT[50..71], INPUT[10004], INPUT[12005]',
        'Extracted all TCP commands, VPr07/VSt07/VSens packet indices, and bitmask offsets',
        'Added MODEL_PRESETS for 400 Lux, 550 Lux, 550 Aqua, 700 Lux, 1000 Lux, 1000 Aqua, 2000 Lux, and Custom',
      ],
    },
  },
  {
    path: 'custom_components/breezart/config_flow.py',
    filename: 'config_flow.py',
    language: 'python',
    content: configFlowPy,
    summary: {
      ru: 'Мастер настройки с выбором пресета модели, протокола (Auto / Modbus TCP 502 / Native TCP 1560) и автоопределением порта.',
      en: 'Setup wizard with model preset selector, protocol selector (Auto / Modbus TCP 502 / Native TCP 1560), and automatic port detection.',
    },
    highlights: {
      ru: [
        'Автоматическое определение протокола: при отказе порта 1560 автоматически проверяет Modbus TCP на порту 502 (пульт JLV135)',
        'Добавлен выбор модели (400_lux..2000_lux) и протокола (auto, modbus_tcp, native_tcp) в мастере и OptionsFlow',
        'Пароль сделан необязательным при работе по Modbus TCP (порт 502)',
      ],
      en: [
        'Automatic protocol detection: falls back to Modbus TCP on port 502 (JLV135 panel) if port 1560 is closed',
        'Added model preset (400_lux..2000_lux) and protocol (auto, modbus_tcp, native_tcp) selectors in initial setup and OptionsFlow',
        'Password is optional when connecting over Modbus TCP (port 502)',
      ],
    },
  },
  {
    path: 'custom_components/breezart/coordinator.py',
    filename: 'coordinator.py',
    language: 'python',
    content: coordinatorPy,
    summary: {
      ru: 'Два клиента (BreezartModbusClient на порту 502 для JLV135/JL204c7 и BreezartTCPClient на порту 1560 для TPD-283U-H) + координатор данных.',
      en: 'Dual clients (BreezartModbusClient on port 502 for JLV135/JL204c7 and BreezartTCPClient on port 1560 for TPD-283U-H) + data coordinator.',
    },
    highlights: {
      ru: [
        'BreezartModbusClient реализует кадры MBAP + PDU (FC 0x03, 0x04, 0x06) на чистом asyncio без внешних зависимостей',
        'Разбор структур IO_DATA (значение + статус достоверности датчика) и битовой маски Status/Alarms контроллера JL204c7 (ПО 1.7.14)',
        'Сериализация запросов через asyncio.Lock и безопасная пауза 60 мс для RS-485 моста панели JLV135',
      ],
      en: [
        'BreezartModbusClient implements MBAP + PDU framing (FC 0x03, 0x04, 0x06) in pure asyncio with zero external dependencies',
        'Parses JL204c7 (SW 1.7.14) IO_DATA sensor pairs (value + reliability status) and Status/Alarms bitmasks',
        'Serializes socket operations via asyncio.Lock with a 60ms bridge delay for the JLV135 RS-485 gateway',
      ],
    },
  },
  {
    path: 'custom_components/breezart/climate.py',
    filename: 'climate.py',
    language: 'python',
    content: climatePy,
    summary: {
      ru: 'Термостат ClimateEntity с _attr_translation_key, динамическим списком скоростей/режимов по модели и числовыми константами режимов.',
      en: 'ClimateEntity thermostat with _attr_translation_key, model-driven fan/HVAC modes, and numeric mode constants.',
    },
    highlights: {
      ru: [
        'Удалена привязка к русским подстрокам ("обогрев" in mode_name) — используются MODE_HEAT, MODE_COOL, CMD_MODE_*',
        'Диапазон скоростей вентилятора (1..8 или 1..10) и режим охлаждения формируются по пресету модели',
        'Использует _attr_translation_key = "climate" вместо захардкоженного _attr_name = "Климат"',
      ],
      en: [
        'Replaced fragile Russian substring checks with numeric constants MODE_HEAT, MODE_COOL, CMD_MODE_*',
        'Fan speed list (1..8 or 1..10) and cooling mode availability adapt to model preset',
        'Uses _attr_translation_key = "climate" instead of hardcoded Russian _attr_name',
      ],
    },
  },
  {
    path: 'custom_components/breezart/sensor.py',
    filename: 'sensor.py',
    language: 'python',
    content: sensorPy,
    summary: {
      ru: '28 сенсоров с полной интернационализацией (_attr_translation_key, SensorDeviceClass.ENUM) и авто-активацией по модели.',
      en: '28 sensors with full i18n (_attr_translation_key, SensorDeviceClass.ENUM) and model-aware default activation.',
    },
    highlights: {
      ru: [
        'Текстовые сенсоры переведены на SensorDeviceClass.ENUM с каноническими ключами состояний для RU и EN',
        'Статусы загрязнения фильтров 1–4 локализуются на русский и английский языки',
        'Набор включённых по умолчанию сенсоров определяется выбранной моделью (водяной / электрический калорифер)',
      ],
      en: [
        'Text sensors converted to SensorDeviceClass.ENUM with canonical state keys for RU and EN',
        'Filter 1–4 pollution statuses localized dynamically in Russian and English',
        'Default enabled sensors automatically tailored to selected model preset (water vs electric heater)',
      ],
    },
  },
  {
    path: 'custom_components/breezart/binary_sensor.py',
    filename: 'binary_sensor.py',
    language: 'python',
    content: binarySensorPy,
    summary: {
      ru: '6 бинарных сенсоров состояния и аварий (включая угрозу перегрева и угрозу обморожения) с поддержкой _attr_translation_key.',
      en: '6 status and diagnostic binary sensors (including overheat and freeze hazards) using _attr_translation_key.',
    },
    highlights: {
      ru: [
        'Использует _attr_translation_key для перевода на русский и английский',
        'Единый DeviceInfo из координатора с отображением выбранной модели Breezart',
      ],
      en: [
        'Uses _attr_translation_key for seamless Russian and English localization',
        'Shared DeviceInfo from coordinator displaying the configured Breezart model',
      ],
    },
  },
  {
    path: 'custom_components/breezart/number.py',
    filename: 'number.py',
    language: 'python',
    content: numberPy,
    summary: {
      ru: 'Регуляторы целевой температуры и скорости вентилятора с пределами из пресета модели и _attr_translation_key.',
      en: 'Target temperature and fan speed number entities using model preset bounds and _attr_translation_key.',
    },
    highlights: {
      ru: [
        'Заменены захардкоженные русские названия на _attr_translation_key',
        'Шаги и границы регулирования берутся из констант и пресета модели',
      ],
      en: [
        'Replaced hardcoded Russian names with _attr_translation_key',
        'Step values and min/max bounds sourced from constants and model preset',
      ],
    },
  },
  {
    path: 'custom_components/breezart/switch.py',
    filename: 'switch.py',
    language: 'python',
    content: switchPy,
    summary: {
      ru: 'Выключатель питания установки + 7 индивидуальных переключателей уведомлений (EntityCategory.CONFIG) в настройках устройства.',
      en: 'Unit power switch + 7 individual notification switches (EntityCategory.CONFIG) in device settings.',
    },
    highlights: {
      ru: [
        'Использует TRANSLATION_KEY_POWER_SWITCH и 7 ключей NOTIFICATION_SETTING_KEYS из const.py',
        'Позволяет по отдельности включать и отключать каждое из 7 уведомлений на странице устройства HA',
      ],
      en: [
        'Uses TRANSLATION_KEY_POWER_SWITCH and 7 NOTIFICATION_SETTING_KEYS from const.py',
        'Allows enabling/disabling each of the 7 notifications individually on the HA device page',
      ],
    },
  },
  {
    path: 'custom_components/breezart/__init__.py',
    filename: '__init__.py',
    language: 'python',
    content: initPy,
    summary: {
      ru: 'Инициализация интеграции, передача выбранного пресета модели и настроек уведомлений без лишней перезагрузки при переключении тумблеров.',
      en: 'Integration setup passing selected model preset and notification settings without unnecessary reloads when toggling switches.',
    },
    highlights: {
      ru: [
        'Поддержка entry.options[CONF_MODEL], 7 флагов уведомлений и слушатель обновления настроек async_reload_entry',
        'Все ключи hass.data вынесены в const.py (DATA_CLIENT, DATA_COORDINATOR, DATA_MODEL, DATA_SKIP_RELOAD)',
      ],
      en: [
        'Supports entry.options[CONF_MODEL], 7 notification flags, and update listener async_reload_entry',
        'All hass.data keys centralized in const.py (DATA_CLIENT, DATA_COORDINATOR, DATA_MODEL, DATA_SKIP_RELOAD)',
      ],
    },
  },
  {
    path: 'custom_components/breezart/translations/ru.json',
    filename: 'translations/ru.json',
    language: 'json',
    content: ruJson,
    summary: {
      ru: 'Полный русский языковой пакет для мастера настройки, опций, пресетов моделей и всех 44 сущностей.',
      en: 'Complete Russian language pack for config flow, options, model presets, and all 44 entities.',
    },
    highlights: {
      ru: [
        'Переводы всех 28 сенсоров, 6 бинарных сенсоров, 2 регуляторов, 8 переключателей и термостата',
        'Переводы всех состояний ENUM-сенсоров и статусов фильтров 1–4',
      ],
      en: [
        'Translations for all 28 sensors, 6 binary sensors, 2 numbers, 8 switches, and climate entity',
        'Translations for all ENUM sensor states and filter 1–4 status attributes',
      ],
    },
  },
  {
    path: 'custom_components/breezart/translations/en.json',
    filename: 'translations/en.json',
    language: 'json',
    content: enJson,
    summary: {
      ru: 'Полный английский языковой пакет, идентичный по структуре ru.json и strings.json.',
      en: 'Complete English language pack structurally identical to ru.json and strings.json.',
    },
    highlights: {
      ru: [
        '100% покрытие всех ключей сущностей, состояний, ошибок и селектора моделей на английском языке',
      ],
      en: [
        '100% coverage of all entity names, enum states, errors, and model selector options in English',
      ],
    },
  },
  {
    path: 'custom_components/breezart/strings.json',
    filename: 'strings.json',
    language: 'json',
    content: stringsJson,
    summary: {
      ru: 'Базовый шаблон строк Home Assistant с полным описанием сущностей и селекторов.',
      en: 'Base Home Assistant strings template with complete entity and selector definitions.',
    },
    highlights: {
      ru: ['Синхронизирован с translations/en.json и translations/ru.json'],
      en: ['Synchronized with translations/en.json and translations/ru.json'],
    },
  },
  {
    path: 'test_connection.py',
    filename: 'test_connection.py',
    language: 'python',
    content: testConnectionPy,
    summary: {
      ru: 'Утилита диагностики TCP-подключения, использующая константы из const.py и двуязычный вывод RU/EN.',
      en: 'TCP connection diagnostic utility using constants from const.py and bilingual RU/EN output.',
    },
    highlights: {
      ru: ['Импортирует DEFAULT_HOST, DEFAULT_PORT, DEFAULT_PASSWORD, REQ_GET_PROPERTIES из const.py'],
      en: ['Imports DEFAULT_HOST, DEFAULT_PORT, DEFAULT_PASSWORD, REQ_GET_PROPERTIES from const.py'],
    },
  },
  {
    path: 'custom_components/breezart/manifest.json',
    filename: 'manifest.json',
    language: 'json',
    content: manifestJson,
    summary: {
      ru: 'Манифест интеграции Home Assistant / HACS (версия 1.2.2, репозиторий akmagcry-oss/breezart-ha).',
      en: 'Home Assistant / HACS integration manifest (v1.2.2, repository akmagcry-oss/breezart-ha).',
    },
    highlights: {
      ru: [
        'Версия 1.2.2 с поддержкой push-уведомлений о важных событиях, Modbus TCP (порт 502) и Native TCP (порт 1560)',
        'Ссылки на https://github.com/akmagcry-oss/breezart-ha и @akmagcry-oss',
      ],
      en: [
        'Release v1.2.2 with important event push notifications, Modbus TCP (port 502), and Native TCP (port 1560) support',
        'Repository links set to https://github.com/akmagcry-oss/breezart-ha and @akmagcry-oss',
      ],
    },
  },
];
