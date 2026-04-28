#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || '123456';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const MODEL = 'sc.ar.ap.project.summary';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'ar-ap-project-summary', ts);

const REQUIRED_COLUMNS = [
  'project_id',
  'partner_name',
  'payable_pricing_method_text',
  'tax_deduction_rate',
  'actual_available_balance',
];

const REQUIRED_LABELS = {
  partner_name: '往来单位',
  payable_pricing_method_text: '计价方式',
  tax_deduction_rate: '抵扣比例',
  actual_available_balance: '实际可用余额',
};

function log(message) {
  console.log(`[fe_ar_ap_project_summary_smoke] ${message}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload);
    const opts = {
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    };
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(data || '{}');
        } catch (_err) {
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

function unwrapIntentData(body) {
  const rootData = body && typeof body === 'object' ? body.data : null;
  if (rootData && typeof rootData === 'object' && rootData.data && typeof rootData.data === 'object') {
    return rootData.data;
  }
  if (rootData && typeof rootData === 'object') return rootData;
  return {};
}

function getTotal(data) {
  if (Number.isFinite(Number(data.total_count))) return Number(data.total_count);
  if (Number.isFinite(Number(data.total))) return Number(data.total);
  return 0;
}

async function getToken(intentUrl) {
  if (AUTH_TOKEN) return AUTH_TOKEN;
  if (!DB_NAME) throw new Error('DB_NAME is required');
  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
    { 'X-Anonymous-Intent': '1' },
  );
  writeJson(path.join(outDir, 'login.log'), loginResp);
  assertIntentEnvelope(loginResp, 'login');
  const token = (loginResp.body.data || {}).token || '';
  if (!token) throw new Error('login response missing token');
  return token;
}

async function main() {
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const token = await getToken(intentUrl);
  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('load_view tree contract');
  const viewResp = await requestJson(
    intentUrl,
    { intent: 'load_view', params: { model: MODEL, view_type: 'tree' } },
    authHeader,
  );
  writeJson(path.join(outDir, 'load_view.log'), viewResp);
  assertIntentEnvelope(viewResp, 'load_view');

  const viewData = viewResp.body.data || {};
  const tree = ((viewData.views || {}).tree || {});
  const columns = Array.isArray(tree.columns) ? tree.columns : [];
  const fields = viewData.fields || {};
  const permissions = (viewData.head || {}).permissions || {};

  const missingColumns = REQUIRED_COLUMNS.filter((column) => !columns.includes(column));
  const missingFields = REQUIRED_COLUMNS.filter((column) => !fields[column]);
  const badLabels = Object.entries(REQUIRED_LABELS).filter(([name, expected]) => {
    return String((fields[name] || {}).string || '') !== expected;
  });

  if (missingColumns.length) throw new Error(`missing columns: ${missingColumns.join(',')}`);
  if (missingFields.length) throw new Error(`missing field definitions: ${missingFields.join(',')}`);
  if (badLabels.length) throw new Error(`bad labels: ${badLabels.map(([name]) => name).join(',')}`);
  if (permissions.read !== true || permissions.write !== false || permissions.create !== false || permissions.unlink !== false) {
    throw new Error(`unexpected permissions: ${JSON.stringify(permissions)}`);
  }

  const dataFields = [
    'project_id',
    'partner_name',
    'payable_pricing_method_text',
    'tax_deduction_rate',
    'actual_available_balance',
  ];

  log('api.data project balance rows');
  const balanceResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: MODEL,
        fields: dataFields,
        domain: [['partner_key', 'like', 'project_balance:%']],
        limit: 5,
        offset: 0,
        need_total: true,
        order: 'actual_available_balance desc,id',
      },
    },
    authHeader,
  );
  writeJson(path.join(outDir, 'project_balance_rows.log'), balanceResp);
  assertIntentEnvelope(balanceResp, 'api.data');
  const balanceData = unwrapIntentData(balanceResp.body);
  const balanceTotal = getTotal(balanceData);
  const balanceRecords = Array.isArray(balanceData.records) ? balanceData.records : [];
  if (balanceTotal !== 56) throw new Error(`project balance row total mismatch: ${balanceTotal}`);
  if (!balanceRecords.length || balanceRecords.some((row) => row.partner_name !== '项目级余额')) {
    throw new Error('project balance sample missing 项目级余额 rows');
  }

  log('api.data project tax rate rows');
  const rateResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: MODEL,
        fields: dataFields,
        domain: [['tax_deduction_rate', '!=', 0]],
        limit: 3,
        offset: 0,
        need_total: true,
        order: 'tax_deduction_rate desc,id',
      },
    },
    authHeader,
  );
  writeJson(path.join(outDir, 'tax_rate_rows.log'), rateResp);
  assertIntentEnvelope(rateResp, 'api.data');
  const rateData = unwrapIntentData(rateResp.body);
  const rateTotal = getTotal(rateData);
  const rateRecords = Array.isArray(rateData.records) ? rateData.records : [];
  if (rateTotal !== 7471) throw new Error(`tax rate row total mismatch: ${rateTotal}`);
  if (!rateRecords.length || rateRecords.some((row) => !(Number(row.tax_deduction_rate || 0) > 0))) {
    throw new Error('tax rate sample missing non-zero rows');
  }

  const summary = [
    `model: ${MODEL}`,
    `columns: ${columns.length}`,
    `required_columns: ${REQUIRED_COLUMNS.join(',')}`,
    `project_balance_rows: ${balanceTotal}`,
    `tax_rate_rows: ${rateTotal}`,
    `permissions: ${JSON.stringify(permissions)}`,
    'result: PASS',
  ];
  writeSummary(summary);
  log('PASS');
}

main().catch((err) => {
  writeJson(path.join(outDir, 'error.log'), { message: err.message, stack: err.stack });
  console.error(`[fe_ar_ap_project_summary_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
