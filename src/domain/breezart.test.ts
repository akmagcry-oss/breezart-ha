import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {
  BREEZART_CONSTANTS,
  MODEL_PRESETS,
  I18N_CATALOG,
  getModelPreset,
  decToHex,
  hexToDec,
  hexToDecSign,
  parseBits,
  buildProtocolRequest,
  classifyFilterPollution,
  resolveHvacMode,
  resolveHvacAction,
  translateEntity,
  translateState,
} from './breezart';

test('model presets provide distinct capabilities for 400_lux, 550_lux, 550_aqua, 1000_lux', () => {
  const p400 = getModelPreset('400_lux');
  assert.equal(p400.name, '400 Lux');
  assert.equal(p400.heaterType, 'electric');
  assert.equal(p400.tempMin, 10);
  assert.equal(p400.speedMax, 8);
  assert.equal(p400.hasWaterHeater, false);
  assert.equal(p400.enabledSensors.includes('power_consumption'), true);
  assert.equal(p400.enabledSensors.includes('temp_water'), false);

  const p550Lux = getModelPreset('550_lux');
  assert.equal(p550Lux.name, '550 Lux');
  assert.equal(p550Lux.airflowM3h, 550);
  assert.equal(p550Lux.heaterType, 'electric');

  const p550Aqua = getModelPreset('550_aqua');
  assert.equal(p550Aqua.name, '550 Aqua');
  assert.equal(p550Aqua.heaterType, 'water');
  assert.equal(p550Aqua.tempMin, 15);
  assert.equal(p550Aqua.hasHumidifier, true);
  assert.equal(p550Aqua.enabledSensors.includes('temp_water'), true);
  assert.equal(p550Aqua.enabledSensors.includes('humidity'), true);

  const p1000Lux = getModelPreset('1000_lux');
  assert.equal(p1000Lux.speedMax, 10);
  assert.equal(p1000Lux.hasCooler, true);

  // Unknown model falls back to 550_lux
  const fallback = getModelPreset('unknown_model');
  assert.equal(fallback.id, '550_lux');
});

test('protocol bit and hex helpers match Breezart TCP specification', () => {
  assert.equal(decToHex(21579), '544b');
  assert.equal(hexToDec('544b'), 21579);
  assert.equal(hexToDecSign('ffce'), -50); // -5.0°C when divided by 10
  assert.equal(hexToDecSign('00dc'), 220); // +22.0°C when divided by 10

  // VPr07 bitTempr: low byte = 10 (0x0a), high byte = 30 (0x1e) -> 0x1e0a
  assert.equal(parseBits('1e0a', 0, 7), 10);
  assert.equal(parseBits('1e0a', 8, 15), 30);

  assert.equal(buildProtocolRequest('VPr07', 21579), 'VPr07_544b');
  assert.equal(buildProtocolRequest('VWTmp', 21579, 22), 'VWTmp_544b_16');
});

test('filter pollution classification and bilingual status translation', () => {
  assert.equal(classifyFilterPollution(null), 'no_data');
  assert.equal(classifyFilterPollution(18), 'excellent');
  assert.equal(classifyFilterPollution(45), 'good');
  assert.equal(classifyFilterPollution(72), 'replace_soon');
  assert.equal(classifyFilterPollution(91), 'clogged');

  assert.equal(translateState('filter_status', 'excellent', 'ru'), 'Отличное');
  assert.equal(translateState('filter_status', 'excellent', 'en'), 'Excellent');
  assert.equal(translateState('filter_status', 'replace_soon', 'ru'), 'Требуется замена');
  assert.equal(translateState('filter_status', 'replace_soon', 'en'), 'Replace soon');
});

test('HVAC mode and action resolution uses protocol numeric constants', () => {
  assert.equal(resolveHvacMode(false, BREEZART_CONSTANTS.MODE_HEAT), 'off');
  assert.equal(resolveHvacMode(true, BREEZART_CONSTANTS.MODE_HEAT), 'heat');
  assert.equal(resolveHvacMode(true, BREEZART_CONSTANTS.MODE_COOL), 'cool');
  assert.equal(resolveHvacMode(true, BREEZART_CONSTANTS.MODE_AUTO_HEAT), 'auto');
  assert.equal(resolveHvacMode(true, BREEZART_CONSTANTS.MODE_VENT), 'fan_only');

  assert.equal(
    resolveHvacAction(true, BREEZART_CONSTANTS.UNIT_STATE_ON, BREEZART_CONSTANTS.MODE_HEAT),
    'heating'
  );
  assert.equal(
    resolveHvacAction(true, BREEZART_CONSTANTS.UNIT_STATE_ON, BREEZART_CONSTANTS.MODE_COOL),
    'cooling'
  );
  assert.equal(
    resolveHvacAction(true, BREEZART_CONSTANTS.UNIT_STATE_STARTUP, BREEZART_CONSTANTS.MODE_HEAT),
    'idle'
  );
});

