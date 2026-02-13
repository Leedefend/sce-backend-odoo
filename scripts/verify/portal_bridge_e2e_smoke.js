#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertHttpStatusOk, assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const LOGIN = process.env.E2E_LOGIN || process.env.ADMIN_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-bridge-e2e', ts);

function log(msg) {
  console.log(`[portal_bridge_e2e_smoke] ${msg}`);
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
        resolve({ status: res.statusCode || 0, body: parsed, headers: res.headers });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function requestGet(url, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const opts = {
      method: 'GET',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: headers || {},
    };
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        resolve({ status: res.statusCode || 0, body: data, headers: res.headers });
      });
    });
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `portal_bridge_${Date.now()}`;
  const summary = [];

  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
    { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
  );
  writeJson(path.join(outDir, 'login.log'), loginResp);
  assertIntentEnvelope(loginResp, 'login');
  const token = (((loginResp.body || {}).data) || {}).token || '';
  if (!token) throw new Error('login token missing');
  summary.push(`jwt: ok`);

  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };
  const initResp = await requestJson(
    intentUrl,
    { intent: 'app.init', params: { scene: 'web', with_preload: false } },
    auth
  );
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });
  summary.push(`app.init: ok`);

  const bridge = new URL('/portal/bridge', BASE_URL);
  bridge.searchParams.set('next', '/portal/lifecycle');
  bridge.searchParams.set('token', token);
  bridge.searchParams.set('db', DB_NAME);
  const bridgeResp = await requestGet(bridge.toString(), { 'X-Trace-Id': traceId });
  writeJson(path.join(outDir, 'bridge.log'), bridgeResp);
  let portalUrl = '';
  if ([301, 302, 303, 307, 308].includes(bridgeResp.status)) {
    const location = bridgeResp.headers.location;
    if (!location) throw new Error('bridge redirect missing location');
    portalUrl = new URL(location, BASE_URL).toString();
    summary.push(`bridge: ${bridgeResp.status}`);
  } else if (bridgeResp.status === 200) {
    // Some deployments may render bridge target directly.
    portalUrl = bridge.toString();
    summary.push('bridge: 200');
  } else if (bridgeResp.status === 404) {
    // Compatibility mode for environments without /portal/bridge route.
    const direct = new URL('/portal/lifecycle', BASE_URL);
    direct.searchParams.set('st', token);
    direct.searchParams.set('db', DB_NAME);
    portalUrl = direct.toString();
    summary.push('bridge: fallback_direct_portal');
  } else {
    throw new Error(`bridge failed: ${bridgeResp.status}`);
  }

  const portalResp = await requestGet(portalUrl, { 'X-Trace-Id': traceId });
  writeJson(path.join(outDir, 'portal_page.log'), { status: portalResp.status });
  const portalPageOk = portalResp.status >= 200 && portalResp.status < 300;
  if (portalPageOk) {
    summary.push(`portal page: ${portalResp.status}`);
  } else if (portalResp.status === 404) {
    summary.push('portal page: 404 (compat-disabled)');
  } else {
    assertHttpStatusOk(portalResp, 'portal page');
  }

  const portalApiUrl = new URL('/api/portal/contract', BASE_URL);
  portalApiUrl.searchParams.set('route', '/portal/lifecycle');
  portalApiUrl.searchParams.set('st', token);
  const portalApiResp = await requestGet(portalApiUrl.toString(), { 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId });
  writeJson(path.join(outDir, 'portal_api.log'), portalApiResp);
  const portalApiOk = portalApiResp.status >= 200 && portalApiResp.status < 300;
  if (portalApiOk) {
    summary.push(`portal api: ${portalApiResp.status}`);
  } else if (portalApiResp.status === 404) {
    summary.push('portal api: 404 (compat-disabled)');
  } else {
    assertHttpStatusOk(portalApiResp, 'portal api');
  }

  if (!portalPageOk && !portalApiOk) {
    throw new Error('portal endpoints unavailable (both page/api non-2xx)');
  }

  summary.push(`trace_id: ${traceId}`);
  writeSummary(summary);

  log('PASS portal bridge e2e smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[portal_bridge_e2e_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
