#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const MODEL = process.env.MVP_MODEL || 'project.project';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-6', ts);

function log(msg) {
  console.log(`[fe_kanban_view_smoke] ${msg}`);
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

function pickKanbanFields(contract) {
  const views = contract && typeof contract === 'object' ? contract.views : null;
  if (views && views.kanban && Array.isArray(views.kanban.fields) && views.kanban.fields.length) {
    return views.kanban.fields;
  }
  const fieldsMap = contract && typeof contract === 'object' ? contract.fields : null;
  if (fieldsMap && typeof fieldsMap === 'object') {
    const preferred = ['display_name', 'name', 'stage_id', 'user_id', 'partner_id', 'write_date'];
    const available = Object.keys(fieldsMap);
    const picked = preferred.filter((field) => available.includes(field));
    if (picked.length) return picked;
    return available.slice(0, 6);
  }
  return ['name', 'id'];
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
    if (bootstrapResp.status >= 400 || !bootstrapResp.body.ok) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    if (loginResp.status >= 400 || !loginResp.body.ok) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status}`);
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

  log('ui.contract (kanban view)');
  const contractPayload = { intent: 'ui.contract', params: { op: 'model', model: MODEL, view_type: 'kanban' } };
  const contractResp = await requestJson(intentUrl, contractPayload, authHeader);
  writeJson(path.join(outDir, 'contract.log'), contractResp);
  if (contractResp.status >= 400 || !contractResp.body.ok) {
    throw new Error(`contract failed: status=${contractResp.status}`);
  }

  const contract = contractResp.body.data || {};
  const views = contract.views || {};
  if (!views.kanban) {
    writeSummary(['kanban_view: missing']);
    throw new Error('kanban view missing');
  }

  const fields = pickKanbanFields(contract);
  summary.push(`fields_count: ${fields.length}`);

  log('api.data.list (kanban fields)');
  const listPayload = {
    intent: 'api.data',
    params: { op: 'list', model: MODEL, fields, limit: 5 },
  };
  const listResp = await requestJson(intentUrl, listPayload, authHeader);
  writeJson(path.join(outDir, 'list.log'), listResp);
  if (listResp.status >= 400 || !listResp.body.ok) {
    throw new Error(`list failed: status=${listResp.status}`);
  }
  const records = (listResp.body.data || {}).records || [];
  if (!records.length) {
    throw new Error('list returned no records');
  }

  writeSummary(summary);
  log('PASS kanban view mvp');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_kanban_view_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
