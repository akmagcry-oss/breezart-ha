import React, { useState } from 'react';
import { I18N_CATALOG, Language } from '../domain/breezart';
import { REPO_FILES } from '../domain/repoFiles';

interface TranslationsAndCodeViewProps {
  lang: Language;
}

export const TranslationsAndCodeView: React.FC<TranslationsAndCodeViewProps> = ({
  lang,
}) => {
  const [selectedFileIndex, setSelectedFileIndex] = useState<number>(0);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);
  const [i18nSearch, setI18nSearch] = useState<string>('');

  const activeFile = REPO_FILES[selectedFileIndex] ?? REPO_FILES[0];

  const handleCopy = async (content: string, path: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedPath(path);
      setTimeout(() => setCopiedPath(null), 2000);
    } catch {
      setCopiedPath(path);
    }
  };

  const handleDownload = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename.replace(/\//g, '_');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Build flat comparison rows of all RU & EN keys
  const allTranslationRows: Array<{
    scope: string;
    key: string;
    ru: string;
    en: string;
  }> = [
    ...Object.keys(I18N_CATALOG.ru.entities).map((k) => ({
      scope: 'entity',
      key: k,
      ru: I18N_CATALOG.ru.entities[k],
      en: I18N_CATALOG.en.entities[k],
    })),
    ...Object.keys(I18N_CATALOG.ru.unit_state).map((k) => ({
      scope: 'state.unit_state',
      key: k,
      ru: I18N_CATALOG.ru.unit_state[k],
      en: I18N_CATALOG.en.unit_state[k],
    })),
    ...Object.keys(I18N_CATALOG.ru.mode).map((k) => ({
      scope: 'state.mode',
      key: k,
      ru: I18N_CATALOG.ru.mode[k],
      en: I18N_CATALOG.en.mode[k],
    })),
    ...Object.keys(I18N_CATALOG.ru.filter_status).map((k) => ({
      scope: 'state_attr.filter_status',
      key: k,
      ru: I18N_CATALOG.ru.filter_status[k as keyof typeof I18N_CATALOG.ru.filter_status],
      en: I18N_CATALOG.en.filter_status[k as keyof typeof I18N_CATALOG.en.filter_status],
    })),
    ...Object.keys(I18N_CATALOG.ru.models).map((k) => ({
      scope: 'selector.model',
      key: k,
      ru: I18N_CATALOG.ru.models[k as keyof typeof I18N_CATALOG.ru.models],
      en: I18N_CATALOG.en.models[k as keyof typeof I18N_CATALOG.en.models],
    })),
  ];

  const filteredTranslations = allTranslationRows.filter((row) => {
    if (!i18nSearch.trim()) return true;
    const q = i18nSearch.toLowerCase();
    return (
      row.key.toLowerCase().includes(q) ||
      row.ru.toLowerCase().includes(q) ||
      row.en.toLowerCase().includes(q) ||
      row.scope.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-8">
      {/* Refactored Repository File Explorer */}
      <section className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              custom_components/breezart/* ({REPO_FILES.length} files)
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? 'Исходный код доработанного проекта Breezart Home Assistant Integration'
                : 'Refactored Breezart Home Assistant Integration Source Files'}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleCopy(activeFile.content, activeFile.path)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors whitespace-nowrap shrink-0"
            >
              {copiedPath === activeFile.path
                ? lang === 'ru'
                  ? 'Скопировано!'
                  : 'Copied!'
                : lang === 'ru'
                  ? 'Копировать файл'
                  : 'Copy File'}
            </button>
            <button
              type="button"
              onClick={() => handleDownload(activeFile.filename, activeFile.content)}
              className="px-3 py-1.5 rounded-lg bg-slate-900 text-xs font-semibold text-white hover:bg-slate-800 transition-colors whitespace-nowrap shrink-0"
            >
              {lang === 'ru' ? `Скачать ${activeFile.filename}` : `Download ${activeFile.filename}`}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-5">
          {/* File list sidebar */}
          <div className="lg:col-span-4 space-y-1">
            {REPO_FILES.map((file, idx) => {
              const active = idx === selectedFileIndex;
              return (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => setSelectedFileIndex(idx)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-mono transition-colors flex items-center justify-between ${
                    active
                      ? 'bg-slate-900 text-white font-semibold'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <span className="truncate">{file.path}</span>
                  <span className="text-[11px] opacity-75 ml-2 shrink-0">
                    {file.content.split('\n').length}L
                  </span>
                </button>
              );
            })}
          </div>

          {/* Code & highlights viewer */}
          <div className="lg:col-span-8 flex flex-col">
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/70 mb-4">
              <p className="text-xs font-mono text-slate-500">{activeFile.path}</p>
              <p className="text-sm font-semibold text-slate-900 mt-1">
                {activeFile.summary[lang]}
              </p>
              <ul className="mt-2 space-y-1 text-xs text-slate-600 list-disc list-inside">
                {activeFile.highlights[lang].map((hl) => (
                  <li key={hl}>{hl}</li>
                ))}
              </ul>
            </div>

            <pre className="max-h-[460px] overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100 font-mono leading-relaxed">
              <code>{activeFile.content}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Bilingual RU / EN Translation Matrix */}
      <section className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              translations/ru.json ↔ translations/en.json ↔ strings.json
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? `Таблица интернационализации RU / EN (${filteredTranslations.length} ключей)`
                : `Bilingual RU / EN Internationalization Matrix (${filteredTranslations.length} keys)`}
            </h2>
          </div>

          <input
            type="search"
            value={i18nSearch}
            onChange={(e) => setI18nSearch(e.target.value)}
            placeholder={
              lang === 'ru' ? 'Поиск по ключу, RU или EN...' : 'Search key, RU, or EN text...'
            }
            aria-label={lang === 'ru' ? 'Поиск перевода' : 'Search translation'}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
          />
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500">
                <th className="py-2.5 pr-4">{lang === 'ru' ? 'Раздел' : 'Scope'}</th>
                <th className="py-2.5 px-4">translation_key</th>
                <th className="py-2.5 px-4">Русский (translations/ru.json)</th>
                <th className="py-2.5 pl-4">English (translations/en.json)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredTranslations.map((row) => (
                <tr key={`${row.scope}:${row.key}`} className="hover:bg-slate-50/80">
                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{row.scope}</td>
                  <td className="py-2.5 px-4 font-mono text-xs font-semibold text-slate-800">
                    {row.key}
                  </td>
                  <td className="py-2.5 px-4 text-xs text-slate-900">{row.ru}</td>
                  <td className="py-2.5 pl-4 text-xs text-slate-900">{row.en}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
