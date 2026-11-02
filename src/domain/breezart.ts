/**
 * Pure domain model, constants, model presets, protocol parser/encoder,
 * and full Russian/English i18n dictionary mirroring custom_components/breezart/.
 */

export type Language = 'ru' | 'en';

export type ModelPresetId =
  | '400_lux'
  | '550_lux'
  | '550_aqua'
  | '700_lux'
  | '1000_lux'
  | '1000_aqua'
  | '2000_lux'
  | 'custom';

export type HeaterType = 'electric' | 'water' | 'auto';

export type HvacModeKey = 'off' | 'fan_only' | 'heat' | 'cool' | 'auto';
export type HvacActionKey = 'off' | 'heating' | 'cooling' | 'fan' | 'idle';

export type FilterStatusKey =
  | 'no_data'
  | 'excellent'
  | 'good'
  | 'replace_soon'
  | 'clogged';

export interface ModelPreset {
  id: ModelPresetId;
  name: string;
  airflowM3h: number;
  heaterType: HeaterType;
  tempMin: number;
  tempMax: number;
  speedMin: number;
  speedMax: number;
  hasCooler: boolean;
  hasHumidifier: boolean;
  hasWaterHeater: boolean;
  enabledSensors: readonly string[];
}

export interface ProtocolConstantEntry {
  name: string;
  value: string | number;
  category: 'network' | 'protocol' | 'bitmask' | 'keys' | 'thresholds' | 'modes';
  usedIn: string[];
  description: { ru: string; en: string };
}

export const BREEZART_CONSTANTS = {
  DOMAIN: 'breezart',
  DEFAULT_NAME: 'Breezart',
  MANUFACTURER: 'Breezart',
  CONFIG_FLOW_VERSION: 1,
  CONF_MODEL: 'model',
  DEFAULT_HOST: '192.168.1.121',
  DEFAULT_PORT: 1560,
  DEFAULT_PASSWORD: '21579',
  DEFAULT_TIMEOUT: 5,
  STATE_UPDATE_INTERVAL: 3,
  SENSORS_UPDATE_INTERVAL: 30,
  OPTIMISTIC_HOLD_SECONDS: 6,
  READ_DELAY_SECONDS: 0.03,
  READ_BUFFER_SIZE: 4096,
  DELIMITER: '_',
  MAX_UINT16: 0xffff,
  SIGN_BIT_MASK: 0x8000,
  SIGN_BIT_OFFSET: 0x10000,
  NO_DATA_VALUE: 0xfb07,
  NO_DATA_HEX: 'fb07',
  NO_DATA_BYTE: 255,
  TEMP_DIVISOR: 10.0,
  REQ_GET_PROPERTIES: 'VPr07',
  REQ_GET_STATE: 'VSt07',
  REQ_GET_SENSORS: 'VSens',
  REQ_SET_POWER: 'VWPwr',
  REQ_SET_TEMP: 'VWTmp',
  REQ_SET_FAN_SPEED: 'VWSpd',
  REQ_SET_MODE: 'VWFtr',
  RESP_OK: 'OK',
  POWER_ON: 1,
  POWER_OFF: 0,
  UNIT_STATE_OFF: 0,
  UNIT_STATE_ON: 1,
  UNIT_STATE_SHUTDOWN: 2,
  UNIT_STATE_STARTUP: 3,
  MODE_HEAT: 0,
  MODE_COOL: 1,
  MODE_AUTO_HEAT: 2,
  MODE_AUTO_COOL: 3,
  MODE_VENT: 4,
  MODE_OFF: 5,
  CMD_MODE_HEAT: 1,
  CMD_MODE_COOL: 2,
  CMD_MODE_AUTO: 3,
  CMD_MODE_VENT: 4,
  FILTER_POLLUTION_EXCELLENT_MAX: 30,
  FILTER_POLLUTION_GOOD_MAX: 60,
  FILTER_POLLUTION_REPLACE_MAX: 85,
} as const;

