#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const REPO_ROOT = path.resolve(__dirname, '../..');

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

const DEBT_BASELINE =
  process.env.DEBT_BASELINE || 'docs/contract/snapshots/scenes/resolve_errors_debt.v0_9_9.json';
const DEBT_OUT = process.env.DEBT_OUT || 'docs/contract/snapshots/scenes/LATEST.resolve_errors_debt.json';
const DEBT_UPDATE = process.env.DEBT_UPDATE === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_9-9', ts);

function log(msg) {
  console.log(`[fe_scene_resolve_errors_debt_guard] ${msg}`);
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

function resolveReadPath(relPath) {
  const roots = [
    process.env.DEBT_ROOT,
    process.env.REPO_ROOT,
    REPO_ROOT,
    process.cwd(),
    '/mnt/extra-addons',
    '/mnt/addons_external',
    '/mnt/odoo',
  ].filter(Boolean);
  const stripped = relPath.startsWith('docs/') ? relPath : relPath;
  for (const root of roots) {
    const candidate = path.join(root, stripped);
    if (fs.existsSync(candidate)) return candidate;
  }
  const fallback = path.join(__dirname, 'baselines', path.basename(relPath));
  if (fs.existsSync(fallback)) return fallback;
  return '';
}

function resolveWritePath(relPath) {
  if (path.isAbsolute(relPath)) return relPath;
  const root = process.env.DEBT_ROOT || process.env.REPO_ROOT || REPO_ROOT;
  return path.join(root, relPath);
}

function normalizeDebtEntries(raw) {
  if (Array.isArray(raw)) return raw;
  if (raw && Array.isArray(raw.entries)) return raw.entries;
  return [];
}

function debtKey(entry) {
  const sceneKey = entry.scene_key || '';
  const code = entry.code || '';
  const ref = entry.ref || '';
  return `${sceneKey}::${code}::${ref}`;
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

  log('app.init');
  const initPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }

  const data = initResp.body.data || {};
  const diag = data.scene_diagnostics || {};
  const resolveErrors = Array.isArray(diag.resolve_errors) ? diag.resolve_errors : [];

  const invalid = resolveErrors.filter(
    (err) => !err || !err.scene_key || !err.code || !err.severity || !err.kind
  );
  if (invalid.length) {
    writeJson(path.join(outDir, 'resolve_errors_invalid.json'), invalid);
    throw new Error(`resolve_errors invalid entries (${invalid.length})`);
  }

  const criticalErrors = resolveErrors.filter((err) => err.severity === 'critical');
  if (criticalErrors.length) {
    writeJson(path.join(outDir, 'resolve_errors_critical.json'), criticalErrors);
    throw new Error(`critical resolve_errors (${criticalErrors.length})`);
  }

  const nonCritical = resolveErrors.filter((err) => err.severity === 'non_critical');
  const currentDebt = nonCritical.map((err) => ({
    scene_key: err.scene_key,
    code: err.code,
    ref: err.ref || '',
  }));

  const baselinePath = resolveReadPath(DEBT_BASELINE);
  if (!baselinePath) {
    throw new Error(`debt baseline not found: ${DEBT_BASELINE}`);
  }
  const baselineRaw = fs.readFileSync(baselinePath, 'utf-8');
  const baseline = normalizeDebtEntries(JSON.parse(baselineRaw));
  const baselineKeys = new Set(baseline.map(debtKey));

  const missing = currentDebt.filter((entry) => !baselineKeys.has(debtKey(entry)));
  const snapshotPath = resolveWritePath(DEBT_OUT);
  writeJson(snapshotPath, { version: 'current', entries: currentDebt });

  if (DEBT_UPDATE) {
    const updatePath = resolveWritePath(DEBT_BASELINE);
    writeJson(updatePath, { version: 'v0_9_9', generated_at: new Date().toISOString(), entries: currentDebt });
    summary.push(`debt_updated: ${updatePath}`);
    summary.push(`non_critical: ${currentDebt.length}`);
    writeSummary(summary);
    log('PASS debt update');
    log(`artifacts: ${outDir}`);
    return;
  }

  summary.push(`baseline: ${baselinePath}`);
  summary.push(`debt_out: ${snapshotPath}`);
  summary.push(`non_critical: ${currentDebt.length}`);
  summary.push(`missing: ${missing.length}`);
  writeSummary(summary);

  if (missing.length) {
    writeJson(path.join(outDir, 'resolve_errors_missing_debt.json'), missing);
    throw new Error(`resolve_errors debt missing (${missing.length})`);
  }

  log('PASS resolve_errors debt guard');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_resolve_errors_debt_guard] FAIL: ${err.message}`);
  process.exit(1);
});
