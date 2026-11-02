import React, { useState } from 'react';
import {
  EXTRACTED_CONSTANTS_CATALOG,
  Language,
  ProtocolConstantEntry,
} from '../domain/breezart';
import { REPO_FILES } from '../domain/repoFiles';

interface ConstantsCatalogViewProps {
  lang: Language;
}

export const ConstantsCatalogView: React.FC<ConstantsCatalogViewProps> = ({ lang }) => {
  const [categoryFilter, setCategoryFilter] = useState<
    'all' | ProtocolConstantEntry['category']
  >('all');
  const [search, setSearch] = useState<string>('');

  const constFile = REPO_FILES.find((f) => f.filename === 'const.py')!;

  const filteredConstants = EXTRACTED_CONSTANTS_CATALOG.filter((item) => {
    if (categoryFilter !== 'all' && item.category !== categoryFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        item.name.toLowerCase().includes(q) ||
        String(item.value).toLowerCase().includes(q) ||
        item.description[lang].toLowerCase().includes(q) ||
        item.usedIn.some((u) => u.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <section className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">
              custom_components/breezart/const.py
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? 'Реестр вынесенных констант протокола и конфигурации'
                : 'Extracted Protocol & Configuration Constants Registry'}
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap items-center gap-1 bg-slate-100 p-1 rounded-lg">
              {(
                [
                  { id: 'all', label: lang === 'ru' ? 'Все' : 'All' },
                  { id: 'protocol', label: lang === 'ru' ? 'Протокол' : 'Protocol' },
                  { id: 'network', label: lang === 'ru' ? 'Сеть / Тайминги' : 'Network' },
                  { id: 'bitmask', label: lang === 'ru' ? 'Биты / Индексы' : 'Bitmasks' },
                  { id: 'modes', label: lang === 'ru' ? 'Режимы' : 'Modes' },
                  { id: 'thresholds', label: lang === 'ru' ? 'Пороги' : 'Thresholds' },
                  { id: 'keys', label: lang === 'ru' ? 'Ключи данных' : 'Data Keys' },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setCategoryFilter(tab.id)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                    categoryFilter === tab.id
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
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={lang === 'ru' ? 'Поиск константы...' : 'Search constant...'}
              aria-label={lang === 'ru' ? 'Поиск константы' : 'Search constant'}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-blue-600 focus:outline-none"
            />
          </div>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500">
                <th className="py-2.5 pr-4">
                  {lang === 'ru' ? 'Группа констант' : 'Constant Group'}
                </th>
                <th className="py-2.5 px-4">
                  {lang === 'ru' ? 'Значение' : 'Value'}
                </th>
                <th className="py-2.5 px-4">
                  {lang === 'ru' ? 'Назначение' : 'Purpose'}
                </th>
                <th className="py-2.5 pl-4">
                  {lang === 'ru' ? 'Используется в модулях' : 'Used In Modules'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredConstants.map((item) => (
                <tr key={item.name} className="hover:bg-slate-50/80">
                  <td className="py-3 pr-4 font-mono text-xs font-semibold text-slate-900">
                    {item.name}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-blue-700 tabular-nums">
                    {item.value}
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-700">
                    {item.description[lang]}
                  </td>
                  <td className="py-3 pl-4 font-mono text-xs text-slate-500">
                    {item.usedIn.join(' · ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <p className="text-xs font-mono text-slate-500">{constFile.path}</p>
            <h3 className="text-base font-bold text-slate-900 mt-0.5">
              {lang === 'ru'
                ? 'Полный исходный код custom_components/breezart/const.py'
                : 'Complete Source Code of custom_components/breezart/const.py'}
            </h3>
          </div>
        </div>
        <pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100 font-mono leading-relaxed">
          <code>{constFile.content}</code>
        </pre>
      </section>
    </div>
  );
};
