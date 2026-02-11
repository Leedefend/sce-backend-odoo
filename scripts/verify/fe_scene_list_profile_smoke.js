#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

// Requires: interactive user (not svc_* readonly) with project read + portal lifecycle access.
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

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_9-2', ts);

function log(msg) {
  console.log(`[fe_scene_list_profile_smoke] ${msg}`);
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
  const initPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });

  const data = initResp.body.data || {};
  const scenes = Array.isArray(data.scenes) ? data.scenes : [];
  const getScene = (key) => scenes.find((item) => item && (item.code === key || item.key === key));
  const ledger = getScene('projects.ledger');
  const list = getScene('projects.list');
  if (!ledger) {
    throw new Error('scene projects.ledger missing');
  }
  if (!list) {
    throw new Error('scene projects.list missing');
  }
  const ledgerProfile = ledger.list_profile || {};
  const listProfile = list.list_profile || {};
  const ledgerColumns = ledgerProfile.columns || [];
  const listColumns = listProfile.columns || [];
  const ledgerHidden = ledgerProfile.hidden_columns || [];
  const listHidden = listProfile.hidden_columns || [];

  summary.push(`ledger_found: ${Boolean(ledger)}`);
  summary.push(`ledger_columns: ${ledgerColumns.length}`);
  summary.push(`ledger_hidden: ${ledgerHidden.length}`);
  summary.push(`ledger_default_sort: ${ledger.default_sort || '-'}`);
  summary.push(`list_found: ${Boolean(list)}`);
  summary.push(`list_columns: ${listColumns.length}`);
  summary.push(`list_hidden: ${listHidden.length}`);
  summary.push(`list_default_sort: ${list.default_sort || '-'}`);
  writeSummary(summary);

  if (!ledgerColumns.length) {
    throw new Error('projects.ledger list_profile.columns missing');
  }
  if (!listColumns.length) {
    throw new Error('projects.list list_profile.columns missing');
  }
  if (!ledgerHidden.includes('message_needaction')) {
    throw new Error('projects.ledger list_profile.hidden_columns missing message_needaction');
  }
  if (!listHidden.includes('message_needaction')) {
    throw new Error('projects.list list_profile.hidden_columns missing message_needaction');
  }

  log('PASS list_profile');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_list_profile_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
