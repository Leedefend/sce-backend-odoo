#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { canonicalizeScenes } = require('./lib/scene_snapshot');

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

const CHANNELS = new Set(['stable', 'beta', 'dev']);
const SCENE_CHANNEL = CHANNELS.has(String(process.env.SCENE_CHANNEL || '').toLowerCase())
  ? String(process.env.SCENE_CHANNEL || '').toLowerCase()
  : 'stable';
const USE_PINNED = ['1', 'true', 'yes', 'on'].includes(String(process.env.SCENE_USE_PINNED || process.env.SCENE_ROLLBACK || '').toLowerCase());

const DRIFT_BASELINE =
  process.env.DRIFT_BASELINE || 'docs/contract/snapshots/scenes/scene_drift_debt.v10_0.json';
const DRIFT_OUT = process.env.DRIFT_OUT || '/mnt/artifacts/scenes/scene_drift_report.latest.json';
const DEFAULT_CONTRACT_BASELINE = USE_PINNED
  ? 'docs/contract/exports/scenes/stable/PINNED.json'
  : `docs/contract/exports/scenes/${SCENE_CHANNEL}/LATEST.json`;
const CONTRACT_BASELINE = process.env.CONTRACT_BASELINE || DEFAULT_CONTRACT_BASELINE;
const CONTRACT_OUT = process.env.CONTRACT_OUT || '/mnt/artifacts/scenes/scene_contract.latest.json';
const CONTRACT_DIFF = process.env.CONTRACT_DIFF || '/mnt/artifacts/scenes/scene_contract.diff.txt';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v10_0', ts);

const CRITICAL_SCENES = new Set(['projects.list', 'projects.ledger']);

function log(msg) {
  console.log(`[fe_scene_drift_guard] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeText(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
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
    process.env.DRIFT_ROOT,
    '/mnt',
    '/mnt/extra-addons',
    '/mnt/addons_external',
    '/mnt/odoo',
    '/mnt/e/sc-backend-odoo',
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

function driftKey(entry) {
  const sceneKey = entry.scene_key || '';
  const kind = entry.kind || '';
  const fields = Array.isArray(entry.fields) ? entry.fields.join(',') : '';
  return `${sceneKey}::${kind}::${fields}`;
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
  const initParams = { scene: 'web', with_preload: false };
  if (SCENE_CHANNEL) initParams.scene_channel = SCENE_CHANNEL;
  if (USE_PINNED) initParams.scene_use_pinned = '1';
  const initPayload = { intent: 'app.init', params: initParams };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }

  const data = initResp.body.data || {};
  const diag = data.scene_diagnostics || {};
  const drift = Array.isArray(diag.drift) ? diag.drift : [];

  const invalid = drift.filter(
    (entry) => !entry || !entry.scene_key || !entry.kind || !entry.severity || !entry.source || !entry.fields
  );
  if (invalid.length) {
    writeJson(path.join(outDir, 'drift_invalid.json'), invalid);
    throw new Error(`drift invalid entries (${invalid.length})`);
  }

  const criticalWarn = drift.filter(
    (entry) => entry.severity === 'warn' && CRITICAL_SCENES.has(entry.scene_key)
  );
  if (criticalWarn.length) {
    writeJson(path.join(outDir, 'drift_critical_warn.json'), criticalWarn);
    throw new Error(`critical scenes drift warn (${criticalWarn.length})`);
  }

  const baselinePath = resolveReadPath(DRIFT_BASELINE);
  if (!baselinePath) {
    throw new Error(`drift baseline not found: ${DRIFT_BASELINE}`);
  }
  const baselineRaw = fs.readFileSync(baselinePath, 'utf-8');
  const baseline = JSON.parse(baselineRaw);
  const baselineEntries = Array.isArray(baseline.entries) ? baseline.entries : [];
  const baselineKeys = new Set(baselineEntries.map(driftKey));

  const fallbackDrift = drift.filter((entry) => entry.kind === 'fallback_override');
  const missing = fallbackDrift.filter((entry) => !baselineKeys.has(driftKey(entry)));

  const driftReport = {
    scene_count: Array.isArray(data.scenes) ? data.scenes.length : 0,
    drift_count: drift.length,
    critical_warn: criticalWarn.length,
    fallback_override: fallbackDrift.length,
    entries: drift,
  };
  writeJson(DRIFT_OUT, driftReport);

  const scenes = Array.isArray(data.scenes) ? data.scenes : [];
  const contract = {
    schema_version: data.schema_version || '',
    scene_version: data.scene_version || '',
    scenes: canonicalizeScenes(scenes),
  };
  writeJson(CONTRACT_OUT, contract);

  const contractBaselinePath = resolveReadPath(CONTRACT_BASELINE);
  if (!contractBaselinePath) {
    throw new Error(`contract baseline not found: ${CONTRACT_BASELINE}`);
  }
  const contractBaseline = JSON.parse(fs.readFileSync(contractBaselinePath, 'utf-8'));
  const currentStr = JSON.stringify(contract);
  const baselineStr = JSON.stringify(contractBaseline);
  const diffLines = [
    `baseline: ${contractBaselinePath}`,
    `current: ${CONTRACT_OUT}`,
    `match: ${currentStr === baselineStr}`,
  ];
  writeText(CONTRACT_DIFF, diffLines.join('\n'));
  if (currentStr !== baselineStr) {
    writeJson('/mnt/artifacts/scenes/scene_contract.current.json', contract);
    writeJson('/mnt/artifacts/scenes/scene_contract.baseline.json', contractBaseline);
  }

  summary.push(`drift_out: ${DRIFT_OUT}`);
  summary.push(`drift_count: ${drift.length}`);
  summary.push(`fallback_override: ${fallbackDrift.length}`);
  summary.push(`missing: ${missing.length}`);
  summary.push(`contract_out: ${CONTRACT_OUT}`);
  summary.push(`contract_diff: ${CONTRACT_DIFF}`);
  writeSummary(summary);

  if (missing.length) {
    writeJson(path.join(outDir, 'drift_missing_debt.json'), missing);
    throw new Error(`fallback_override drift missing (${missing.length})`);
  }

  log('PASS drift guard');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_drift_guard] FAIL: ${err.message}`);
  process.exit(1);
});
