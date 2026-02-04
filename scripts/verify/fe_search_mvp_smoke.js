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
  console.log(`[fe_search_mvp_smoke] ${msg}`);
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

  log('api.data.list (base)');
  const basePayload = {
    intent: 'api.data',
    params: { op: 'list', model: MODEL, fields: ['id', 'name'], limit: 5 },
  };
  const baseResp = await requestJson(intentUrl, basePayload, authHeader);
  writeJson(path.join(outDir, 'base.log'), baseResp);
  if (baseResp.status >= 400 || !baseResp.body.ok) {
    throw new Error(`base list failed: status=${baseResp.status}`);
  }
  const baseRecords = (baseResp.body.data || {}).records || [];
  if (!baseRecords.length || !baseRecords[0].name) {
    throw new Error('base list missing records');
  }

  const term = String(baseRecords[0].name).slice(0, 6);

  log('api.data.list (search)');
  const searchPayload = {
    intent: 'api.data',
    params: { op: 'list', model: MODEL, fields: ['id', 'name'], limit: 5, search_term: term },
  };
  const searchResp = await requestJson(intentUrl, searchPayload, authHeader);
  writeJson(path.join(outDir, 'search.log'), searchResp);
  if (searchResp.status >= 400 || !searchResp.body.ok) {
    throw new Error(`search list failed: status=${searchResp.status}`);
  }
  const searchRecords = (searchResp.body.data || {}).records || [];

  summary.push(`term: ${term}`);
  summary.push(`base_count: ${baseRecords.length}`);
  summary.push(`search_count: ${searchRecords.length}`);
  writeSummary(summary);

  if (!searchRecords.length) {
    throw new Error('search returned no records');
  }

  log('PASS search mvp');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_search_mvp_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
