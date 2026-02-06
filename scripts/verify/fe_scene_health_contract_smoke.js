#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'svc_project_ro';
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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-health-v10_3', ts);

function log(msg) {
  console.log(`[fe_scene_health_contract_smoke] ${msg}`);
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

function countCriticalResolveErrors(diag) {
  const list = diag && Array.isArray(diag.resolve_errors) ? diag.resolve_errors : [];
  return list.filter((item) => String((item && item.severity) || '').toLowerCase() === 'critical').length;
}

function countCriticalDriftWarn(diag) {
  const list = diag && Array.isArray(diag.drift) ? diag.drift : [];
  return list.filter((item) => {
    const sev = String((item && item.severity) || '').toLowerCase();
    const key = String((item && item.scene_key) || '');
    return sev === 'warn' && (key === 'projects.list' || key === 'projects.ledger');
  }).length;
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `scene_health_contract_${Date.now()}`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
      'X-Trace-Id': traceId,
    });
    if (bootstrapResp.status >= 400 || !bootstrapResp.body.ok) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    const candidates = [
      { login: process.env.SCENE_LOGIN || '', password: process.env.SCENE_PASSWORD || '' },
      { login: process.env.E2E_LOGIN || '', password: process.env.E2E_PASSWORD || '' },
      { login: 'admin', password: process.env.ADMIN_PASSWD || 'admin' },
      { login: LOGIN, password: PASSWORD },
    ].filter((c) => c.login && c.password);

    let lastLoginResp = null;
    for (const candidate of candidates) {
      log(`login: ${candidate.login} db=${DB_NAME}`);
      const loginPayload = {
        intent: 'login',
        params: { db: DB_NAME, login: candidate.login, password: candidate.password },
      };
      const loginResp = await requestJson(intentUrl, loginPayload, {
        'X-Anonymous-Intent': '1',
        'X-Trace-Id': traceId,
      });
      lastLoginResp = loginResp;
      if (loginResp.status < 400 && loginResp.body.ok) {
        token = (loginResp.body.data || {}).token || '';
        if (token) break;
      }
    }
    if (!token) {
      writeJson(path.join(outDir, 'login.log'), lastLoginResp || {});
      throw new Error('login failed: no usable credentials');
    }
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
    'X-Trace-Id': traceId,
  };

  log('app.init');
  const initResp = await requestJson(
    intentUrl,
    { intent: 'app.init', params: { scene: 'web', with_preload: false } },
    authHeader
  );
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }
  const initDiag = (initResp.body && initResp.body.data && initResp.body.data.scene_diagnostics) || {};
  const initCriticalResolve = countCriticalResolveErrors(initDiag);
  const initCriticalDrift = countCriticalDriftWarn(initDiag);

  log('scene.health');
  const healthResp = await requestJson(intentUrl, { intent: 'scene.health', params: {} }, authHeader);
  writeJson(path.join(outDir, 'scene_health.log'), healthResp);
  if (healthResp.status >= 400 || !healthResp.body.ok) {
    throw new Error(`scene.health failed: status=${healthResp.status}`);
  }
  const health = (healthResp.body && healthResp.body.data) || {};
  const summaryObj = health.summary || {};
  const details = health.details || {};

  const requiredKeys = ['company_id', 'scene_channel', 'rollback_active', 'scene_version', 'schema_version', 'contract_ref', 'summary', 'details', 'last_updated_at', 'trace_id'];
  for (const key of requiredKeys) {
    if (!(key in health)) {
      throw new Error(`scene.health missing key: ${key}`);
    }
  }
  if (
    typeof summaryObj.critical_resolve_errors_count !== 'number' ||
    typeof summaryObj.critical_drift_warn_count !== 'number' ||
    typeof summaryObj.non_critical_debt_count !== 'number'
  ) {
    throw new Error('scene.health summary counters missing');
  }
  if (!Array.isArray(details.resolve_errors) || !Array.isArray(details.drift) || !Array.isArray(details.debt)) {
    throw new Error('scene.health details arrays missing');
  }

  if (summaryObj.critical_resolve_errors_count !== initCriticalResolve) {
    throw new Error(
      `critical_resolve_errors_count mismatch: health=${summaryObj.critical_resolve_errors_count}, init=${initCriticalResolve}`
    );
  }
  if (summaryObj.critical_drift_warn_count !== initCriticalDrift) {
    throw new Error(
      `critical_drift_warn_count mismatch: health=${summaryObj.critical_drift_warn_count}, init=${initCriticalDrift}`
    );
  }

  summary.push(`company_id: ${health.company_id != null ? health.company_id : '-'}`);
  summary.push(`scene_channel: ${health.scene_channel}`);
  summary.push(`rollback_active: ${Boolean(health.rollback_active)}`);
  summary.push(`critical_resolve_errors_count: ${summaryObj.critical_resolve_errors_count}`);
  summary.push(`critical_drift_warn_count: ${summaryObj.critical_drift_warn_count}`);
  summary.push(`non_critical_debt_count: ${summaryObj.non_critical_debt_count}`);
  summary.push(`trace_id: ${health.trace_id || '-'}`);
  writeSummary(summary);

  log('PASS health contract');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_health_contract_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
