import React from 'react';
import {
  I18N_CATALOG,
  MODEL_PRESETS,
  Language,
  ModelPresetId,
  translateEntity,
} from '../domain/breezart';

interface PresetsComparisonViewProps {
  lang: Language;
  selectedModel: ModelPresetId;
  onSelectModel: (model: ModelPresetId) => void;
}

export const PresetsComparisonView: React.FC<PresetsComparisonViewProps> = ({
  lang,
  selectedModel,
  onSelectModel,
}) => {
  const presets = Object.values(MODEL_PRESETS);

  const formatHeater = (heaterType: string) => {
    if (lang === 'ru') {
      if (heaterType === 'electric') return 'Электрический (ТЭН)';
      if (heaterType === 'water') return 'Водяной (Aqua)';
      return 'Авто (по VPr07)';
    }
    if (heaterType === 'electric') return 'Electric (PTC/Fin)';
    if (heaterType === 'water') return 'Water (Aqua)';
    return 'Auto (from VPr07)';
  };

  return (
    <div className="space-y-6">
      <section className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              custom_components/breezart/const.py · MODEL_PRESETS
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? 'Преднастройки конфигурации для моделей Breezart (400 Lux, 550 Lux, 550 Aqua и др.)'
                : 'Configuration Presets for Breezart Models (400 Lux, 550 Lux, 550 Aqua, etc.)'}
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            {lang === 'ru'
              ? 'Выберите модель для применения её параметров в симуляторе и Config Flow'
              : 'Select any model preset to apply its parameters in Simulator & Config Flow'}
          </p>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500">
                <th className="py-3 pr-4">{lang === 'ru' ? 'Модель' : 'Model'}</th>
                <th className="py-3 px-4 font-mono">CONF_MODEL</th>
                <th className="py-3 px-4">{lang === 'ru' ? 'Нагреватель' : 'Heater Type'}</th>
                <th className="py-3 px-4 text-right">
                  {lang === 'ru' ? 'Расход' : 'Airflow'}
                </th>
                <th className="py-3 px-4 text-right">
                  {lang === 'ru' ? 'Температура' : 'Temp Range'}
                </th>
                <th className="py-3 px-4 text-right">
                  {lang === 'ru' ? 'Скорости' : 'Fan Speeds'}
                </th>
                <th className="py-3 px-4">
                  {lang === 'ru' ? 'Охлаждение / Увлажнитель' : 'Cooler / Humidifier'}
                </th>
                <th className="py-3 px-4">
                  {lang === 'ru' ? 'Доп. активные сенсоры' : 'Extra Active Sensors'}
                </th>
                <th className="py-3 pl-4 text-right">
                  {lang === 'ru' ? 'Действие' : 'Action'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {presets.map((p) => {
                const isSelected = p.id === selectedModel;
                const extraSensors = p.enabledSensors.filter(
                  (k) =>
                    ![
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
                    ].includes(k)
                );

                return (
                  <tr
                    key={p.id}
                    className={isSelected ? 'bg-blue-50/50' : 'hover:bg-slate-50/80'}
                  >
                    <td className="py-3 pr-4 font-semibold text-slate-900">
                      Breezart {p.name}
                      <div className="text-xs font-normal text-slate-500">
                        {I18N_CATALOG[lang].models[p.id]}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-700">{p.id}</td>
                    <td className="py-3 px-4 text-xs text-slate-700">
                      {formatHeater(p.heaterType)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-xs tabular-nums text-slate-800">
                      {p.airflowM3h > 0 ? `${p.airflowM3h} m³/h` : 'Auto'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-xs tabular-nums text-slate-800">
                      {p.tempMin}..{p.tempMax} °C
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-xs tabular-nums text-slate-800">
                      {p.speedMin}..{p.speedMax}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-700">
                      <span>
                        {lang === 'ru' ? 'Охл:' : 'Cool:'} {p.hasCooler ? 'Да / Yes' : 'Нет / No'}
                      </span>
                      <span className="mx-1.5 text-slate-300">·</span>
                      <span>
                        {lang === 'ru' ? 'Увл:' : 'Humid:'}{' '}
                        {p.hasHumidifier ? 'Да / Yes' : 'Нет / No'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600">
                      {extraSensors.map((sKey) => translateEntity(sKey, lang)).join(' · ')}
                    </td>
                    <td className="py-3 pl-4 text-right">
                      <button
                        type="button"
                        onClick={() => onSelectModel(p.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-100 text-slate-800 hover:bg-slate-200'
                        }`}
                      >
                        {isSelected
                          ? lang === 'ru'
                            ? 'Активна'
                            : 'Active'
                          : lang === 'ru'
                            ? 'Выбрать'
                            : 'Select'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
