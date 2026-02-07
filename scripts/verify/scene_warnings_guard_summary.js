#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'svc_e2e_smoke';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'demo';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const DENY_WARNING_CODES = (process.env.DENY_WARNING_CODES || '')
  .split(',')
  .map((code) => code.trim())
  .filter(Boolean);
const DEFAULT_ACT_URL_MAX = Number(process.env.SC_WARN_ACT_URL_LEGACY_MAX || 3);
const MAX_WARNING_CODES_RAW = process.env.MAX_WARNING_CODES || '';
const MAX_WARNING_CODES = (process.env.MAX_WARNING_CODES || '')
  .split(',')
  .map((pair) => pair.trim())
  .filter(Boolean)
  .reduce((acc, pair) => {
    const [code, rawLimit] = pair.split('=').map((part) => (part || '').trim());
    if (!code) return acc;
    const limit = Number(rawLimit);
    if (!Number.isNaN(limit)) acc[code] = limit;
    return acc;
  }, {});
if (!MAX_WARNING_CODES_RAW && !Number.isNaN(DEFAULT_ACT_URL_MAX)) {
  MAX_WARNING_CODES.ACT_URL_LEGACY = DEFAULT_ACT_URL_MAX;
}

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-warnings', ts);

function log(msg) {
  console.log(`[scene_warnings_guard] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
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

async function loginToken() {
  const intentUrl = `${BASE_URL}/api/v1/intent`;
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
    if (!token) throw new Error('login response missing token');
  }
  return token;
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  const token = await loginToken();
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };

  log('app.init');
  const initPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }

  const diag = (initResp.body.data || {}).scene_diagnostics || {};
  const warnings = Array.isArray(diag.normalize_warnings) ? diag.normalize_warnings : [];
  const summary = {};
  for (const entry of warnings) {
    if (!entry || typeof entry !== 'object') continue;
    const code = entry.code || 'UNKNOWN';
    summary[code] = (summary[code] || 0) + 1;
  }

  const limitsSnapshot = {};
  for (const [code, limit] of Object.entries(MAX_WARNING_CODES)) {
    limitsSnapshot[code] = { max: limit, actual: summary[code] || 0 };
  }
  writeJson(path.join(outDir, 'warnings.json'), {
    total: warnings.length,
    by_code: summary,
    limits: limitsSnapshot,
    entries: warnings,
  });
  log(`warnings: ${warnings.length}`);

  if (DENY_WARNING_CODES.length) {
    const blocked = warnings.filter((item) => DENY_WARNING_CODES.includes(item.code));
    if (blocked.length) {
      writeJson(path.join(outDir, 'warnings_blocked.json'), blocked);
      throw new Error(`blocked warning codes (${blocked.length})`);
    }
  }
  const limitBreaches = [];
  for (const [code, limit] of Object.entries(MAX_WARNING_CODES)) {
    const count = summary[code] || 0;
    if (count > limit) {
      limitBreaches.push({ code, limit, count });
    }
  }
  if (limitBreaches.length) {
    writeJson(path.join(outDir, 'warnings_limits_exceeded.json'), limitBreaches);
    throw new Error(`warning limits exceeded (${limitBreaches.length})`);
  }

  log('PASS warnings guard');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[scene_warnings_guard] FAIL: ${err.message}`);
  process.exit(1);
});
