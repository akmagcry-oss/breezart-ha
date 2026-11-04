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

test('model presets provide distinct capabilities and JLV135-compatible 10-speed / 5..35°C defaults', () => {
  const p400 = getModelPreset('400_lux');
  assert.equal(p400.name, '400 Lux');
  assert.equal(p400.heaterType, 'electric');
  assert.equal(p400.tempMin, 5);
  assert.equal(p400.tempMax, 35);
  assert.equal(p400.speedMax, 10);
  assert.equal(p400.hasWaterHeater, false);
  assert.equal(p400.enabledSensors.includes('power_consumption'), true);
  assert.equal(p400.enabledSensors.includes('temp_water'), false);

  const p550Lux = getModelPreset('550_lux');
  assert.equal(p550Lux.name, '550 Lux');
  assert.equal(p550Lux.airflowM3h, 550);
  assert.equal(p550Lux.heaterType, 'electric');
  assert.equal(p550Lux.tempMin, 5);
  assert.equal(p550Lux.tempMax, 35);
  assert.equal(p550Lux.speedMax, 10);

  const p550Aqua = getModelPreset('550_aqua');
  assert.equal(p550Aqua.name, '550 Aqua');
  assert.equal(p550Aqua.heaterType, 'water');
  assert.equal(p550Aqua.tempMin, 5);
  assert.equal(p550Aqua.tempMax, 35);
  assert.equal(p550Aqua.speedMax, 10);
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

test('repository metadata, GitHub URLs, BLOG_ARTICLE removal, and version 1.2.3 bump with date-free CHANGELOG history', () => {
  const rootDir = process.cwd();

  // 1) BLOG_ARTICLE.md must be deleted
  assert.equal(
    fs.existsSync(path.join(rootDir, 'BLOG_ARTICLE.md')),
    false,
    'BLOG_ARTICLE.md should be removed'
  );

  // 2) manifest.json and package.json must have version 1.2.3 and akmagcry-oss/breezart-ha links
  const manifest = JSON.parse(
    fs.readFileSync(path.join(rootDir, 'custom_components/breezart/manifest.json'), 'utf8')
  );
  assert.equal(manifest.version, '1.2.3');
  assert.equal(manifest.documentation, 'https://github.com/akmagcry-oss/breezart-ha');
  assert.equal(manifest.issue_tracker, 'https://github.com/akmagcry-oss/breezart-ha/issues');
  assert.deepEqual(manifest.codeowners, ['@akmagcry-oss']);

  const pkg = JSON.parse(fs.readFileSync(path.join(rootDir, 'package.json'), 'utf8'));
  assert.equal(pkg.version, '1.2.3');

  // 3) CHANGELOG.md must contain [1.2.3], [1.2.2], [1.2.1], [1.2.0], [1.1.2], [1.1.1], [1.1.0], and [1.0.0] in descending order without release dates
  const changelog = fs.readFileSync(path.join(rootDir, 'CHANGELOG.md'), 'utf8');
  assert.equal(changelog.includes('## [1.2.3]'), true);
  assert.equal(changelog.includes('## [1.2.2]'), true);
  assert.equal(changelog.includes('## [1.2.1]'), true);
  assert.equal(changelog.includes('## [1.2.0]'), true);
  assert.equal(changelog.includes('## [1.1.2]'), true);
  assert.equal(changelog.includes('## [1.1.1]'), true);
  assert.equal(changelog.includes('## [1.1.0]'), true);
  assert.equal(changelog.includes('## [1.0.0]'), true);
  assert.equal(
    /^## \[\d+\.\d+\.\d+\] -/m.test(changelog),
    false,
    'CHANGELOG.md version headers must not contain release dates'
  );
  assert.equal(
    changelog.indexOf('## [1.2.3]') < changelog.indexOf('## [1.2.2]'),
    true,
    '[1.2.3] should appear before [1.2.2] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.2.2]') < changelog.indexOf('## [1.2.1]'),
    true,
    '[1.2.2] should appear before [1.2.1] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.2.1]') < changelog.indexOf('## [1.2.0]'),
    true,
    '[1.2.1] should appear before [1.2.0] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.2.0]') < changelog.indexOf('## [1.1.2]'),
    true,
    '[1.2.0] should appear before [1.1.2] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.1.2]') < changelog.indexOf('## [1.1.1]'),
    true,
    '[1.1.2] should appear before [1.1.1] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.1.1]') < changelog.indexOf('## [1.1.0]'),
    true,
    '[1.1.1] should appear before [1.1.0] in CHANGELOG.md'
  );
  assert.equal(
    changelog.indexOf('## [1.1.0]') < changelog.indexOf('## [1.0.0]'),
    true,
    '[1.1.0] should appear before [1.0.0] in CHANGELOG.md'
  );

  const readme = fs.readFileSync(path.join(rootDir, 'README.md'), 'utf8');
  assert.equal(readme.includes('https://github.com/akmagcry-oss/breezart-ha'), true);
  assert.equal(readme.includes('smirnowegor/Breezart-Home-Assistant-Integration'), false);

  // 4) CONFIG_FLOW_VERSION must remain 1
  assert.equal(BREEZART_CONSTANTS.CONFIG_FLOW_VERSION, 1);
  const constPy = fs.readFileSync(
    path.join(rootDir, 'custom_components/breezart/const.py'),
    'utf8'
  );
  assert.equal(constPy.includes('CONFIG_FLOW_VERSION: Final[int] = 1'), true);

  // 5) Custom integration icon & logo files must exist and match the uploaded Breezart icon
  const sourceIcon = fs.readFileSync(
    path.join(rootDir, 'public/assets/aistudio/image_a4906a24.png')
  );
  for (const relIconPath of [
    'custom_components/breezart/icon.png',
    'custom_components/breezart/icon@2x.png',
    'custom_components/breezart/logo.png',
    'custom_components/breezart/logo@2x.png',
    'custom_components/breezart/brand/icon.png',
    'custom_components/breezart/brand/icon@2x.png',
    'custom_components/breezart/brand/logo.png',
    'custom_components/breezart/brand/logo@2x.png',
    'assets/breezart.png',
  ]) {
    const fullPath = path.join(rootDir, relIconPath);
    assert.equal(fs.existsSync(fullPath), true, `${relIconPath} must exist`);
    assert.equal(
      fs.readFileSync(fullPath).equals(sourceIcon),
      true,
      `${relIconPath} must match uploaded Breezart icon`
    );
  }

  // 6) README cleanup & separated documentation in docs/
  for (const docRelPath of [
    'docs/README.md',
    'docs/sensors.md',
    'docs/protocols.md',
    'docs/structure.md',
  ]) {
    const docFullPath = path.join(rootDir, docRelPath);
    assert.equal(fs.existsSync(docFullPath), true, `${docRelPath} must exist`);
  }

  const docsSensors = fs.readFileSync(path.join(rootDir, 'docs/sensors.md'), 'utf8');
  assert.equal(docsSensors.includes('Отличное / Excellent'), true);
  assert.equal(docsSensors.includes('switch.breezart_notify_overheat'), true);

  const docsProtocols = fs.readFileSync(path.join(rootDir, 'docs/protocols.md'), 'utf8');
  assert.equal(docsProtocols.includes('HOLDING[0]'), true);
  assert.equal(docsProtocols.includes('VPr07'), true);

  const docsStructure = fs.readFileSync(path.join(rootDir, 'docs/structure.md'), 'utf8');
  assert.equal(docsStructure.includes('custom_components/breezart/'), true);

  // README must NOT have logo image, HACS creating-links note, or duplicated Особенности/Возможности
  assert.equal(readme.includes('![Breezart]'), false, 'Breezart logo must be removed from README.md');
  assert.equal(
    readme.includes('Если нужно подробнее про формир'),
    false,
    'HACS link formation note must be removed from README.md'
  );
  assert.equal(readme.includes('Особенности'), false, 'Особенности must be merged into Возможности');
  assert.equal(
    readme.includes('custom_components/breezart/\n├──'),
    false,
    'Project structure block must be moved out of README.md into docs/'
  );
  assert.equal(
    readme.includes('HOLDING[0]'),
    false,
    'Protocols block must be moved out of README.md into docs/'
  );

  // Official links to Breezart and Home Assistant in description
  assert.equal(readme.includes('https://breezart.ru'), true, 'README must link to official Breezart site');
  assert.equal(
    readme.includes('https://www.home-assistant.io'),
    true,
    'README must link to official Home Assistant site'
  );
  assert.equal(
    readme.toLowerCase().includes('неофициальная интеграция'),
    true,
    'README must state that this is an unofficial integration'
  );

  // Exact section order: 1) Title/Description -> 2) Возможности -> 3) Совместимость -> 4) Установка и настройка -> 5) Документация
  const idxFeatures = readme.indexOf('## Возможности');
  const idxCompat = readme.indexOf('## Совместимость');
  const idxInstall = readme.indexOf('## Установка и настройка');
  const idxDocs = readme.indexOf('## Документация');
  assert.equal(idxFeatures > 0, true, 'README must have ## Возможности');
  assert.equal(idxCompat > idxFeatures, true, '## Совместимость must follow ## Возможности');
  assert.equal(idxInstall > idxCompat, true, '## Установка и настройка must follow ## Совместимость');
  assert.equal(idxDocs > idxInstall, true, '## Документация must be at the end after ## Установка и настройка');
  assert.equal(readme.includes('docs/'), true, 'README must link to docs/');
});

