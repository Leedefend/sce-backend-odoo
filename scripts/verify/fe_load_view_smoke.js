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
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = Number(process.env.RECORD_ID || 8);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-1', ts);

function log(msg) {
  console.log(`[fe_load_view_smoke] ${msg}`);
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

  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
  if (loginResp.status >= 400 || !loginResp.body.ok) {
    writeJson(path.join(outDir, 'login.log'), loginResp);
    throw new Error(`login failed: status=${loginResp.status}`);
  }
  const token = (loginResp.body.data || {}).token;
  if (!token) {
    throw new Error('login response missing token');
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('load_view');
  const viewPayload = { intent: 'load_view', params: { model: MODEL, view_type: 'form' } };
  const viewResp = await requestJson(intentUrl, viewPayload, authHeader);
  writeJson(path.join(outDir, 'load_view.log'), viewResp);
  if (viewResp.status >= 400 || !viewResp.body.ok) {
    throw new Error(`load_view failed: status=${viewResp.status}`);
  }
  const viewData = viewResp.body.data || {};
  const layoutOk = Boolean(viewData.layout);
  summary.push(`layout_ok: ${layoutOk ? 'true' : 'false'}`);

  log('api.data.read');
  const readPayload = { intent: 'api.data', params: { op: 'read', model: MODEL, ids: [RECORD_ID], fields: ['id', 'name'] } };
  const readResp = await requestJson(intentUrl, readPayload, authHeader);
  writeJson(path.join(outDir, 'read.log'), readResp);
  if (readResp.status >= 400 || !readResp.body.ok) {
    throw new Error(`read failed: status=${readResp.status}`);
  }
  const records = (readResp.body.data || {}).records || [];
  const recordOk = Array.isArray(records) && records.length > 0;
  summary.push(`record_ok: ${recordOk ? 'true' : 'false'}`);

  writeSummary(summary);

  if (!layoutOk || !recordOk) {
    throw new Error('layout/read assertions failed');
  }

  log('PASS layout_ok=true record_ok=true');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_load_view_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