export const EXTRACTED_CONSTANTS_CATALOG: readonly ProtocolConstantEntry[] = [
  {
    name: 'DOMAIN / MANUFACTURER / CONFIG_FLOW_VERSION',
    value: '"breezart" / "Breezart" / 1',
    category: 'keys',
    usedIn: ['__init__.py', 'config_flow.py', 'coordinator.py', 'climate.py', 'sensor.py'],
    description: {
      ru: 'Идентификатор домена, производителя и версия схемы конфигурации HA',
      en: 'Integration domain identifier, manufacturer name, and HA config schema version',
    },
  },
  {
    name: 'DEFAULT_HOST / DEFAULT_PORT / DEFAULT_PASSWORD',
    value: '"192.168.1.121" : 1560 (pwd: "21579")',
    category: 'network',
    usedIn: ['config_flow.py', 'test_connection.py'],
    description: {
      ru: 'Параметры TCP-подключения по умолчанию (ранее были захардкожены в config_flow.py)',
      en: 'Default TCP connection parameters (previously hardcoded inside config_flow.py)',
    },
  },
  {
    name: 'STATE_UPDATE_INTERVAL / SENSORS_UPDATE_INTERVAL / OPTIMISTIC_HOLD_SECONDS',
    value: '3s / 30s / 6s',
    category: 'network',
    usedIn: ['coordinator.py', 'climate.py'],
    description: {
      ru: 'Интервалы опроса состояния (VSt07), сенсоров (VSens) и удержания optimistic-состояния UI',
      en: 'Polling intervals for state (VSt07), sensors (VSens), and UI optimistic hold duration',
    },
  },
  {
    name: 'READ_DELAY_SECONDS / READ_BUFFER_SIZE / DEFAULT_TIMEOUT',
    value: '0.03s / 4096 B / 5s',
    category: 'network',
    usedIn: ['coordinator.py', 'test_connection.py'],
    description: {
      ru: 'Тайминги чтения сокета и размер буфера пакета контроллера JL205 / TPD-283U-H',
      en: 'Socket read timing and packet buffer size for JL205 / TPD-283U-H controller',
    },
  },
  {
    name: 'REQ_GET_PROPERTIES / REQ_GET_STATE / REQ_GET_SENSORS',
    value: '"VPr07" / "VSt07" / "VSens"',
    category: 'protocol',
    usedIn: ['coordinator.py', 'test_connection.py'],
    description: {
      ru: 'Команды чтения свойств, состояния и датчиков нативного TCP-протокола Breezart',
      en: 'Read commands for device properties, state, and sensors in native Breezart TCP protocol',
    },
  },
  {
    name: 'REQ_SET_POWER / REQ_SET_TEMP / REQ_SET_FAN_SPEED / REQ_SET_MODE',
    value: '"VWPwr" / "VWTmp" / "VWSpd" / "VWFtr"',
    category: 'protocol',
    usedIn: ['coordinator.py', 'climate.py', 'number.py', 'switch.py'],
    description: {
      ru: 'Команды записи питания, целевой температуры, скорости вентилятора и режима работы',
      en: 'Write commands for power state, target temperature, fan speed, and operating mode',
    },
  },
  {
    name: 'VPR07_IDX_* / VST07_IDX_* / VSENS_IDX_*',
    value: 'Indices 1..14 & Bit Offsets 0..15',
    category: 'bitmask',
    usedIn: ['coordinator.py'],
    description: {
      ru: 'Индексы полей пакетов VPr07, VSt07, VSens и битовые смещения флагов состояния',
      en: 'Packet word indices for VPr07, VSt07, VSens and bitmask offsets for state flags',
    },
  },
  {
    name: 'NO_DATA_VALUE / NO_DATA_HEX / NO_DATA_BYTE / MAX_UINT16',
    value: '0xFB07 ("fb07") / 255 / 0xFFFF',
    category: 'bitmask',
    usedIn: ['coordinator.py'],
    description: {
      ru: 'Маркеры отсутствия датчика (0xFB07 и 0xFF) и маски знакового 16-битного числа',
      en: 'Missing sensor sentinel values (0xFB07 and 0xFF) and signed 16-bit integer masks',
    },
  },
  {
    name: 'MODE_HEAT..MODE_OFF / CMD_MODE_HEAT..CMD_MODE_VENT',
    value: '0..5 (state) / 1..4 (command)',
    category: 'modes',
    usedIn: ['climate.py', 'sensor.py'],
    description: {
      ru: 'Числовые коды режимов работы вместо проверки русских подстрок ("обогрев" in mode_name)',
      en: 'Numeric mode constants replacing fragile Russian substring checks in climate.py',
    },
  },
  {
    name: 'FILTER_POLLUTION_EXCELLENT_MAX / GOOD_MAX / REPLACE_MAX',
    value: '30% / 60% / 85%',
    category: 'thresholds',
    usedIn: ['const.py', 'sensor.py'],
    description: {
      ru: 'Пороги классификации загрязнённости фильтров 1–4 (Отличное / Хорошее / Замена / Забит)',
      en: 'Filter 1–4 pollution classification thresholds (Excellent / Good / Replace soon / Clogged)',
    },
  },
  {
    name: 'KEY_POWER..KEY_FILTER4_POLLUTION (34 Coordinator Keys)',
    value: '"power", "temp_supply", "co2", ...',
    category: 'keys',
    usedIn: ['coordinator.py', 'climate.py', 'sensor.py', 'binary_sensor.py', 'number.py', 'switch.py'],
    description: {
      ru: 'Единые константы ключей словаря данных координатора и translation_key всех объектов',
      en: 'Unified dictionary keys for coordinator state and entity translation_key identifiers',
    },
  },
];

