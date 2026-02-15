#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'admin';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'ChangeMe_123!';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const DENY_WARNING_CODES = (process.env.DENY_WARNING_CODES || '')
  .split(',')
  .map((code) => code.trim())
  .filter(Boolean);

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_9-8', ts);

function log(msg) {
  console.log(`[fe_scene_diagnostics_smoke] ${msg}`);
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
    writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
    assertIntentEnvelope(bootstrapResp, 'bootstrap', { requireTrace: false });
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    writeJson(path.join(outDir, 'login.log'), loginResp);
    assertIntentEnvelope(loginResp, 'login');
    token = (loginResp.body.data || {}).token || '';
    if (!token) {
      throw new Error('login response missing token');
    }
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('app.init');
  const initPayload = {
    intent: 'app.init',
    params: { scene: 'web', with_preload: false, contract_mode: 'hud' },
  };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });

  const data = initResp.body.data || {};
  const diag = data.scene_diagnostics;
  if (!diag || typeof diag !== 'object') {
    throw new Error('scene_diagnostics missing');
  }
  if (!diag.schema_version) {
    throw new Error('scene_diagnostics.schema_version missing');
  }
  if (!diag.scene_version) {
    throw new Error('scene_diagnostics.scene_version missing');
  }
  if (!Array.isArray(diag.resolve_errors)) {
    throw new Error('scene_diagnostics.resolve_errors not array');
  }
  if (!Array.isArray(diag.drift)) {
    throw new Error('scene_diagnostics.drift not array');
  }
  const allowedSeverities = new Set(['critical', 'non_critical']);
  const invalidErrors = diag.resolve_errors.filter(
    (err) => !err || !err.scene_key || !err.code || !err.severity || !allowedSeverities.has(err.severity)
  );
  if (invalidErrors.length) {
    throw new Error(`resolve_errors invalid entries (${invalidErrors.length})`);
  }
  const criticalErrors = diag.resolve_errors.filter((err) => err.severity === 'critical');
  if (criticalErrors.length) {
    throw new Error(`resolve_errors critical (${criticalErrors.length})`);
  }
  if (diag.normalize_warnings && Array.isArray(diag.normalize_warnings)) {
    const bad = diag.normalize_warnings.filter((item) => !item || !item.code || !item.message);
    if (bad.length) {
      throw new Error('normalize_warnings contains invalid entries');
    }
    if (DENY_WARNING_CODES.length) {
      const blocked = diag.normalize_warnings.filter((item) => DENY_WARNING_CODES.includes(item.code));
      if (blocked.length) {
        writeJson(path.join(outDir, 'normalize_warnings_blocked.json'), blocked);
        throw new Error(`normalize_warnings blocked codes (${blocked.length})`);
      }
    }
  }

  summary.push(`schema_version: ${diag.schema_version}`);
  summary.push(`scene_version: ${diag.scene_version}`);
  summary.push(`loaded_from: ${diag.loaded_from || '-'}`);
  summary.push(`resolve_errors: ${diag.resolve_errors.length}`);
  summary.push(`drift: ${diag.drift.length}`);
  summary.push(`normalize_warnings: ${(diag.normalize_warnings || []).length}`);
  writeSummary(summary);

  log('PASS diagnostics');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_diagnostics_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
