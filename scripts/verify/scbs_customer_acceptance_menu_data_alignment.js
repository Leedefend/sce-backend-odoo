#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.FRONTEND_URL || process.env.BASE_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(process.cwd(), 'artifacts');
const OUTPUT = path.join(ARTIFACTS_DIR, 'migration', 'scbs_customer_acceptance_menu_data_alignment_v1.json');
const OUTPUT_MD = path.join(ARTIFACTS_DIR, 'migration', 'scbs_customer_acceptance_menu_data_alignment_v1.md');

const EXPECTED_GROUPS = new Set(['旧业务数据核对', '直营项目数据核对']);
const FORBIDDEN_LABELS = new Set([
  '基础设置',
  '项目中心',
  '合同中心',
  '物资与分包',
  '财务中心',
  '采购',
  '客户',
  '供应商',
  '智慧大屏',
]);

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const body = JSON.stringify(payload);
    const transport = target.protocol === 'https:' ? https : http;
    const req = transport.request({
      method: 'POST',
      hostname: target.hostname,
      port: target.port || (target.protocol === 'https:' ? 443 : 80),
      path: `${target.pathname}${target.search}`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(data || '{}');
        } catch {
          parsed = { raw: data };
        }
        resolve({ status: res.statusCode || 0, body: parsed });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function okEnvelope(resp) {
  return resp.status >= 200 && resp.status < 300 && resp.body && resp.body.ok !== false;
}

async function intent(token, intentName, params = {}, anonymous = false) {
  const headers = { 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': `scbs-menu-data-${Date.now()}` };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (anonymous) headers['X-Anonymous-Intent'] = 'true';
  const resp = await requestJson(
    `${BASE_URL.replace(/\/$/, '')}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`,
    { intent: intentName, params },
    headers,
  );
  if (!okEnvelope(resp)) {
    throw new Error(`${intentName} failed: ${JSON.stringify(resp.body && (resp.body.error || resp.body))}`);
  }
  return resp.body.data || {};
}

function flattenNav(nodes, ancestors = [], out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== 'object') continue;
    const label = normalize(node.label || node.title || node.name);
    const pathLabels = [...ancestors, label].filter(Boolean);
    const children = Array.isArray(node.children) ? node.children : [];
    if (children.length) {
      flattenNav(children, pathLabels, out);
      continue;
    }
    const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
    const actionId = Number(meta.action_id || node.action_id || 0);
    const model = normalize(meta.model || node.model);
    if (!actionId || !model) continue;
    out.push({
      label,
      path: pathLabels.join(' / '),
      menu_id: Number(meta.menu_id || node.menu_id || 0),
      menu_xmlid: normalize(meta.menu_xmlid || node.menu_xmlid),
      action_id: actionId,
      model,
      route: normalize(meta.route || node.route),
    });
  }
  return out;
}

function topGroups(nav) {
  const root = Array.isArray(nav) && nav[0] && typeof nav[0] === 'object' ? nav[0] : {};
  return (Array.isArray(root.children) ? root.children : [])
    .map((node) => normalize(node.label || node.title || node.name))
    .filter(Boolean);
}

function collectLabels(nodes, out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== 'object') continue;
    const label = normalize(node.label || node.title || node.name);
    if (label) out.push(label);
    collectLabels(node.children, out);
  }
  return out;
}

function dataFields(contract) {
  const tree = (((contract.views || {}).tree) || {});
  const schema = Array.isArray(tree.columns_schema) ? tree.columns_schema : [];
  const names = schema.map((row) => normalize(row && row.name)).filter(Boolean);
  const fields = ['id'];
  for (const name of names) {
    if (!fields.includes(name)) fields.push(name);
    if (fields.length >= 8) break;
  }
  if (fields.length === 1) fields.push('display_name');
  return fields;
}

async function validateLeaf(token, leaf) {
  const contract = await intent(token, 'ui.contract', {
    op: 'action_open',
    action_id: leaf.action_id,
  });
  const head = contract.head && typeof contract.head === 'object' ? contract.head : {};
  const model = normalize(head.model || leaf.model);
  const data = await intent(token, 'api.data', {
    op: 'list',
    model,
    domain: Array.isArray(head.domain) ? head.domain : [],
    domain_raw: normalize(head.domain_raw),
    context_raw: normalize(head.context_raw),
    fields: dataFields(contract),
    limit: 1,
    need_total: true,
  });
  const records = Array.isArray(data.records) ? data.records : [];
  return {
    ...leaf,
    contract_model: model,
    contract_title: normalize(head.title),
    total: Number(data.total || 0),
    first_record_id: records[0] ? Number(records[0].id || 0) : 0,
    domain_raw: normalize(head.domain_raw),
    context_raw: normalize(head.context_raw),
  };
}

