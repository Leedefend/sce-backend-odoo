#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { canonicalizeScenes } = require('./lib/scene_snapshot');
const { loadProfiles, normalizeVersion } = require('./lib/scene_schema_loader');
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

const CHANNELS = new Set(['stable', 'beta', 'dev']);

function normalizeChannel(value) {
  const raw = String(value || '').trim().toLowerCase();
  return CHANNELS.has(raw) ? raw : 'stable';
}

const SCENE_CHANNEL = normalizeChannel(process.env.SCENE_CHANNEL || 'stable');
const DEFAULT_CONTRACT_OUT = `docs/contract/exports/scenes/${SCENE_CHANNEL}/LATEST.json`;
const CONTRACT_OUT = process.env.CONTRACT_OUT || DEFAULT_CONTRACT_OUT;
const CONTRACT_LATEST = process.env.CONTRACT_LATEST || DEFAULT_CONTRACT_OUT;
const INCLUDE_GENERATED_AT = process.env.INCLUDE_GENERATED_AT === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v10_0', ts);

function log(msg) {
  console.log(`[fe_scene_contract_export] ${msg}`);
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

function resolveWritePath(relPath) {
  if (path.isAbsolute(relPath)) return relPath;
  const root = process.env.CONTRACT_ROOT || process.env.SNAPSHOT_ROOT || '/mnt/extra-addons';
  return path.join(root, relPath);
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
    try {
      assertIntentEnvelope(bootstrapResp, 'bootstrap', { allowMetaIntentAliases: ['session.bootstrap'] });
    } catch (_err) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status || 0}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    try {
      assertIntentEnvelope(loginResp, 'login');
    } catch (_err) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status || 0}`);
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
  const initPayload = { intent: 'app.init', params: initParams };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });

  const data = initResp.body.data || {};
  const scenes = Array.isArray(data.scenes) ? data.scenes : [];
  const canonical = canonicalizeScenes(scenes);
  const schemaVersion = normalizeVersion(data.schema_version || 'v1', 'v1');
  const profiles = loadProfiles(schemaVersion);

  const contract = {
    schema_version: data.schema_version || schemaVersion,
    scene_version: data.scene_version || '',
    profiles_version: profiles.version || '',
    scenes: canonical,
  };
  if (INCLUDE_GENERATED_AT) {
    contract.generated_at = new Date().toISOString();
  }

  const outPath = resolveWritePath(CONTRACT_OUT);
  const latestPath = resolveWritePath(CONTRACT_LATEST);
  writeJson(outPath, contract);
  if (CONTRACT_LATEST) {
    writeJson(latestPath, contract);
  }

  summary.push(`contract_out: ${outPath}`);
  summary.push(`contract_latest: ${latestPath}`);
  summary.push(`scene_channel: ${SCENE_CHANNEL}`);
  summary.push(`scene_count: ${canonical.length}`);
  summary.push(`schema_version: ${contract.schema_version}`);
  summary.push(`scene_version: ${contract.scene_version}`);
  summary.push(`profiles_version: ${contract.profiles_version}`);
  writeSummary(summary);

  log('PASS contract export');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_contract_export] FAIL: ${err.message}`);
  process.exit(1);
});