export const BASE_ENABLED_SENSORS = [
  'temperature',
  'temp_supply',
  'temperature_target',
  'speed',
  'speed_target',
  'filter_dust',
  'unit_state',
  'mode',
  'mode_set',
  'color_ind',
  'color_msg',
  'msg',
  'firmware_ver',
  'protocol_ver',
] as const;

export const MODEL_PRESETS: Record<ModelPresetId, ModelPreset> = {
  '400_lux': {
    id: '400_lux',
    name: '400 Lux',
    airflowM3h: 400,
    heaterType: 'electric',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 8,
    hasCooler: false,
    hasHumidifier: false,
    hasWaterHeater: false,
    enabledSensors: [...BASE_ENABLED_SENSORS, 'power_consumption', 'temp_outdoor'],
  },
  '550_lux': {
    id: '550_lux',
    name: '550 Lux',
    airflowM3h: 550,
    heaterType: 'electric',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 8,
    hasCooler: false,
    hasHumidifier: false,
    hasWaterHeater: false,
    enabledSensors: [...BASE_ENABLED_SENSORS, 'power_consumption', 'temp_outdoor'],
  },
  '550_aqua': {
    id: '550_aqua',
    name: '550 Aqua',
    airflowM3h: 550,
    heaterType: 'water',
    tempMin: 15,
    tempMax: 30,
    speedMin: 1,
    speedMax: 8,
    hasCooler: false,
    hasHumidifier: true,
    hasWaterHeater: true,
    enabledSensors: [...BASE_ENABLED_SENSORS, 'humidity', 'temp_water', 'temp_outdoor'],
  },
  '700_lux': {
    id: '700_lux',
    name: '700 Lux',
    airflowM3h: 700,
    heaterType: 'electric',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 8,
    hasCooler: true,
    hasHumidifier: false,
    hasWaterHeater: false,
    enabledSensors: [...BASE_ENABLED_SENSORS, 'power_consumption', 'temp_outdoor', 'temp_room'],
  },
  '1000_lux': {
    id: '1000_lux',
    name: '1000 Lux',
    airflowM3h: 1000,
    heaterType: 'electric',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 10,
    hasCooler: true,
    hasHumidifier: false,
    hasWaterHeater: false,
    enabledSensors: [
      ...BASE_ENABLED_SENSORS,
      'power_consumption',
      'temp_outdoor',
      'temp_room',
      'speed_fact',
    ],
  },
  '1000_aqua': {
    id: '1000_aqua',
    name: '1000 Aqua',
    airflowM3h: 1000,
    heaterType: 'water',
    tempMin: 15,
    tempMax: 30,
    speedMin: 1,
    speedMax: 10,
    hasCooler: true,
    hasHumidifier: true,
    hasWaterHeater: true,
    enabledSensors: [
      ...BASE_ENABLED_SENSORS,
      'humidity',
      'temp_water',
      'temp_outdoor',
      'temp_room',
      'speed_fact',
    ],
  },
  '2000_lux': {
    id: '2000_lux',
    name: '2000 Lux',
    airflowM3h: 2000,
    heaterType: 'electric',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 10,
    hasCooler: true,
    hasHumidifier: true,
    hasWaterHeater: false,
    enabledSensors: [
      ...BASE_ENABLED_SENSORS,
      'humidity',
      'power_consumption',
      'temp_outdoor',
      'temp_room',
      'speed_fact',
      'co2',
    ],
  },
  custom: {
    id: 'custom',
    name: 'Custom (Auto)',
    airflowM3h: 0,
    heaterType: 'auto',
    tempMin: 10,
    tempMax: 30,
    speedMin: 1,
    speedMax: 10,
    hasCooler: true,
    hasHumidifier: true,
    hasWaterHeater: true,
    enabledSensors: [...BASE_ENABLED_SENSORS, 'humidity'],
  },
};

