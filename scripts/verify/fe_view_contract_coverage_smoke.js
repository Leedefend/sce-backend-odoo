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
const VIEW_TYPE = process.env.MVP_VIEW_TYPE || 'form';
const ALLOWED_MISSING = (process.env.ALLOWED_MISSING || '').split(',').map((s) => s.trim()).filter(Boolean);
const REQUIRED_NODES = (process.env.REQUIRED_NODES || 'field,group,notebook,page,headerButtons,statButtons,ribbon,chatter')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-semantic', ts);

function log(msg) {
  console.log(`[fe_view_contract_coverage_smoke] ${msg}`);
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

function asArray(value) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') return [value];
  return [];
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
    const bootstrapPayload = {
      intent: 'bootstrap',
      params: { db: DB_NAME, login: BOOTSTRAP_LOGIN },
    };
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

  log('load_view');
  const viewPayload = { intent: 'load_view', params: { model: MODEL, view_type: VIEW_TYPE } };
  const viewResp = await requestJson(intentUrl, viewPayload, authHeader);
  writeJson(path.join(outDir, 'load_view.log'), viewResp);
  if (viewResp.status >= 400 || !viewResp.body.ok) {
    throw new Error(`load_view failed: status=${viewResp.status}`);
  }

  const viewData = viewResp.body.data || {};
  const layout = viewData.layout;
  const layoutOk = Boolean(layout && typeof layout === 'object');
  if (!layoutOk) {
    throw new Error('layout missing');
  }

  const present = new Set();
  if (asArray(layout.groups).length) present.add('group');
  const groupFields = asArray(layout.groups).some((g) => asArray(g.fields).length || asArray(g.sub_groups).length);
  if (groupFields) present.add('field');
  if (asArray(layout.notebooks).length) present.add('notebook');
  if (asArray(layout.notebooks).some((nb) => asArray(nb.pages).length)) present.add('page');
  if (asArray(layout.headerButtons).length) present.add('headerButtons');
  if (asArray(layout.statButtons).length) present.add('statButtons');
  if (layout.ribbon) present.add('ribbon');
  if (layout.chatter) present.add('chatter');

  const supported = new Set(['field', 'group', 'notebook', 'page', 'headerButtons', 'statButtons', 'ribbon', 'chatter']);
  const missing = REQUIRED_NODES.filter((node) => !present.has(node));
  const allowedMissing = new Set(ALLOWED_MISSING);
  const blockingMissing = missing.filter((node) => !allowedMissing.has(node));

  summary.push(`layout_ok: ${layoutOk ? 'true' : 'false'}`);
  summary.push(`present_count: ${present.size}`);
  summary.push(`required_count: ${REQUIRED_NODES.length}`);
  summary.push(`missing_count: ${missing.length}`);
  summary.push(`present_nodes: ${[...present].sort().join(',') || '-'}`);
  summary.push(`required_nodes: ${REQUIRED_NODES.join(',')}`);
  summary.push(`supported_nodes: ${[...supported].sort().join(',')}`);
  summary.push(`missing_nodes: ${missing.join(',') || '-'}`);
  summary.push(`allowed_missing: ${ALLOWED_MISSING.join(',') || '-'}`);

  writeJson(path.join(outDir, 'coverage.json'), {
    model: MODEL,
    view_type: VIEW_TYPE,
    present_count: present.size,
    required_count: REQUIRED_NODES.length,
    missing_count: missing.length,
    present_nodes: [...present].sort(),
    required_nodes: REQUIRED_NODES,
    missing_nodes: missing,
    allowed_missing: ALLOWED_MISSING,
    blocking_missing: blockingMissing,
  });
  writeSummary(summary);

  if (blockingMissing.length) {
    throw new Error(`missing nodes: ${blockingMissing.join(',')}`);
  }

  log('PASS contract coverage');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_view_contract_coverage_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