async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  let index = 0;
  async function worker() {
    while (index < items.length) {
      const current = index;
      index += 1;
      try {
        out[current] = await fn(items[current], current);
      } catch (error) {
        out[current] = { ...items[current], error: error && error.message ? error.message : String(error) };
      }
    }
  }
  await Promise.all(Array.from({ length: Math.max(1, Math.min(limit, items.length)) }, worker));
  return out;
}

function writeReport(report) {
  ensureDir(OUTPUT);
  fs.writeFileSync(OUTPUT, JSON.stringify(report, null, 2) + '\n', 'utf8');
  const lines = [
    '# SCBS Customer Acceptance Menu Data Alignment',
    '',
    `- ok: ${report.ok}`,
    `- base_url: ${report.base_url}`,
    `- db_name: ${report.db_name}`,
    `- login: ${report.login}`,
    `- menu_leaf_count: ${report.summary.menu_leaf_count}`,
    `- validated_count: ${report.summary.validated_count}`,
    `- zero_count: ${report.summary.zero_count}`,
    `- error_count: ${report.summary.error_count}`,
    `- forbidden_label_count: ${report.summary.forbidden_label_count}`,
    '',
    '| path | model | total | status |',
    '| --- | --- | ---: | --- |',
  ];
  for (const row of report.rows) {
    lines.push(`| ${row.path} | ${row.contract_model || row.model || ''} | ${row.total ?? ''} | ${row.error ? `ERROR: ${row.error}` : (row.total > 0 ? 'PASS' : 'ZERO')} |`);
  }
  fs.writeFileSync(OUTPUT_MD, lines.join('\n') + '\n', 'utf8');
}

(async function main() {
  const loginData = await intent('', 'login', { db: DB_NAME, login: LOGIN, password: PASSWORD }, true);
  const token = loginData.token || (loginData.session || {}).token;
  if (!token) throw new Error('login response missing token');
  const init = await intent(token, 'system.init', { contract_mode: 'user' });
  const nav = Array.isArray(init.nav) ? init.nav : [];
  const labels = collectLabels(nav);
  const forbiddenLabels = [...FORBIDDEN_LABELS].filter((label) => labels.includes(label));
  const groups = topGroups(nav);
  const unexpectedTopGroups = groups.filter((label) => !EXPECTED_GROUPS.has(label));
  const missingTopGroups = [...EXPECTED_GROUPS].filter((label) => !groups.includes(label));
  const leaves = flattenNav(nav);
  const rows = await mapLimit(leaves, Number(process.env.CONCURRENCY || 4), (leaf) => validateLeaf(token, leaf));
  rows.sort((a, b) => a.path.localeCompare(b.path, 'zh-Hans-CN'));
  const zeroRows = rows.filter((row) => !row.error && Number(row.total || 0) <= 0);
  const errorRows = rows.filter((row) => row.error);
  const report = {
    ok: !forbiddenLabels.length && !unexpectedTopGroups.length && !missingTopGroups.length && !zeroRows.length && !errorRows.length,
    base_url: BASE_URL,
    db_name: DB_NAME,
    login: LOGIN,
    summary: {
      top_groups: groups,
      missing_top_groups: missingTopGroups,
      unexpected_top_groups: unexpectedTopGroups,
      menu_leaf_count: leaves.length,
      validated_count: rows.length,
      zero_count: zeroRows.length,
      error_count: errorRows.length,
      forbidden_label_count: forbiddenLabels.length,
      forbidden_labels: forbiddenLabels,
    },
    rows,
    zero_rows: zeroRows,
    error_rows: errorRows,
  };
  writeReport(report);
  console.log(JSON.stringify(report.summary, null, 2));
  console.log(`SCBS_CUSTOMER_ACCEPTANCE_MENU_DATA_ALIGNMENT=${report.ok ? 'PASS' : 'FAIL'}`);
  if (!report.ok) process.exit(1);
}()).catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