test('all entity translation keys exist in both Russian and English catalogs and HA JSON files', () => {
  const ruEntities = Object.keys(I18N_CATALOG.ru.entities);
  const enEntities = Object.keys(I18N_CATALOG.en.entities);
  assert.deepEqual(ruEntities, enEntities);

  for (const key of ruEntities) {
    assert.ok(translateEntity(key, 'ru').length > 0, `Missing RU translation for ${key}`);
    assert.ok(translateEntity(key, 'en').length > 0, `Missing EN translation for ${key}`);
  }

  // Verify custom_components/breezart JSON files are valid and aligned
  const rootDir = process.cwd();
  const stringsJson = JSON.parse(
    fs.readFileSync(path.join(rootDir, 'custom_components/breezart/strings.json'), 'utf8')
  );
  const enJson = JSON.parse(
    fs.readFileSync(path.join(rootDir, 'custom_components/breezart/translations/en.json'), 'utf8')
  );
  const ruJson = JSON.parse(
    fs.readFileSync(path.join(rootDir, 'custom_components/breezart/translations/ru.json'), 'utf8')
  );

  assert.deepEqual(Object.keys(stringsJson.entity.sensor), Object.keys(enJson.entity.sensor));
  assert.deepEqual(Object.keys(enJson.entity.sensor), Object.keys(ruJson.entity.sensor));
  assert.deepEqual(
    Object.keys(enJson.selector.model.options),
    Object.keys(ruJson.selector.model.options)
  );
  assert.equal(Object.keys(enJson.selector.model.options).length, Object.keys(MODEL_PRESETS).length);

  // Verify no hardcoded _attr_name remains in Python entity files
  for (const pyFile of ['climate.py', 'sensor.py', 'binary_sensor.py', 'number.py', 'switch.py']) {
    const content = fs.readFileSync(
      path.join(rootDir, 'custom_components/breezart', pyFile),
      'utf8'
    );
    assert.equal(
      content.includes('_attr_name'),
      false,
      `${pyFile} should use _attr_translation_key instead of hardcoded _attr_name`
    );
    assert.equal(
      content.includes('_attr_translation_key'),
      true,
      `${pyFile} must define _attr_translation_key`
    );
  }
});

test('repository metadata, GitHub URLs, BLOG_ARTICLE removal, and version 1.0.0 reset', () => {
  const rootDir = process.cwd();

  // 1) BLOG_ARTICLE.md must be deleted
  assert.equal(
    fs.existsSync(path.join(rootDir, 'BLOG_ARTICLE.md')),
    false,
    'BLOG_ARTICLE.md should be removed'
  );

  // 2) manifest.json must have version 1.0.0 and akmagcry-oss/breezart-ha links
  const manifest = JSON.parse(
    fs.readFileSync(path.join(rootDir, 'custom_components/breezart/manifest.json'), 'utf8')
  );
  assert.equal(manifest.version, '1.0.0');
  assert.equal(manifest.documentation, 'https://github.com/akmagcry-oss/breezart-ha');
  assert.equal(manifest.issue_tracker, 'https://github.com/akmagcry-oss/breezart-ha/issues');
  assert.deepEqual(manifest.codeowners, ['@akmagcry-oss']);

  // 3) CHANGELOG.md and README.md must reflect 1.0.0 as initial release and use new GitHub URL
  const changelog = fs.readFileSync(path.join(rootDir, 'CHANGELOG.md'), 'utf8');
  assert.equal(changelog.includes('1.0.0'), true);
  assert.equal(changelog.includes('1.1.0'), false);
  assert.equal(changelog.includes('1.2.0'), false);

  const readme = fs.readFileSync(path.join(rootDir, 'README.md'), 'utf8');
  assert.equal(readme.includes('https://github.com/akmagcry-oss/breezart-ha'), true);
  assert.equal(readme.includes('smirnowegor/Breezart-Home-Assistant-Integration'), false);
  assert.equal(readme.includes('1.1.0'), false);
  assert.equal(readme.includes('1.2.0'), false);

  // 4) CONFIG_FLOW_VERSION must be 1
  assert.equal(BREEZART_CONSTANTS.CONFIG_FLOW_VERSION, 1);
  const constPy = fs.readFileSync(
    path.join(rootDir, 'custom_components/breezart/const.py'),
    'utf8'
  );
  assert.equal(constPy.includes('CONFIG_FLOW_VERSION: Final[int] = 1'), true);
});

