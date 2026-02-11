#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');
const { probeModels, assertRequiredModels } = require('./scene_observability_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'admin';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'admin';
const STRICT = process.env.SCENE_OBSERVABILITY_PREFLIGHT_STRICT === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-observability-preflight-v10_4', ts);

function log(msg) {
  console.log(`[fe_scene_observability_preflight_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload || {});
    const opts = {
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: Object.assign(
        {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        headers || {}
      ),
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
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const traceId = `scene_observability_preflight_${Date.now()}`;
  const intentUrl = `${BASE_URL}/api/v1/intent`;

  const candidates = [
    { login: process.env.SCENE_LOGIN || '', password: process.env.SCENE_PASSWORD || '' },
    { login: process.env.E2E_LOGIN || '', password: process.env.E2E_PASSWORD || '' },
    { login: LOGIN, password: PASSWORD },
    { login: 'admin', password: process.env.ADMIN_PASSWD || 'admin' },
  ].filter((c) => c.login && c.password);
  let token = '';
  let usedLogin = '';
  let lastLoginResp = null;
  for (const candidate of candidates) {
    const loginResp = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: candidate.login, password: candidate.password } },
      { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
    );
    lastLoginResp = loginResp;
    if (loginResp.status < 400 && loginResp.body.ok) {
      assertIntentEnvelope(loginResp, 'login');
      token = (((loginResp.body || {}).data) || {}).token || '';
      if (token) {
        usedLogin = candidate.login;
        break;
      }
    }
  }
  if (!token) throw new Error('login token missing');
  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };

  const governance = await probeModels(requestJson, intentUrl, auth, ['sc.scene.governance.log', 'sc.audit.log']);
  const notify = await probeModels(requestJson, intentUrl, auth, ['sc.audit.log']);
  const report = {
    trace_id: traceId,
    strict: STRICT,
    governance: governance,
    notify: notify,
  };
  if (lastLoginResp) {
    report.login = {
      used_login: usedLogin || null,
      final_status: lastLoginResp.status || 0,
    };
  }
  writeJson(path.join(outDir, 'preflight.log'), report);

  assertRequiredModels(STRICT, ['sc.scene.governance.log', 'sc.audit.log'], governance.available, 'governance log');
  assertRequiredModels(STRICT, ['sc.audit.log'], notify.available, 'notify audit');

  const summary = [
    `trace_id: ${traceId}`,
    `strict: ${STRICT ? 'true' : 'false'}`,
    `governance_available: ${(governance.available || []).join(',') || '-'}`,
    `governance_missing: ${(governance.missing || []).join(',') || '-'}`,
    `notify_available: ${(notify.available || []).join(',') || '-'}`,
    `notify_missing: ${(notify.missing || []).join(',') || '-'}`,
  ];
  writeSummary(summary);
  log('PASS scene observability preflight');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_observability_preflight_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
