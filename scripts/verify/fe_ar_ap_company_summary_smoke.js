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
const MODEL = 'sc.ar.ap.company.summary';
const EXPECTED_SUMMARY_ROWS = 771;
const EXPECTED_RECEIVABLE_ROWS = 657;
const EXPECTED_NEGATIVE_BALANCE_ROWS = 37;

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'ar-ap-company-summary', ts);

const REQUIRED_COLUMNS = [
  'project_id',
  'partner_count',
  'income_contract_amount',
  'receivable_unpaid_amount',
  'payable_contract_amount',
  'payable_pricing_method_text',
  'tax_deduction_rate',
  'actual_available_balance',
];

const REQUIRED_LABELS = {
  project_id: '项目',
  partner_count: '往来单位数',
  income_contract_amount: '收入合同金额',
  receivable_unpaid_amount: '未收款',
  payable_contract_amount: '应付合同金额',
  payable_pricing_method_text: '计价方式',
  tax_deduction_rate: '抵扣比例',
  actual_available_balance: '实际可用余额',
};

const REQUIRED_HELP_SUBSTRINGS = {
  tax_deduction_rate: ['项目级指标', '不应跨项目简单平均'],
  actual_available_balance: ['项目级指标', '每个项目只展示一次'],
};

function log(message) {
  console.log(`[fe_ar_ap_company_summary_smoke] ${message}`);
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

async function list(intentUrl, authHeader, domain, file, order = 'project_id,id') {
  const resp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: MODEL,
        fields: REQUIRED_COLUMNS,
        domain,
        limit: 5,
        offset: 0,
        need_total: true,
        order,
      },
    },
    authHeader,
  );
  writeJson(path.join(outDir, file), resp);
  assertIntentEnvelope(resp, 'api.data');
  return unwrapIntentData(resp.body);
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
  const badHelp = Object.entries(REQUIRED_HELP_SUBSTRINGS).filter(([name, expectedParts]) => {
    const help = String((fields[name] || {}).help || '');
    return expectedParts.some((part) => !help.includes(part));
  });

  if (missingColumns.length) throw new Error(`missing columns: ${missingColumns.join(',')}`);
  if (missingFields.length) throw new Error(`missing field definitions: ${missingFields.join(',')}`);
  if (badLabels.length) throw new Error(`bad labels: ${badLabels.map(([name]) => name).join(',')}`);
  if (badHelp.length) throw new Error(`bad field help: ${badHelp.map(([name]) => name).join(',')}`);
  if (permissions.read !== true || permissions.write !== false || permissions.create !== false || permissions.unlink !== false) {
    throw new Error(`unexpected permissions: ${JSON.stringify(permissions)}`);
  }

  log('api.data all project summary rows');
  const allData = await list(intentUrl, authHeader, [], 'summary_rows.log');
  const allTotal = getTotal(allData);
  const allRecords = Array.isArray(allData.records) ? allData.records : [];
  if (allTotal !== EXPECTED_SUMMARY_ROWS) throw new Error(`summary row total mismatch: ${allTotal}`);
  if (!allRecords.length || allRecords.some((row) => !Array.isArray(row.project_id) && !row.project_id)) {
    throw new Error('summary sample missing project values');
  }

  log('api.data receivable rows');
  const receivableData = await list(
    intentUrl,
    authHeader,
    [['receivable_unpaid_amount', '!=', 0]],
    'receivable_rows.log',
    'receivable_unpaid_amount desc,id',
  );
  const receivableTotal = getTotal(receivableData);
  if (receivableTotal !== EXPECTED_RECEIVABLE_ROWS) throw new Error(`receivable row total mismatch: ${receivableTotal}`);

  log('api.data negative balance rows');
  const balanceData = await list(
    intentUrl,
    authHeader,
    [['actual_available_balance', '<', 0]],
    'negative_balance_rows.log',
    'actual_available_balance asc,id',
  );
  const negativeBalanceTotal = getTotal(balanceData);
  if (negativeBalanceTotal !== EXPECTED_NEGATIVE_BALANCE_ROWS) {
    throw new Error(`negative balance row total mismatch: ${negativeBalanceTotal}`);
  }

  writeSummary([
    `model: ${MODEL}`,
    `columns: ${columns.length}`,
    `required_columns: ${REQUIRED_COLUMNS.join(',')}`,
    `summary_rows: ${allTotal}`,
    `receivable_rows: ${receivableTotal}`,
    `negative_balance_rows: ${negativeBalanceTotal}`,
    `permissions: ${JSON.stringify(permissions)}`,
    'result: PASS',
  ]);
  log('PASS');
}

main().catch((err) => {
  writeJson(path.join(outDir, 'error.log'), { message: err.message, stack: err.stack });
  console.error(`[fe_ar_ap_company_summary_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