export function getModelPreset(modelId?: string | null): ModelPreset {
  if (!modelId || !(modelId in MODEL_PRESETS)) {
    return MODEL_PRESETS['550_lux'];
  }
  return MODEL_PRESETS[modelId as ModelPresetId];
}

export function decToHex(value: number): string {
  if (!Number.isInteger(value) || value < 0 || value > BREEZART_CONSTANTS.MAX_UINT16) {
    throw new Error(`Value must be a positive integer <= ${BREEZART_CONSTANTS.MAX_UINT16}, got ${value}`);
  }
  return value.toString(16);
}

export function hexToDec(hexStr: string): number {
  return parseInt(hexStr, 16);
}

export function hexToDecSign(hexStr: string): number {
  let val = parseInt(hexStr, 16);
  if (val & BREEZART_CONSTANTS.SIGN_BIT_MASK) {
    val -= BREEZART_CONSTANTS.SIGN_BIT_OFFSET;
  }
  return val;
}

export function parseBits(hexStr: string, fromBit: number, toBit?: number): number {
  const endBit = toBit ?? fromBit;
  if (hexStr === '0') {
    return 0;
  }
  const num = parseInt(hexStr, 16);
  const bits = num.toString(2).padStart(16, '0').split('').reverse().join('');
  const extracted = bits
    .slice(fromBit, endBit + 1)
    .split('')
    .reverse()
    .join('');
  return parseInt(extracted || '0', 2);
}

export function buildProtocolRequest(
  requestType: string,
  password: number,
  data?: number
): string {
  const parts = [requestType, decToHex(password)];
  if (data !== undefined) {
    parts.push(decToHex(data));
  }
  return parts.join(BREEZART_CONSTANTS.DELIMITER);
}

export function classifyFilterPollution(pollution: number | null | undefined): FilterStatusKey {
  if (pollution === null || pollution === undefined || Number.isNaN(pollution)) {
    return 'no_data';
  }
  if (pollution < BREEZART_CONSTANTS.FILTER_POLLUTION_EXCELLENT_MAX) {
    return 'excellent';
  }
  if (pollution < BREEZART_CONSTANTS.FILTER_POLLUTION_GOOD_MAX) {
    return 'good';
  }
  if (pollution < BREEZART_CONSTANTS.FILTER_POLLUTION_REPLACE_MAX) {
    return 'replace_soon';
  }
  return 'clogged';
}

export function resolveHvacMode(power: boolean, modeCode: number): HvacModeKey {
  if (!power) return 'off';
  if (modeCode === BREEZART_CONSTANTS.MODE_HEAT) return 'heat';
  if (modeCode === BREEZART_CONSTANTS.MODE_COOL) return 'cool';
  if (
    modeCode === BREEZART_CONSTANTS.MODE_AUTO_HEAT ||
    modeCode === BREEZART_CONSTANTS.MODE_AUTO_COOL
  ) {
    return 'auto';
  }
  return 'fan_only';
}

export function resolveHvacAction(
  power: boolean,
  unitState: number,
  modeCode: number
): HvacActionKey {
  if (!power || unitState === BREEZART_CONSTANTS.UNIT_STATE_OFF) {
    return 'off';
  }
  if (unitState === BREEZART_CONSTANTS.UNIT_STATE_ON) {
    if (
      modeCode === BREEZART_CONSTANTS.MODE_HEAT ||
      modeCode === BREEZART_CONSTANTS.MODE_AUTO_HEAT
    ) {
      return 'heating';
    }
    if (
      modeCode === BREEZART_CONSTANTS.MODE_COOL ||
      modeCode === BREEZART_CONSTANTS.MODE_AUTO_COOL
    ) {
      return 'cooling';
    }
    return 'fan';
  }
  return 'idle';
}

export interface TranslationCatalog {
  entities: Record<string, string>;
  unit_state: Record<string, string>;
  mode: Record<string, string>;
  color_msg: Record<string, string>;
  color_ind: Record<string, string>;
  filter_status: Record<FilterStatusKey, string>;
  models: Record<ModelPresetId, string>;
  config: {
    title: string;
    description: string;
    modelLabel: string;
    hostLabel: string;
    portLabel: string;
    passwordLabel: string;
    submitButton: string;
    errors: {
      cannot_connect: string;
      invalid_auth: string;
      unknown: string;
    };
  };
}