test('Modbus TCP (JLV135 + JL204c7 v1.7.14) MBAP framing, register scaling, freeze hazard detection, and 7 individual notification switches with deduplication & throttle (v1.2.1)', async () => {
  const mod = await import('./breezart');
  assert.equal(typeof mod.buildModbusReadFrameHex, 'function');
  assert.equal(typeof mod.buildModbusWriteSingleFrameHex, 'function');
  assert.equal(typeof mod.scaleSpeedToModbusPercent100, 'function');
  assert.equal(typeof mod.scaleModbusPercent100ToSpeed, 'function');
  assert.equal(typeof mod.mapCmdModeToModbusHc, 'function');
  assert.equal(typeof mod.mapModbusHcToCmdMode, 'function');
  assert.equal(typeof mod.detectFreezeHazard, 'function');
  assert.equal(typeof mod.resolveNotifyTargets, 'function');
  assert.equal(typeof mod.shouldSendThrottledNotification, 'function');

  // 1) Notification target deduplication:
  // When notify_service is "notify.notify" and HA has ["notify", "mobile_app_iphone"],
  // it MUST return ONLY ["mobile_app_iphone"] so notify.notify doesn't send a 2nd duplicate push!
  assert.deepEqual(
    mod.resolveNotifyTargets('notify.notify', ['notify', 'mobile_app_iphone']),
    ['mobile_app_iphone']
  );
  // When no mobile_app_* exists, fallback to ["notify"]
  assert.deepEqual(
    mod.resolveNotifyTargets('notify.notify', ['notify', 'persistent_notification']),
    ['notify']
  );
  // When user explicitly specifies custom services including notify.notify + mobile_app_*, drop notify
  assert.deepEqual(
    mod.resolveNotifyTargets('notify.notify, notify.mobile_app_iphone, notify.telegram', [
      'notify',
      'mobile_app_iphone',
      'telegram',
    ]),
    ['mobile_app_iphone', 'telegram']
  );

  // 2) Per-event throttle/cooldown helper:
  const lastSent: Record<string, number> = {};
  // First event at t=100s -> allowed (true)
  assert.equal(mod.shouldSendThrottledNotification('offline', 100, lastSent, 30), true);
  // Duplicate event 4s later at t=104s -> suppressed (false)
  assert.equal(mod.shouldSendThrottledNotification('offline', 104, lastSent, 30), false);
  // Different event ('online') at t=106s -> allowed (true)
  assert.equal(mod.shouldSendThrottledNotification('online', 106, lastSent, 30), true);
  // Duplicate 'online' 2s later at t=108s -> suppressed (false)
  assert.equal(mod.shouldSendThrottledNotification('online', 108, lastSent, 30), false);
  // Same event after cooldown expires at t=135s -> allowed (true)
  assert.equal(mod.shouldSendThrottledNotification('offline', 135, lastSent, 30), true);

  // Read Holding Registers (FC 0x03) start=0, count=9, unitId=1, txId=1:
  assert.equal(
    mod.buildModbusReadFrameHex(0x03, 0, 9, 1, 1),
    '00 01 00 00 00 06 01 03 00 00 00 09'
  );

  // Translations for danger_freeze and all 7 notification switches
  assert.equal(translateEntity('danger_freeze', 'ru'), 'Угроза обморожения');
  assert.equal(translateEntity('danger_freeze', 'en'), 'Freeze hazard');
  assert.equal(mod.NOTIFICATION_SETTING_KEYS.length, 7);

  const rootDir = process.cwd();
  const constPy = fs.readFileSync(
    path.join(rootDir, 'custom_components/breezart/const.py'),
    'utf8'
  );
  assert.equal(constPy.includes('NOTIFY_COOLDOWN_SECONDS'), true);
  assert.equal(constPy.includes('NOTIFY_OFFLINE_FAILURE_THRESHOLD'), true);

  const coordinatorPy = fs.readFileSync(
    path.join(rootDir, 'custom_components/breezart/coordinator.py'),
    'utf8'
  );
  assert.equal(coordinatorPy.includes('_resolve_notify_targets'), true);
  assert.equal(coordinatorPy.includes('_consecutive_failures'), true);
  assert.equal(coordinatorPy.includes('_last_notification_time'), true);
});




