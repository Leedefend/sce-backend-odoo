#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const APP_DIR = path.join(ROOT, 'frontend/apps/web/src/app');
const cache = new Map();

function loadTs(moduleName) {
  const sourcePath = path.join(APP_DIR, `${moduleName}.ts`);
  if (cache.has(sourcePath)) return cache.get(sourcePath).exports;
  const source = fs.readFileSync(sourcePath, 'utf8');
  const output = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const module = { exports: {} };
  cache.set(sourcePath, module);
  const localRequire = (request) => {
    if (request.startsWith('./')) return loadTs(request.slice(2));
    throw new Error(`unsupported lifecycle smoke import: ${request}`);
  };
  vm.runInNewContext(`(function(require,module,exports){${output}\n})`, {}, { filename: sourcePath })(localRequire, module, module.exports);
  return module.exports;
}

function equal(actual, expected, label) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function main() {
  const { createPageIdentityCoordinator } = loadTs('pageIdentityCoordinator');
  const coordinator = createPageIdentityCoordinator();

  equal(coordinator.begin('/a/1', { kind: 'list', actionName: '付款申请' }).title, '付款申请', 'list route begins identity');
  equal(coordinator.begin('/r/payment.request/1', { kind: 'detail', actionName: '付款申请', state: 'loading' }).title, '付款申请 · 加载中', 'direct detail refresh loading identity');
  equal(coordinator.publish('/r/payment.request/1', { kind: 'detail', actionName: '付款申请', recordDisplayName: 'FE-A-PR-001' }).title, 'FE-A-PR-001', 'async detail publication');
  equal(coordinator.publish('/r/payment.request/1', { kind: 'edit', actionName: '付款申请', recordDisplayName: 'FE-A-PR-001' }).title, '编辑 FE-A-PR-001', 'detail to edit lifecycle');
  equal(coordinator.begin('/r/payment.request/2', { kind: 'detail', actionName: '付款申请', state: 'loading' }).title, '付款申请 · 加载中', 'fast record switch begins clean identity');
  equal(coordinator.publish('/r/payment.request/1', { kind: 'detail', recordDisplayName: 'STALE-PR-001' }), null, 'stale record publication rejected');
  equal(coordinator.publish('/r/payment.request/2', { kind: 'detail', recordDisplayName: 'FE-A-PR-002' }).title, 'FE-A-PR-002', 'active record publication accepted');
  equal(coordinator.begin('/company-b/a/1', { kind: 'list', actionName: '付款申请' }).title, '付款申请', 'company switch begins route identity');
  equal(coordinator.publish('/r/payment.request/2', { kind: 'detail', recordDisplayName: 'FE-A-PR-002' }), null, 'company switch rejects old record publication');
  equal(coordinator.begin('/project-member', { fallbackTitle: '角色首页' }).title, '角色首页', 'role switch replaces finance identity');
  equal(coordinator.clear().title, '工作台', 'logout clears business identity');
  equal(coordinator.currentKey(), '', 'logout clears active route key');

  console.log('[frontend_page_identity_lifecycle_smoke] PASS assertions=12');
}

main();
