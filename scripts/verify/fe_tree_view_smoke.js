#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const MODEL = process.env.MVP_MODEL || 'project.project';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUIRE_GROUPED_ROWS = process.env.REQUIRE_GROUPED_ROWS === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-6', ts);

function log(msg) {
  console.log(`[fe_tree_view_smoke] ${msg}`);
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
      res.on('data', (chunk) => (data += chunk));
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

function pickColumns(contract) {
  const views = contract && typeof contract === 'object' ? contract.views : null;
  if (views && typeof views === 'object') {
    const tree = views.tree || views.list;
    if (tree && Array.isArray(tree.columns) && tree.columns.length) {
      return tree.columns;
    }
  }
  return [];
}

function pickGroupByField(contract) {
  const search = contract && typeof contract === 'object' ? contract.search : null;
  const rows = search && typeof search === 'object' && Array.isArray(search.group_by) ? search.group_by : [];
  for (const row of rows) {
    if (typeof row === 'string' && row.trim()) return row.trim();
    if (row && typeof row === 'object') {
      const field = String(row.field || '').trim();
      if (field) return field;
    }
  }
  return 'create_uid';
}

function unwrapIntentData(body) {
  const rootData = body && typeof body === 'object' ? body.data : null;
  if (rootData && typeof rootData === 'object' && rootData.data && typeof rootData.data === 'object') {
    return rootData.data;
  }
  if (rootData && typeof rootData === 'object') return rootData;
  return {};
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
    });
    try {
      assertIntentEnvelope(bootstrapResp, 'bootstrap', { allowMetaIntentAliases: ['session.bootstrap'] });
    } catch (_err) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status || 0}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    try {
      assertIntentEnvelope(loginResp, 'login');
    } catch (_err) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status || 0}`);
    }
    token = (loginResp.body.data || {}).token || '';
    if (!token) {
      throw new Error('login response missing token');
    }
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('ui.contract (tree view)');
  const contractPayload = { intent: 'ui.contract', params: { op: 'model', model: MODEL, view_type: 'tree' } };
  const contractResp = await requestJson(intentUrl, contractPayload, authHeader);
  writeJson(path.join(outDir, 'contract.log'), contractResp);
  assertIntentEnvelope(contractResp, 'ui.contract');

  const contract = unwrapIntentData(contractResp.body);
  const columns = pickColumns(contract);
  summary.push(`columns_count: ${columns.length}`);
  if (!columns.length) {
    writeSummary(summary);
    throw new Error('tree columns missing');
  }

  log('api.data.list (tree columns)');
  const listPayload = {
    intent: 'api.data',
    params: { op: 'list', model: MODEL, fields: columns, limit: 5 },
  };
  const listResp = await requestJson(intentUrl, listPayload, authHeader);
  writeJson(path.join(outDir, 'list.log'), listResp);
  assertIntentEnvelope(listResp, 'api.data');
  const listData = unwrapIntentData(listResp.body);
  const records = Array.isArray(listData.records) ? listData.records : [];
  if (!records.length) {
    throw new Error('list returned no records');
  }
  const first = records[0] || {};
  const missing = columns.filter((col) => !Object.prototype.hasOwnProperty.call(first, col));
  summary.push(`missing_columns: ${missing.length}`);
  if (missing.length) {
    summary.push(`missing_columns_list: ${missing.join(', ')}`);
    writeSummary(summary);
    throw new Error('record missing tree columns');
  }

  log('api.data.list (grouped rows)');
  const groupByField = pickGroupByField(contract);
  const groupedPayload = {
    intent: 'api.data',
    params: {
      op: 'list',
      model: MODEL,
      fields: columns,
      group_by: groupByField,
      group_sample_limit: 3,
      limit: 12,
      offset: 0,
    },
  };
  const groupedResp = await requestJson(intentUrl, groupedPayload, authHeader);
  writeJson(path.join(outDir, 'grouped.log'), groupedResp);
  assertIntentEnvelope(groupedResp, 'api.data');
  const groupedData = unwrapIntentData(groupedResp.body);
  const groupedRows = Array.isArray(groupedData.grouped_rows) ? groupedData.grouped_rows : [];
  const groupSummary = Array.isArray(groupedData.group_summary) ? groupedData.group_summary : [];
  summary.push(`group_by_field: ${groupByField}`);
  summary.push(`group_summary_count: ${groupSummary.length}`);
  summary.push(`grouped_rows_count: ${groupedRows.length}`);
  const hasGroupedPayload = Array.isArray(groupedData.group_summary) && Array.isArray(groupedData.grouped_rows);
  summary.push(`grouped_payload_present: ${hasGroupedPayload ? 'yes' : 'no'}`);
  if (!hasGroupedPayload && REQUIRE_GROUPED_ROWS) {
    writeSummary(summary);
    throw new Error('grouped response missing group_summary/grouped_rows (REQUIRE_GROUPED_ROWS=1)');
  }

  writeSummary(summary);
  log('PASS tree view mvp');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_tree_view_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
