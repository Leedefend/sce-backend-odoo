#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ts = require('../../frontend/apps/web/node_modules/typescript');

const ROOT = path.resolve(__dirname, '..', '..');
const SOURCE = path.join(ROOT, 'frontend/apps/web/src/app/pageIdentity.ts');

function loadIdentityResolver() {
  const source = fs.readFileSync(SOURCE, 'utf8');
  const transpiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(transpiled, { module, exports: module.exports }, { filename: SOURCE });
  return module.exports;
}

function equal(actual, expected, label) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assert(value, label) {
  if (!value) throw new Error(label);
}

function main() {
  const { resolveProductPageIdentity, isTechnicalPageIdentity } = loadIdentityResolver();
  const resolve = resolveProductPageIdentity;

  equal(resolve({ kind: 'list', actionName: '我的付款申请', menuName: '付款申请', modelLabel: '付款申请单' }).title, '我的付款申请', 'action outranks menu and model');
  equal(resolve({ kind: 'list', menuName: '付款申请', modelLabel: '付款申请单' }).title, '付款申请', 'menu fallback');
  equal(resolve({ kind: 'list', modelLabel: '付款申请单' }).title, '付款申请单', 'model display name fallback');
  equal(resolve({ kind: 'detail', actionName: '付款申请', record: { display_name: 'FE-A-PR-001' } }).title, 'FE-A-PR-001', 'record display_name outranks action');
  equal(resolve({ kind: 'detail', actionName: '付款申请', record: { contract_no: 'FE-A-CONTRACT-001' }, primaryFieldNames: ['contract_no'] }).title, 'FE-A-CONTRACT-001', 'business primary field fallback');
  equal(resolve({ kind: 'detail', modelName: 'construction.contract' }).title, '记录详情', 'technical model never reaches detail fallback');
  equal(resolve({ kind: 'detail', actionName: '付款申请' }).title, '付款申请详情', 'detail action fallback');
  equal(resolve({ kind: 'create', actionName: '付款申请' }).title, '新建付款申请', 'create title');
  equal(resolve({ kind: 'edit', actionName: '付款申请', record: { display_name: 'FE-A-PR-001' } }).title, '编辑 FE-A-PR-001', 'edit title');
  equal(resolve({ kind: 'list', actionName: '付款申请', state: 'loading' }).title, '付款申请 · 加载中', 'loading title');
  equal(resolve({ kind: 'list', actionName: '付款申请', state: 'empty' }).title, '付款申请 · 暂无数据', 'empty title');
  equal(resolve({ kind: 'list', actionName: '付款申请', state: 'denied' }).title, '付款申请 · 无权访问', 'denied title');
  equal(resolve({ kind: 'detail', state: 'not-found' }).title, '记录不存在', 'not-found title');
  equal(resolve({ kind: 'detail', actionName: '付款申请', recordDisplayName: 'SECRET-PR-001', state: 'denied' }).title, '付款申请 · 无权访问', 'denied identity never leaks record name');
  equal(resolve({ kind: 'detail', actionName: '付款申请', recordDisplayName: 'STALE-PR-001', state: 'not-found' }).title, '记录不存在', 'not-found identity never retains stale record');
  equal(resolve({ kind: 'list', actionName: '业务动作' }).title, '业务列表', 'generic action rejected');
  equal(resolve({ kind: 'detail', recordDisplayName: 'payment.request #5' }).title, '记录详情', 'model id fallback rejected');
  equal(resolve({ kind: 'detail', actionName: '付款申请', record: { display_name: 'FE-A-PR-001' }, breadcrumbs: [
    { label: '资金管理', to: '/m/1' },
    { label: '付款申请', to: '/a/2' },
    { label: 'payment.request #5', to: '/r/payment.request/5' },
  ] }).breadcrumbs, [
    { label: '资金管理', to: '/m/1' },
    { label: '付款申请', to: '/a/2' },
    { label: 'FE-A-PR-001' },
  ], 'breadcrumb strips technical ids and keeps current record unlinked');
  assert(isTechnicalPageIdentity('construction.contract'), 'technical model detection');
  assert(isTechnicalPageIdentity('合同 #12'), 'hash id detection');
  assert(isTechnicalPageIdentity('undefined'), 'undefined detection');
  assert(!isTechnicalPageIdentity('FE-A-PR-001'), 'business identifier accepted');
  assert(resolve({ kind: 'list', actionName: '结算管理' }).documentTitle === '结算管理 - 智能施工企业管理平台', 'document title contract');

  console.log('[frontend_page_identity_smoke] PASS assertions=23');
}

main();