export const I18N_CATALOG: Record<Language, TranslationCatalog> = {
  ru: {
    entities: {
      climate: 'Климат',
      power: 'Питание',
      target_temperature: 'Заданная температура',
      fan_speed: 'Скорость вентилятора',
      temperature: 'Температура (точка регулирования)',
      temp_supply: 'Температура подачи (выход установки)',
      temp_room: 'Температура в помещении',
      temp_outdoor: 'Температура на улице',
      temp_water: 'Температура теплоносителя',
      temperature_target: 'Заданная температура',
      speed: 'Скорость вентилятора',
      speed_target: 'Заданная скорость',
      speed_fact: 'Фактическая скорость',
      power_consumption: 'Потребляемая мощность',
      filter_dust: 'Загрязнённость фильтра',
      humidity: 'Влажность',
      unit_state: 'Состояние установки',
      mode: 'Режим работы',
      mode_set: 'Заданный режим',
      color_ind: 'Индикатор питания',
      color_msg: 'Статус сообщения',
      msg: 'Сообщение устройства',
      firmware_ver: 'Версия прошивки',
      protocol_ver: 'Версия протокола',
      humidity_supply: 'Влажность на притоке',
      humidity_room: 'Влажность в помещении',
      humidity_outdoor: 'Влажность уличного воздуха',
      co2: 'CO₂',
      voc: 'VOC (загрязнённость воздуха)',
      filter1_pollution: 'Фильтр 1',
      filter2_pollution: 'Фильтр 2',
      filter3_pollution: 'Фильтр 3',
      filter4_pollution: 'Фильтр 4',
      is_warn_err: 'Предупреждение',
      is_fatal_err: 'Критическая ошибка',
      danger_overheat: 'Угроза перегрева',
      change_filter: 'Требуется замена фильтра',
      unit_running: 'Установка включена',
    },
    unit_state: {
      off: 'Выключено',
      on: 'Включено',
      turning_off: 'Выключение',
      turning_on: 'Включение',
      unknown: 'Неизвестно',
    },
    mode: {
      heat: 'Обогрев',
      cool: 'Охлаждение',
      auto_heat: 'Авто-Обогрев',
      auto_cool: 'Авто-Охлаждение',
      fan_only: 'Вентиляция',
      auto: 'Авто',
      off: 'Выключено',
      unknown: 'Неизвестно',
    },
    color_msg: {
      normal: 'Норма',
      warning: 'Предупреждение',
      error: 'Ошибка',
      unknown: 'Неизвестно',
    },
    color_ind: {
      off: 'Выключено',
      transition: 'Переходный процесс',
      on: 'Включено',
      unknown: 'Неизвестно',
    },
    filter_status: {
      no_data: 'Нет данных',
      excellent: 'Отличное',
      good: 'Хорошее',
      replace_soon: 'Требуется замена',
      clogged: 'Забит',
    },
    models: {
      '400_lux': 'Breezart 400 Lux (Электрический, до 400 м³/ч)',
      '550_lux': 'Breezart 550 Lux (Электрический, до 550 м³/ч)',
      '550_aqua': 'Breezart 550 Aqua (Водяной + увлажнитель, до 550 м³/ч)',
      '700_lux': 'Breezart 700 Lux (Электрический + охлаждение, до 700 м³/ч)',
      '1000_lux': 'Breezart 1000 Lux (Электрический, 10 скоростей, до 1000 м³/ч)',
      '1000_aqua': 'Breezart 1000 Aqua (Водяной + увлажнитель, до 1000 м³/ч)',
      '2000_lux': 'Breezart 2000 Lux (Промышленный, до 2000 м³/ч)',
      custom: 'Пользовательский / Автоопределение (VPr07)',
    },
    config: {
      title: 'Вентиляция Breezart',
      description: 'Настройка подключения и выбор модели установки Breezart',
      modelLabel: 'Модель установки (преднастройка)',
      hostLabel: 'Хост (IP-адрес)',
      portLabel: 'TCP-порт',
      passwordLabel: 'Пароль удалённого доступа',
      submitButton: 'Проверить подключение и применить',
      errors: {
        cannot_connect: 'Не удалось подключиться к контроллеру Breezart',
        invalid_auth: 'Неверный пароль удалённого доступа',
        unknown: 'Неожиданная ошибка при подключении',
      },
    },
  },
  en: {
    entities: {
      climate: 'Climate',
      power: 'Power',
      target_temperature: 'Target temperature',
      fan_speed: 'Fan speed',
      temperature: 'Temperature (control point)',
      temp_supply: 'Supply air temperature',
      temp_room: 'Room temperature',
      temp_outdoor: 'Outdoor air temperature',
      temp_water: 'Heat carrier (water) temperature',
      temperature_target: 'Target temperature',
      speed: 'Fan speed',
      speed_target: 'Target fan speed',
      speed_fact: 'Actual fan speed',
      power_consumption: 'Power consumption',
      filter_dust: 'Filter pollution',
      humidity: 'Humidity',
      unit_state: 'Unit state',
      mode: 'Operating mode',
      mode_set: 'Requested mode',
      color_ind: 'Power indicator',
      color_msg: 'Message status',
      msg: 'Device message',
      firmware_ver: 'Firmware version',
      protocol_ver: 'Protocol version',
      humidity_supply: 'Supply air humidity',
      humidity_room: 'Room humidity',
      humidity_outdoor: 'Outdoor air humidity',
      co2: 'CO₂',
      voc: 'VOC (air quality)',
      filter1_pollution: 'Filter 1',
      filter2_pollution: 'Filter 2',
      filter3_pollution: 'Filter 3',
      filter4_pollution: 'Filter 4',
      is_warn_err: 'Warning',
      is_fatal_err: 'Fatal error',
      danger_overheat: 'Overheat hazard',
      change_filter: 'Filter replacement required',
      unit_running: 'Unit running',
    },
    unit_state: {
      off: 'Off',
      on: 'On',
      turning_off: 'Turning off',
      turning_on: 'Turning on',
      unknown: 'Unknown',
    },
    mode: {
      heat: 'Heating',
      cool: 'Cooling',
      auto_heat: 'Auto Heating',
      auto_cool: 'Auto Cooling',
      fan_only: 'Ventilation',
      auto: 'Auto',
      off: 'Off',
      unknown: 'Unknown',
    },
    color_msg: {
      normal: 'Normal',
      warning: 'Warning',
      error: 'Error',
      unknown: 'Unknown',
    },
    color_ind: {
      off: 'Off',
      transition: 'Transitioning',
      on: 'On',
      unknown: 'Unknown',
    },
    filter_status: {
      no_data: 'No data',
      excellent: 'Excellent',
      good: 'Good',
      replace_soon: 'Replace soon',
      clogged: 'Clogged',
    },
    models: {
      '400_lux': 'Breezart 400 Lux (Electric, up to 400 m³/h)',
      '550_lux': 'Breezart 550 Lux (Electric, up to 550 m³/h)',
      '550_aqua': 'Breezart 550 Aqua (Water heater + humidifier, up to 550 m³/h)',
      '700_lux': 'Breezart 700 Lux (Electric + cooling, up to 700 m³/h)',
      '1000_lux': 'Breezart 1000 Lux (Electric, 10 speeds, up to 1000 m³/h)',
      '1000_aqua': 'Breezart 1000 Aqua (Water heater + humidifier, up to 1000 m³/h)',
      '2000_lux': 'Breezart 2000 Lux (Commercial, up to 2000 m³/h)',
      custom: 'Custom / Auto-detect (VPr07)',
    },
    config: {
      title: 'Breezart Ventilation',
      description: 'Configure connection and model preset for your Breezart controller',
      modelLabel: 'Unit Model Preset',
      hostLabel: 'Host (IP address)',
      portLabel: 'TCP Port',
      passwordLabel: 'Remote Access Password',
      submitButton: 'Test Connection & Apply Preset',
      errors: {
        cannot_connect: 'Failed to connect to the Breezart controller',
        invalid_auth: 'Invalid remote access password',
        unknown: 'Unexpected error occurred',
      },
    },
  },
};

export function translateEntity(key: string, lang: Language): string {
  return I18N_CATALOG[lang].entities[key] ?? key;
}

export function translateState(
  category: 'unit_state' | 'mode' | 'color_msg' | 'color_ind' | 'filter_status',
  key: string,
  lang: Language
): string {
  const dict = I18N_CATALOG[lang][category] as Record<string, string>;
  return dict[key] ?? key;
}
