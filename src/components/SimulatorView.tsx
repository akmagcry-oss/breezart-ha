import React, { useState } from 'react';
import {
  BREEZART_CONSTANTS,
  I18N_CATALOG,
  MODEL_PRESETS,
  Language,
  ModelPresetId,
  ProtocolType,
  HvacModeKey,
  buildModbusReadFrameHex,
  buildModbusWriteSingleFrameHex,
  buildProtocolRequest,
  classifyFilterPollution,
  detectFreezeHazard,
  getModelPreset,
  mapCmdModeToModbusHc,
  resolveHvacAction,
  resolveHvacMode,
  scaleSpeedToModbusPercent100,
  translateEntity,
  translateState,
} from '../domain/breezart';

interface SimulatorViewProps {
  lang: Language;
  selectedModel: ModelPresetId;
  onSelectModel: (model: ModelPresetId) => void;
}

export const SimulatorView: React.FC<SimulatorViewProps> = ({
  lang,
  selectedModel,
  onSelectModel,
}) => {
  const preset = getModelPreset(selectedModel);
  const t = I18N_CATALOG[lang];

  // Config Flow form state (defaults to user's JLV135 + JL204c7 setup at 192.168.2.38:502)
  const [protocolInput, setProtocolInput] = useState<ProtocolType>('modbus_tcp');
  const [hostInput, setHostInput] = useState<string>(BREEZART_CONSTANTS.DEFAULT_HOST);
  const [portInput, setPortInput] = useState<string>(String(BREEZART_CONSTANTS.DEFAULT_MODBUS_PORT));
  const [slaveIdInput, setSlaveIdInput] = useState<string>(String(BREEZART_CONSTANTS.DEFAULT_SLAVE_ID));
  const [passwordInput, setPasswordInput] = useState<string>(BREEZART_CONSTANTS.DEFAULT_PASSWORD);
  const [speedMaxInput, setSpeedMaxInput] = useState<number>(preset.speedMax);
  const [tempMinInput, setTempMinInput] = useState<number>(preset.tempMin);
  const [tempMaxInput, setTempMaxInput] = useState<number>(preset.tempMax);
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSavedBanner, setConfigSavedBanner] = useState<string | null>(null);

  // Simulated device state
  const [power, setPower] = useState<boolean>(true);
  const [modeCode, setModeCode] = useState<number>(BREEZART_CONSTANTS.MODE_HEAT);
  const [targetTemp, setTargetTemp] = useState<number>(22);
  const [supplyTemp, setSupplyTemp] = useState<number>(21.6);
  const [outdoorTemp, setOutdoorTemp] = useState<number>(-4.5);
  const [roomTemp, setRoomTemp] = useState<number>(22.4);
  const [waterTemp, setWaterTemp] = useState<number>(48.0);
  const [targetSpeed, setTargetSpeed] = useState<number>(5);
  const [humidity, setHumidity] = useState<number>(44);
  const [co2, setCo2] = useState<number>(520);
  const [voc, setVoc] = useState<number>(115);
  const [filter1Pollution, setFilter1Pollution] = useState<number>(22);
  const [filter2Pollution, setFilter2Pollution] = useState<number>(64);
  const [warnErr, setWarnErr] = useState<boolean>(false);
  const [fatalErr, setFatalErr] = useState<boolean>(false);
  const [overheat, setOverheat] = useState<boolean>(false);
  const [freezeAlarm, setFreezeAlarm] = useState<boolean>(false);
  const [sensorFilter, setSensorFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [sensorSearch, setSensorSearch] = useState<string>('');
  const [lastTxCommand, setLastTxCommand] = useState<string>(
    `FC=0x03 Read Holding[0..8]: ${buildModbusReadFrameHex(0x03, 0, 9, 1, 1)}`
  );

  const activeSpeedMax = Math.max(1, Math.min(10, speedMaxInput || preset.speedMax));
  const activeTempMin = Math.max(5, Math.min(35, tempMinInput || preset.tempMin));
  const activeTempMax = Math.max(activeTempMin + 1, Math.min(45, tempMaxInput || preset.tempMax));

  const clampedTargetTemp = Math.min(
    activeTempMax,
    Math.max(activeTempMin, targetTemp)
  );
  const clampedSpeed = Math.min(
    activeSpeedMax,
    Math.max(preset.speedMin, targetSpeed)
  );

  const unitStateCode = power
    ? BREEZART_CONSTANTS.UNIT_STATE_ON
    : BREEZART_CONSTANTS.UNIT_STATE_OFF;
  const hvacMode = resolveHvacMode(power, modeCode);
  const hvacAction = resolveHvacAction(power, unitStateCode, modeCode);
  const isFreezeHazard = detectFreezeHazard({
    hwFreezeFlag: freezeAlarm,
    power,
    modeCode,
    controlTemp: supplyTemp,
    supplyTemp,
    outdoorTemp,
    waterTemp: preset.hasWaterHeater ? waterTemp : null,
  });

  const parsedPass = Number.parseInt(passwordInput, 10) || 21579;
  const parsedSlaveId = Number.parseInt(slaveIdInput, 10) || 1;
  const isModbusActive =
    protocolInput === 'modbus_tcp' ||
    (protocolInput === 'auto' && Number.parseInt(portInput, 10) === 502);

  const handleProtocolChange = (nextProto: ProtocolType) => {
    setProtocolInput(nextProto);
    if (nextProto === 'modbus_tcp') {
      setPortInput('502');
      setLastTxCommand(
        `FC=0x03 Read Holding[0..8]: ${buildModbusReadFrameHex(0x03, 0, 9, parsedSlaveId, 1)}`
      );
    } else if (nextProto === 'native_tcp') {
      setPortInput('1560');
      setLastTxCommand(buildProtocolRequest(BREEZART_CONSTANTS.REQ_GET_STATE, parsedPass));
    }
  };

  const handleConfigSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setConfigError(null);
    setConfigSavedBanner(null);

    const trimmedHost = hostInput.trim();
    const portNum = Number.parseInt(portInput, 10);
    const passNum = Number.parseInt(passwordInput, 10);

    if (!trimmedHost || Number.isNaN(portNum) || portNum < 1 || portNum > 65535) {
      setConfigError(t.config.errors.cannot_connect);
      return;
    }
    if (
      !isModbusActive &&
      (Number.isNaN(passNum) ||
        passNum < 0 ||
        passNum > BREEZART_CONSTANTS.MAX_UINT16 ||
        passwordInput.trim() === '00000')
    ) {
      setConfigError(t.config.errors.invalid_auth);
      return;
    }

    const resolvedPort = protocolInput === 'auto' && portNum === 1560 ? 502 : portNum;
    if (isModbusActive || resolvedPort === 502) {
      setPortInput(String(resolvedPort));
      setLastTxCommand(
        `FC=0x03 Read Holding[0..8]: ${buildModbusReadFrameHex(0x03, 0, 9, parsedSlaveId, 1)}`
      );
      setConfigSavedBanner(
        lang === 'ru'
          ? `Подключено по Modbus TCP (JLV135 / JL204c7): Breezart ${preset.name} (${trimmedHost}:${resolvedPort}, Slave ID=${parsedSlaveId})`
          : `Connected via Modbus TCP (JLV135 / JL204c7): Breezart ${preset.name} (${trimmedHost}:${resolvedPort}, Slave ID=${parsedSlaveId})`
      );
    } else {
      setLastTxCommand(buildProtocolRequest(BREEZART_CONSTANTS.REQ_GET_PROPERTIES, passNum));
      setConfigSavedBanner(
        lang === 'ru'
          ? `Подключено по Native TCP: Breezart ${preset.name} (${trimmedHost}:${portNum})`
          : `Connected via Native TCP: Breezart ${preset.name} (${trimmedHost}:${portNum})`
      );
    }
  };

  const handlePowerToggle = () => {
    const nextPower = !power;
    setPower(nextPower);
    if (isModbusActive) {
      const regVal = nextPower ? BREEZART_CONSTANTS.POWER_ON : BREEZART_CONSTANTS.POWER_OFF;
      setLastTxCommand(
        `FC=0x06 Write Holding[3] (on_off=${regVal}): ${buildModbusWriteSingleFrameHex(
          BREEZART_CONSTANTS.MODBUS_HR_POWER_STATE,
          regVal,
          parsedSlaveId,
          2
        )}`
      );
    } else {
      setLastTxCommand(
        buildProtocolRequest(
          BREEZART_CONSTANTS.REQ_SET_POWER,
          parsedPass,
          nextPower ? BREEZART_CONSTANTS.POWER_ON : BREEZART_CONSTANTS.POWER_OFF
        )
      );
    }
  };

  const handleTempChange = (nextTemp: number) => {
    setTargetTemp(nextTemp);
    setSupplyTemp(Number((nextTemp - 0.3).toFixed(1)));
    if (isModbusActive) {
      const rawDeci = Math.round(nextTemp * 10);
      setLastTxCommand(
        `FC=0x06 Write Holding[1] (t_task=${rawDeci} -> ${nextTemp.toFixed(1)}°C): ${buildModbusWriteSingleFrameHex(
          BREEZART_CONSTANTS.MODBUS_HR_TEMP_TARGET,
          rawDeci,
          parsedSlaveId,
          3
        )}`
      );
    } else {
      setLastTxCommand(
        buildProtocolRequest(BREEZART_CONSTANTS.REQ_SET_TEMP, parsedPass, nextTemp)
      );
    }
  };

  const handleSpeedChange = (nextSpeed: number) => {
    setTargetSpeed(nextSpeed);
    if (isModbusActive) {
      const rawPct100 = scaleSpeedToModbusPercent100(nextSpeed, activeSpeedMax);
      setLastTxCommand(
        `FC=0x06 Write Holding[0] (fan_task=${rawPct100} -> ${Math.round(rawPct100 / 100)}%): ${buildModbusWriteSingleFrameHex(
          BREEZART_CONSTANTS.MODBUS_HR_FAN_SPEED,
          rawPct100,
          parsedSlaveId,
          4
        )}`
      );
    } else {
      setLastTxCommand(
        buildProtocolRequest(BREEZART_CONSTANTS.REQ_SET_FAN_SPEED, parsedPass, nextSpeed)
      );
    }
  };

  const handleHvacModeSelect = (nextMode: HvacModeKey) => {
    if (nextMode === 'off') {
      setPower(false);
      if (isModbusActive) {
        setLastTxCommand(
          `FC=0x06 Write Holding[3] (on_off=0): ${buildModbusWriteSingleFrameHex(
            BREEZART_CONSTANTS.MODBUS_HR_POWER_STATE,
            0,
            parsedSlaveId,
            5
          )}`
        );
      } else {
        setLastTxCommand(
          buildProtocolRequest(
            BREEZART_CONSTANTS.REQ_SET_POWER,
            parsedPass,
            BREEZART_CONSTANTS.POWER_OFF
          )
        );
      }
      return;
    }
    setPower(true);
    let newModeCode: number = BREEZART_CONSTANTS.MODE_HEAT;
    let cmdCode: number = BREEZART_CONSTANTS.CMD_MODE_HEAT;
    if (nextMode === 'heat') {
      newModeCode = BREEZART_CONSTANTS.MODE_HEAT;
      cmdCode = BREEZART_CONSTANTS.CMD_MODE_HEAT;
    } else if (nextMode === 'cool') {
      newModeCode = BREEZART_CONSTANTS.MODE_COOL;
      cmdCode = BREEZART_CONSTANTS.CMD_MODE_COOL;
    } else if (nextMode === 'auto') {
      newModeCode = BREEZART_CONSTANTS.MODE_AUTO_HEAT;
      cmdCode = BREEZART_CONSTANTS.CMD_MODE_AUTO;
    } else if (nextMode === 'fan_only') {
      newModeCode = BREEZART_CONSTANTS.MODE_VENT;
      cmdCode = BREEZART_CONSTANTS.CMD_MODE_VENT;
    }
    setModeCode(newModeCode);
    if (isModbusActive) {
      const modbusHc = mapCmdModeToModbusHc(cmdCode);
      setLastTxCommand(
        `FC=0x06 Write Holding[7] (mode_hc=${modbusHc}): ${buildModbusWriteSingleFrameHex(
          BREEZART_CONSTANTS.MODBUS_HR_MODE_HC,
          modbusHc,
          parsedSlaveId,
          6
        )}`
      );
    } else {
      setLastTxCommand(
        buildProtocolRequest(BREEZART_CONSTANTS.REQ_SET_MODE, parsedPass, cmdCode)
      );
    }
  };

  const unitStateKey = power ? 'on' : 'off';
  const modeKeyMap: Record<number, string> = {
    0: 'heat',
    1: 'cool',
    2: 'auto_heat',
    3: 'auto_cool',
    4: 'fan_only',
    5: 'off',
  };
  const currentModeStateKey = power ? modeKeyMap[modeCode] ?? 'heat' : 'off';
  const colorMsgKey = fatalErr ? 'error' : warnErr ? 'warning' : 'normal';
  const colorIndKey = power ? 'on' : 'off';
  const filter1StatusKey = classifyFilterPollution(filter1Pollution);
  const filter2StatusKey = classifyFilterPollution(filter2Pollution);

  const powerWatts = power
    ? preset.heaterType === 'electric'
      ? Math.round(350 + clampedSpeed * 180 + Math.max(0, clampedTargetTemp - outdoorTemp) * 42)
      : Math.round(45 + clampedSpeed * 28)
    : 0;

  const allSensorRows = [
    {
      key: 'temperature',
      value: `${clampedTargetTemp.toFixed(1)} °C`,
      category: 'measurement',
    },
    {
      key: 'temp_supply',
      value: `${supplyTemp.toFixed(1)} °C`,
      category: 'measurement',
    },
    {
      key: 'temp_room',
      value: `${roomTemp.toFixed(1)} °C`,
      category: 'measurement',
    },
    {
      key: 'temp_outdoor',
      value: `${outdoorTemp.toFixed(1)} °C`,
      category: 'measurement',
    },
    {
      key: 'temp_water',
      value: preset.hasWaterHeater ? `${waterTemp.toFixed(1)} °C` : '— (0xFB07)',
      category: 'measurement',
    },
    {
      key: 'temperature_target',
      value: `${clampedTargetTemp} °C`,
      category: 'diagnostic',
    },
    {
      key: 'speed',
      value: `${power ? clampedSpeed : 0} / ${activeSpeedMax}`,
      category: 'measurement',
    },
    {
      key: 'speed_target',
      value: `${clampedSpeed} / ${activeSpeedMax}`,
      category: 'diagnostic',
    },
    {
      key: 'speed_fact',
      value: `${power ? Math.round((clampedSpeed / activeSpeedMax) * 100) : 0} %`,
      category: 'measurement',
    },
    {
      key: 'power_consumption',
      value: `${powerWatts} W`,
      category: 'measurement',
    },
    {
      key: 'filter_dust',
      value: `${filter1Pollution} %`,
      category: 'diagnostic',
    },
    {
      key: 'humidity',
      value: preset.hasHumidifier ? `${humidity} %` : '— (255)',
      category: 'measurement',
    },
    {
      key: 'unit_state',
      value: translateState('unit_state', unitStateKey, lang),
      rawKey: unitStateKey,
      category: 'enum',
    },
    {
      key: 'mode',
      value: translateState('mode', currentModeStateKey, lang),
      rawKey: currentModeStateKey,
      category: 'enum',
    },
    {
      key: 'mode_set',
      value: translateState('mode', hvacMode === 'off' ? 'heat' : hvacMode, lang),
      rawKey: hvacMode === 'off' ? 'heat' : hvacMode,
      category: 'enum',
    },
    {
      key: 'color_ind',
      value: translateState('color_ind', colorIndKey, lang),
      rawKey: colorIndKey,
      category: 'enum',
    },
    {
      key: 'color_msg',
      value: translateState('color_msg', colorMsgKey, lang),
      rawKey: colorMsgKey,
      category: 'enum',
    },
    {
      key: 'msg',
      value: fatalErr ? 'ERR: FATAL OVERLOAD' : warnErr ? 'WARN: CHECK FILTER' : 'OK',
      category: 'diagnostic',
    },
    {
      key: 'firmware_ver',
      value: '2054',
      category: 'diagnostic',
    },
    {
      key: 'protocol_ver',
      value: '1.7',
      category: 'diagnostic',
    },
    {
      key: 'humidity_supply',
      value: `${humidity} %`,
      category: 'measurement',
    },
    {
      key: 'humidity_room',
      value: '42 %',
      category: 'measurement',
    },
    {
      key: 'humidity_outdoor',
      value: '68 %',
      category: 'measurement',
    },
    {
      key: 'co2',
      value: `${co2} ppm`,
      category: 'measurement',
    },
    {
      key: 'voc',
      value: `${voc} ppb`,
      category: 'measurement',
    },
    {
      key: 'filter1_pollution',
      value: `${filter1Pollution} % · ${translateState('filter_status', filter1StatusKey, lang)}`,
      rawKey: filter1StatusKey,
      category: 'filter',
    },
    {
      key: 'filter2_pollution',
      value: `${filter2Pollution} % · ${translateState('filter_status', filter2StatusKey, lang)}`,
      rawKey: filter2StatusKey,
      category: 'filter',
    },
    {
      key: 'filter3_pollution',
      value: `12 % · ${translateState('filter_status', 'excellent', lang)}`,
      rawKey: 'excellent',
      category: 'filter',
    },
    {
      key: 'filter4_pollution',
      value: `— · ${translateState('filter_status', 'no_data', lang)}`,
      rawKey: 'no_data',
      category: 'filter',
    },
  ].map((row) => ({
    ...row,
    name: translateEntity(row.key, lang),
    enabledByPreset: preset.enabledSensors.includes(row.key),
  }));

  const filteredSensors = allSensorRows.filter((row) => {
    if (sensorFilter === 'enabled' && !row.enabledByPreset) return false;
    if (sensorFilter === 'disabled' && row.enabledByPreset) return false;
    if (sensorSearch.trim()) {
      const q = sensorSearch.toLowerCase();
      return (
        row.name.toLowerCase().includes(q) ||
        row.key.toLowerCase().includes(q) ||
        row.value.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const availableHvacModes: HvacModeKey[] = preset.hasCooler
    ? ['off', 'fan_only', 'heat', 'cool', 'auto']
    : ['off', 'fan_only', 'heat', 'auto'];

  const speedButtons = Array.from(
    { length: activeSpeedMax - preset.speedMin + 1 },
    (_, idx) => preset.speedMin + idx
  );

  // Simulated VPr07 response packet
  const vprTemprWord = ((activeTempMax << 8) | activeTempMin).toString(16).padStart(4, '0');
  const vprSpeedWord = ((activeSpeedMax << 8) | preset.speedMin).toString(16).padStart(4, '0');
  const vprMiscWord = (
    ((preset.hasCooler ? 1 : 0) << 14) |
    ((preset.hasHumidifier ? 1 : 0) << 13)
  )
    .toString(16)
    .padStart(4, '0');

  return (
    <div className="space-y-8">
      {/* Row 1: Config Flow + Climate Entity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Config Flow Wizard (5 cols) */}
        <section
          aria-labelledby="config-flow-heading"
          className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <p className="text-xs font-mono text-slate-500">
                  custom_components/breezart/config_flow.py
                </p>
                <h2 id="config-flow-heading" className="text-lg font-bold text-slate-900 mt-0.5">
                  {t.config.title}
                </h2>
              </div>
              <span className="text-xs font-mono text-slate-500">
                v{BREEZART_CONSTANTS.CONFIG_FLOW_VERSION}
              </span>
            </div>

            <p className="text-sm text-slate-600 mt-3">{t.config.description}</p>

            <form onSubmit={handleConfigSubmit} className="mt-5 space-y-4">
              <div>
                <label
                  htmlFor="config-model-select"
                  className="block text-xs font-semibold text-slate-700 mb-1.5"
                >
                  {t.config.modelLabel}
                </label>
                <select
                  id="config-model-select"
                  value={selectedModel}
                  onChange={(e) => onSelectModel(e.target.value as ModelPresetId)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
                >
                  {(Object.keys(MODEL_PRESETS) as ModelPresetId[]).map((mId) => (
                    <option key={mId} value={mId}>
                      {t.models[mId]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="config-protocol-select"
                  className="block text-xs font-semibold text-slate-700 mb-1.5"
                >
                  {t.config.protocolLabel}
                </label>
                <select
                  id="config-protocol-select"
                  value={protocolInput}
                  onChange={(e) => handleProtocolChange(e.target.value as ProtocolType)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-600 focus:outline-none"
                >
                  {(['auto', 'modbus_tcp', 'native_tcp'] as ProtocolType[]).map((pId) => (
                    <option key={pId} value={pId}>
                      {t.protocols[pId]}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-4 gap-3">
                <div className="col-span-2">
                  <label
                    htmlFor="config-host-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.hostLabel}
                  </label>
                  <input
                    id="config-host-input"
                    type="text"
                    value={hostInput}
                    onChange={(e) => setHostInput(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label
                    htmlFor="config-port-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.portLabel}
                  </label>
                  <input
                    id="config-port-input"
                    type="number"
                    value={portInput}
                    onChange={(e) => setPortInput(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label
                    htmlFor="config-slave-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.slaveIdLabel}
                  </label>
                  <input
                    id="config-slave-input"
                    type="number"
                    min={1}
                    max={247}
                    value={slaveIdInput}
                    onChange={(e) => setSlaveIdInput(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label
                    htmlFor="config-speed-max-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.speedMaxLabel}
                  </label>
                  <input
                    id="config-speed-max-input"
                    type="number"
                    min={1}
                    max={10}
                    value={speedMaxInput}
                    onChange={(e) => setSpeedMaxInput(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label
                    htmlFor="config-temp-min-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.tempMinLabel}
                  </label>
                  <input
                    id="config-temp-min-input"
                    type="number"
                    min={5}
                    max={30}
                    value={tempMinInput}
                    onChange={(e) => setTempMinInput(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label
                    htmlFor="config-temp-max-input"
                    className="block text-xs font-semibold text-slate-700 mb-1.5"
                  >
                    {t.config.tempMaxLabel}
                  </label>
                  <input
                    id="config-temp-max-input"
                    type="number"
                    min={15}
                    max={45}
                    value={tempMaxInput}
                    onChange={(e) => setTempMaxInput(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="config-password-input"
                  className="block text-xs font-semibold text-slate-700 mb-1.5"
                >
                  {t.config.passwordLabel}
                </label>
                <input
                  id="config-password-input"
                  type="text"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  disabled={isModbusActive}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono tabular-nums text-slate-900 focus:border-blue-600 focus:outline-none disabled:bg-slate-100 disabled:text-slate-400"
                />
                <p className="text-xs text-slate-500 mt-1">
                  {isModbusActive
                    ? lang === 'ru'
                      ? 'Для пульта JLV135 / контроллера JL204c7 (Modbus TCP :502) пароль не требуется'
                      : 'Password is not required for JLV135 / JL204c7 (Modbus TCP :502)'
                    : lang === 'ru'
                      ? 'Подсказка: введите 00000 для проверки ошибки invalid_auth (VEPas)'
                      : 'Tip: enter 00000 to test localized invalid_auth (VEPas) error handling'}
                </p>
              </div>

              {configError && (
                <div
                  role="alert"
                  className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700"
                >
                  {configError}
                </div>
              )}

              {configSavedBanner && (
                <div
                  role="status"
                  className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800"
                >
                  {configSavedBanner}
                </div>
              )}

              <button
                type="submit"
                className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors whitespace-nowrap"
              >
                {t.config.submitButton}
              </button>
            </form>
          </div>

          {/* DeviceInfo preview */}
          <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-600 space-y-1">
            <div className="flex justify-between">
              <span>DeviceInfo.name:</span>
              <span className="font-mono font-semibold text-slate-900">
                Breezart {preset.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span>
                {lang === 'ru' ? 'Контроллер / Протокол:' : 'Controller / Protocol:'}
              </span>
              <span className="font-mono text-slate-800">
                {isModbusActive
                  ? `JLV135 + JL204c7 (SW 1.7.14) · Modbus :${portInput}`
                  : `TPD-283U-H + JL205 · Native TCP :${portInput}`}
              </span>
            </div>
            <div className="flex justify-between">
              <span>
                {lang === 'ru' ? 'Диапазон уставок:' : 'Preset bounds:'}
              </span>
              <span className="font-mono tabular-nums text-slate-800">
                {activeTempMin}..{activeTempMax} °C · {lang === 'ru' ? 'Скор.' : 'Speed'}{' '}
                {preset.speedMin}..{activeSpeedMax}
              </span>
            </div>
          </div>
        </section>

        {/* Climate & Control Entities (7 cols) */}
        <section
          aria-labelledby="climate-card-heading"
          className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 flex flex-col justify-between"
        >
          <div>
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <p className="text-xs font-mono text-slate-500">
                  climate.breezart_climate · switch.breezart_power · number.*
                </p>
                <h2 id="climate-card-heading" className="text-lg font-bold text-slate-900 mt-0.5">
                  {translateEntity('climate', lang)} — Breezart {preset.name}
                </h2>
              </div>

              <button
                type="button"
                onClick={handlePowerToggle}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                  power
                    ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                    : 'bg-slate-200 text-slate-800 hover:bg-slate-300'
                }`}
              >
                {translateEntity('power', lang)}: {translateState('unit_state', unitStateKey, lang)}
              </button>
            </div>

            {/* Primary Climate Readout */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-5">
              <div className="border border-slate-200 rounded-lg p-4">
                <p className="text-xs text-slate-500">{translateEntity('temp_supply', lang)}</p>
                <p className="text-2xl font-bold font-mono tabular-nums text-slate-900 mt-1">
                  {supplyTemp.toFixed(1)} °C
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  HVACAction: <span className="font-mono font-semibold">{hvacAction}</span>
                </p>
              </div>

              <div className="border border-slate-200 rounded-lg p-4">
                <p className="text-xs text-slate-500">
                  {translateEntity('target_temperature', lang)}
                </p>
                <p className="text-2xl font-bold font-mono tabular-nums text-blue-600 mt-1">
                  {clampedTargetTemp} °C
                </p>
                <p className="text-xs text-slate-500 mt-1 tabular-nums">
                  Min {activeTempMin} °C · Max {activeTempMax} °C
                </p>
              </div>

              <div className="border border-slate-200 rounded-lg p-4">
                <p className="text-xs text-slate-500">{translateEntity('fan_speed', lang)}</p>
                <p className="text-2xl font-bold font-mono tabular-nums text-slate-900 mt-1">
                  {power ? clampedSpeed : 0} <span className="text-sm font-normal text-slate-500">/ {activeSpeedMax}</span>
                </p>
                <p className="text-xs text-slate-500 mt-1 tabular-nums">
                  {preset.airflowM3h > 0
                    ? `${Math.round((clampedSpeed / activeSpeedMax) * preset.airflowM3h)} m³/h`
                    : 'Auto VPr07 / Modbus'}
                </p>
              </div>
            </div>

            {/* HVAC Mode Segmented Control */}
            <div className="mb-5">
              <p className="text-xs font-semibold text-slate-700 mb-2">
                {translateEntity('mode', lang)} (HVACMode)
              </p>
              <div className="flex flex-wrap gap-1.5 bg-slate-100 p-1.5 rounded-lg">
                {availableHvacModes.map((mKey) => {
                  const active = hvacMode === mKey;
                  return (
                    <button
                      key={mKey}
                      type="button"
                      onClick={() => handleHvacModeSelect(mKey)}
                      className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                        active
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {translateState('mode', mKey, lang)}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Target Temperature Slider */}
            <div className="mb-5">
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1.5">
                <label htmlFor="target-temp-slider">
                  {translateEntity('target_temperature', lang)} (
                  {isModbusActive ? 'Holding[1] °C×10' : 'VWTmp'})
                </label>
                <span className="font-mono tabular-nums">{clampedTargetTemp} °C</span>
              </div>
              <input
                id="target-temp-slider"
                type="range"
                min={activeTempMin}
                max={activeTempMax}
                step={1}
                value={clampedTargetTemp}
                onChange={(e) => handleTempChange(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Fan Speed Buttons */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-2">
                <span>
                  {translateEntity('fan_speed', lang)} (
                  {isModbusActive ? 'Holding[0] %×100' : 'VWSpd'} · 1..{activeSpeedMax})
                </span>
                <span className="font-mono tabular-nums">
                  {lang === 'ru' ? 'Выбрана скорость' : 'Selected speed'}: {clampedSpeed} (
                  {Math.round((clampedSpeed / activeSpeedMax) * 100)}%)
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {speedButtons.map((spd) => (
                  <button
                    key={spd}
                    type="button"
                    onClick={() => handleSpeedChange(spd)}
                    className={`w-9 h-9 rounded-lg font-mono text-xs font-semibold tabular-nums transition-colors ${
                      clampedSpeed === spd
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {spd}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Live Modbus TCP / Native TCP Packet Inspector */}
          <div className="mt-6 pt-4 border-t border-slate-100">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
              <span className="text-slate-500">
                {isModbusActive ? 'Modbus TCP' : 'Native TCP'} {hostInput}:{portInput} TX:
              </span>
              <code className="bg-slate-900 text-emerald-400 px-2.5 py-1 rounded">
                {lastTxCommand}
              </code>
              <span className="text-slate-500">
                {isModbusActive ? 'JL204c7 RX:' : 'VPr07 RX:'}
              </span>
              <code className="bg-slate-100 text-slate-800 px-2.5 py-1 rounded">
                {isModbusActive
                  ? `HR[0]=${scaleSpeedToModbusPercent100(clampedSpeed, preset.speedMax)} HR[1]=${clampedTargetTemp * 10} HR[3]=${power ? 1 : 0} IR[13]=${Math.round(supplyTemp * 10)}`
                  : `VPr07_${vprTemprWord}_${vprSpeedWord}_0000_${vprMiscWord}_0107_0000_0806`}
              </code>
            </div>
          </div>
        </section>
      </div>

      {/* Row 2: Binary Sensors + Filter Pollution Simulator */}
      <section
        aria-labelledby="binary-sensors-heading"
        className="bg-white border border-slate-200 rounded-xl p-6"
      >
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              custom_components/breezart/binary_sensor.py · sensor.py (BreezartFilterSensor)
            </p>
            <h2 id="binary-sensors-heading" className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? 'Бинарные сенсоры и диагностика фильтров (RU / EN)'
                : 'Binary Sensors & Filter Pollution Diagnostics (RU / EN)'}
            </h2>
          </div>
          <span className="text-xs text-slate-500">
            {lang === 'ru'
              ? 'Нажмите на бинарный сенсор для имитации аварии в пакете VSt07'
              : 'Click any binary sensor below to simulate VSt07 fault flags'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 mt-4">
          {[
            {
              key: 'unit_running',
              haKey: 'power',
              active: power,
              toggle: handlePowerToggle,
              isProblem: false,
            },
            {
              key: 'is_warn_err',
              haKey: 'is_warn_err',
              active: warnErr,
              toggle: () => setWarnErr(!warnErr),
              isProblem: true,
            },
            {
              key: 'is_fatal_err',
              haKey: 'is_fatal_err',
              active: fatalErr,
              toggle: () => setFatalErr(!fatalErr),
              isProblem: true,
            },
            {
              key: 'danger_overheat',
              haKey: 'danger_overheat',
              active: overheat,
              toggle: () => setOverheat(!overheat),
              isProblem: true,
            },
            {
              key: 'danger_freeze',
              haKey: 'danger_freeze',
              active: isFreezeHazard,
              toggle: () => setFreezeAlarm(!freezeAlarm),
              isProblem: true,
            },
            {
              key: 'change_filter',
              haKey: 'change_filter',
              active: filter1Pollution >= BREEZART_CONSTANTS.FILTER_POLLUTION_REPLACE_MAX || filter2Pollution >= BREEZART_CONSTANTS.FILTER_POLLUTION_REPLACE_MAX,
              toggle: () =>
                setFilter1Pollution((prev) => (prev >= 85 ? 22 : 88)),
              isProblem: true,
            },
          ].map((bs) => (
            <button
              key={bs.haKey}
              type="button"
              onClick={bs.toggle}
              className={`text-left p-3.5 rounded-lg border transition-colors ${
                bs.active
                  ? bs.isProblem
                    ? 'border-red-300 bg-red-50/70 text-red-950'
                    : 'border-emerald-300 bg-emerald-50/70 text-emerald-950'
                  : 'border-slate-200 bg-slate-50/60 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <p className="text-xs font-mono text-slate-500">
                binary_sensor.breezart_{bs.haKey}
              </p>
              <p className="text-sm font-semibold mt-1">{translateEntity(bs.key, lang)}</p>
              <p className="text-xs font-mono font-semibold mt-1.5">
                {bs.active
                  ? bs.isProblem
                    ? lang === 'ru'
                      ? 'Вкл (Проблема)'
                      : 'On (Problem)'
                    : lang === 'ru'
                      ? 'Работает'
                      : 'Running'
                  : lang === 'ru'
                    ? 'Выкл (Норма)'
                    : 'Off (OK)'}
              </p>
            </button>
          ))}
        </div>

        {/* Filter 1 & Filter 2 Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-5 pt-5 border-t border-slate-100">
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1.5">
              <label htmlFor="filter1-slider">
                {translateEntity('filter1_pollution', lang)} (sensor.breezart_filter1_pollution)
              </label>
              <span className="font-mono tabular-nums">
                {filter1Pollution}% · {translateState('filter_status', filter1StatusKey, lang)} (
                {filter1StatusKey})
              </span>
            </div>
            <input
              id="filter1-slider"
              type="range"
              min={0}
              max={100}
              value={filter1Pollution}
              onChange={(e) => setFilter1Pollution(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1.5">
              <label htmlFor="filter2-slider">
                {translateEntity('filter2_pollution', lang)} (sensor.breezart_filter2_pollution)
              </label>
              <span className="font-mono tabular-nums">
                {filter2Pollution}% · {translateState('filter_status', filter2StatusKey, lang)} (
                {filter2StatusKey})
              </span>
            </div>
            <input
              id="filter2-slider"
              type="range"
              min={0}
              max={100}
              value={filter2Pollution}
              onChange={(e) => setFilter2Pollution(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>
        </div>

        {/* Device Configuration: 7 Individual Notification Switches (EntityCategory.CONFIG) */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <p className="text-xs font-mono text-slate-500">
                custom_components/breezart/switch.py (EntityCategory.CONFIG) · coordinator.py (notify.mobile_app_*)
              </p>
              <h3 className="text-sm font-bold text-slate-900 mt-0.5">
                {lang === 'ru'
                  ? 'Настройки устройства: индивидуальные переключатели уведомлений (7 событий)'
                  : 'Device Configuration: Individual Notification Toggles (7 Events)'}
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded">
              notify.notify + notify.mobile_app_*
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {(
              [
                'notify_overheat',
                'notify_freeze',
                'notify_filter',
                'notify_offline',
                'notify_online',
                'notify_power',
                'notify_other_errors',
              ] as const
            ).map((nKey) => (
              <div
                key={nKey}
                className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-800 truncate">
                    {translateEntity(nKey, lang)}
                  </p>
                  <p className="text-[11px] font-mono text-slate-500 truncate">
                    switch.breezart_{nKey}
                  </p>
                </div>
                <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded shrink-0">
                  ON
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Row 3: All 28 Sensors Table */}
      <section
        aria-labelledby="sensors-table-heading"
        className="bg-white border border-slate-200 rounded-xl p-6"
      >
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              custom_components/breezart/sensor.py · translations/{lang}.json
            </p>
            <h2 id="sensors-table-heading" className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? `Все сенсоры интеграции (${filteredSensors.length} из ${allSensorRows.length})`
                : `All Integration Sensors (${filteredSensors.length} of ${allSensorRows.length})`}
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              {(
                [
                  {
                    id: 'all',
                    label: lang === 'ru' ? `Все (${allSensorRows.length})` : `All (${allSensorRows.length})`,
                  },
                  {
                    id: 'enabled',
                    label:
                      lang === 'ru'
                        ? `Активны для ${preset.name} (${preset.enabledSensors.length})`
                        : `Enabled for ${preset.name} (${preset.enabledSensors.length})`,
                  },
                  {
                    id: 'disabled',
                    label:
                      lang === 'ru'
                        ? 'По умолч. скрыты'
                        : 'Disabled by default',
                  },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSensorFilter(tab.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                    sensorFilter === tab.id
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <input
              type="search"
              value={sensorSearch}
              onChange={(e) => setSensorSearch(e.target.value)}
              placeholder={
                lang === 'ru' ? 'Поиск сенсора или ключа...' : 'Search sensor or key...'
              }
              aria-label={lang === 'ru' ? 'Поиск сенсора' : 'Search sensor'}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
            />
          </div>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500">
                <th className="py-2.5 pr-4">
                  {lang === 'ru' ? 'Локализованное имя (HA)' : 'Localized Entity Name (HA)'}
                </th>
                <th className="py-2.5 px-4">translation_key</th>
                <th className="py-2.5 px-4">
                  {lang === 'ru' ? 'Тип / Класс' : 'Type / Class'}
                </th>
                <th className="py-2.5 px-4">
                  {lang === 'ru' ? `Пресет ${preset.name}` : `Preset ${preset.name}`}
                </th>
                <th className="py-2.5 pl-4 text-right">
                  {lang === 'ru' ? 'Значение' : 'Value'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredSensors.map((row) => (
                <tr key={row.key} className="hover:bg-slate-50/80">
                  <td className="py-2.5 pr-4 font-medium text-slate-900">{row.name}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-slate-600">
                    sensor.breezart_{row.key}
                  </td>
                  <td className="py-2.5 px-4 font-mono text-xs text-slate-500">
                    {row.category}
                  </td>
                  <td className="py-2.5 px-4 text-xs">
                    {row.enabledByPreset ? (
                      <span className="text-emerald-700 font-medium">
                        {lang === 'ru' ? 'Включён по умолчанию' : 'Enabled by default'}
                      </span>
                    ) : (
                      <span className="text-slate-400">
                        {lang === 'ru' ? 'Отключён (опционально)' : 'Disabled (optional)'}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pl-4 text-right font-mono text-xs font-semibold tabular-nums text-slate-900">
                    {row.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
