/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  I18N_CATALOG,
  MODEL_PRESETS,
  Language,
  ModelPresetId,
  getModelPreset,
} from './domain/breezart';
import { SimulatorView } from './components/SimulatorView';
import { PresetsComparisonView } from './components/PresetsComparisonView';
import { ConstantsCatalogView } from './components/ConstantsCatalogView';
import { TranslationsAndCodeView } from './components/TranslationsAndCodeView';

type ActiveTab = 'simulator' | 'presets' | 'constants' | 'code';

export default function App() {
  const [lang, setLang] = useState<Language>('ru');
  const [activeTab, setActiveTab] = useState<ActiveTab>('simulator');
  const [selectedModel, setSelectedModel] = useState<ModelPresetId>('550_lux');

  const preset = getModelPreset(selectedModel);

  const navItems: Array<{ id: ActiveTab; label: { ru: string; en: string } }> = [
    { id: 'simulator', label: { ru: 'Симулятор HA', en: 'HA Simulator' } },
    { id: 'presets', label: { ru: 'Модели (Пресеты)', en: 'Model Presets' } },
    { id: 'constants', label: { ru: 'Константы', en: 'Constants' } },
    { id: 'code', label: { ru: 'Переводы и Код', en: 'Translations & Code' } },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* 3-Zone Top Bar Contract */}
      <header className="flex items-center justify-between gap-8 px-6 py-4 bg-white border-b border-slate-200">
        {/* Zone 1: Brand icon + wordmark */}
        <a
          href="#top"
          onClick={(e) => {
            e.preventDefault();
            setActiveTab('simulator');
          }}
          className="flex items-center gap-2.5 text-lg font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
        >
          <img
            src="/assets/aistudio/image_a4906a24.png"
            alt="Breezart"
            className="h-7 w-7 object-contain rounded"
          />
          <span>Breezart HA Integration</span>
        </a>

        {/* Zone 2: 4 concise single-line navigation links */}
        <nav
          aria-label={lang === 'ru' ? 'Основная навигация' : 'Main navigation'}
          className="flex items-center gap-6 text-sm font-medium text-slate-600 overflow-x-auto"
        >
          {navItems.map((item) => {
            const isCurrent = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTab(item.id)}
                className={`py-1 transition-colors whitespace-nowrap shrink-0 border-b-2 ${
                  isCurrent
                    ? 'border-slate-900 text-slate-900 font-semibold'
                    : 'border-transparent hover:text-slate-900'
                }`}
              >
                {item.label[lang]}
              </button>
            );
          })}
        </nav>

        {/* Zone 3: 1 primary action (Language Toggle RU / EN) */}
        <div className="flex items-center shrink-0">
          <button
            type="button"
            onClick={() => setLang((prev) => (prev === 'ru' ? 'en' : 'ru'))}
            aria-label={
              lang === 'ru'
                ? 'Switch interface and entity translations to English'
                : 'Переключить язык интерфейса и сущностей на русский'
            }
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 rounded-lg hover:bg-slate-800 transition-colors whitespace-nowrap shrink-0"
          >
            {lang === 'ru' ? 'Язык: Русский → EN' : 'Language: English → RU'}
          </button>
        </div>
      </header>

      {/* Workspace Context Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <img
              src="/assets/aistudio/image_a4906a24.png"
              alt="Breezart Integration Icon"
              className="h-11 w-11 object-contain rounded-lg border border-slate-200 bg-white p-1 shrink-0"
            />
            <div>
              <h1 className="text-xl font-bold text-slate-900">
                {lang === 'ru'
                  ? 'Интеграция вентиляции Breezart для Home Assistant (v1.2.3)'
                  : 'Breezart Ventilation Home Assistant Integration (v1.2.3)'}
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                <a
                  href="https://github.com/akmagcry-oss/breezart-ha"
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-slate-700 hover:underline"
                >
                  github.com/akmagcry-oss/breezart-ha
                </a>
              <span className="mx-2" aria-hidden="true">
                ·
              </span>
              <span>
                {lang === 'ru'
                  ? '1) Все константы в const.py'
                  : '1) All constants in const.py'}
              </span>
              <span className="mx-2" aria-hidden="true">
                ·
              </span>
              <span>
                {lang === 'ru'
                  ? '2) Преднастройки 400 Lux, 550 Lux, 550 Aqua, 700/1000/2000 Lux'
                  : '2) Presets for 400 Lux, 550 Lux, 550 Aqua, 700/1000/2000 Lux'}
              </span>
              <span className="mx-2" aria-hidden="true">
                ·
              </span>
                <span>
                  {lang === 'ru'
                    ? '3) Полная интернационализация RU / EN · 4) Modbus TCP (:502) + Native TCP (:1560) · 5) Push-уведомления на телефон'
                    : '3) Full RU / EN i18n · 4) Modbus TCP (:502) + Native TCP (:1560) · 5) Mobile Push Notifications'}
                </span>
              </p>
            </div>
          </div>

          {/* Quick Model Preset Switcher */}
          <div className="flex flex-wrap items-center gap-2">
            <label
              htmlFor="quick-preset-select"
              className="text-xs font-semibold text-slate-600 whitespace-nowrap"
            >
              {lang === 'ru' ? 'Активная модель:' : 'Active Model:'}
            </label>
            <select
              id="quick-preset-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as ModelPresetId)}
              className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-900 focus:border-blue-600 focus:outline-none"
            >
              {(Object.keys(MODEL_PRESETS) as ModelPresetId[]).map((mId) => (
                <option key={mId} value={mId}>
                  Breezart {MODEL_PRESETS[mId].name} ({MODEL_PRESETS[mId].tempMin}..
                  {MODEL_PRESETS[mId].tempMax}°C, 1..{MODEL_PRESETS[mId].speedMax})
                </option>
              ))}
            </select>

            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setLang('ru')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                  lang === 'ru'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                RU
              </button>
              <button
                type="button"
                onClick={() => setLang('en')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors whitespace-nowrap shrink-0 ${
                  lang === 'en'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                EN
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {activeTab === 'simulator' && (
          <SimulatorView
            lang={lang}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
          />
        )}
        {activeTab === 'presets' && (
          <PresetsComparisonView
            lang={lang}
            selectedModel={selectedModel}
            onSelectModel={(m) => {
              setSelectedModel(m);
              setActiveTab('simulator');
            }}
          />
        )}
        {activeTab === 'constants' && <ConstantsCatalogView lang={lang} />}
        {activeTab === 'code' && <TranslationsAndCodeView lang={lang} />}
      </main>

      {/* Quiet Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-4 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <span>
            Breezart Home Assistant Integration v1.2.3 · Modbus TCP (Port 502, JLV135 / JL204c7) & Native TCP (Port 1560) · Active Preset: Breezart {preset.name}
          </span>
          <a
            href="https://github.com/akmagcry-oss/breezart-ha"
            target="_blank"
            rel="noreferrer"
            className="hover:text-slate-900 hover:underline font-mono"
          >
            https://github.com/akmagcry-oss/breezart-ha
          </a>
        </div>
      </footer>
    </div>
  );
}
