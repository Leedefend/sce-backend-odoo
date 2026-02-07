#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'svc_e2e_smoke';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'audit', 'scene-config', ts);

function log(msg) {
  console.log(`[scene_config_audit] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
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

function classifySource(value) {
  if (Array.isArray(value)) {
    return value.length ? 'payload' : 'payload_empty';
  }
  if (value && typeof value === 'object') {
    return Object.keys(value).length ? 'payload' : 'payload_empty';
  }
  if (typeof value === 'string') {
    return value ? 'payload' : 'missing';
  }
  return value ? 'payload' : 'missing';
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const intentUrl = `${BASE_URL}/api/v1/intent`;

  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
    { 'X-Anonymous-Intent': '1' }
  );
  if (loginResp.status >= 400 || !loginResp.body.ok) throw new Error(`login failed: ${loginResp.status}`);
  const token = (((loginResp.body || {}).data) || {}).token || '';
  if (!token) throw new Error('login token missing');

  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const initResp = await requestJson(
    intentUrl,
    { intent: 'app.init', params: { scene: 'web', with_preload: false } },
    auth
  );
  if (initResp.status >= 400 || !initResp.body.ok) throw new Error(`app.init failed: ${initResp.status}`);

  const data = (initResp.body || {}).data || {};
  const scenes = data.scenes || [];
  const report = scenes.map((scene) => {
    const code = scene.code || scene.key || '';
    return {
      code,
      layout_source: classifySource(scene.layout),
      tiles_source: classifySource(scene.tiles),
      list_profile_source: classifySource(scene.list_profile),
      portal_only: Boolean(scene.portal_only),
      spa_ready: Boolean(scene.spa_ready),
    };
  });
  const diagnostics = data.scene_diagnostics || {};
  const normalizeWarnings = Array.isArray(diagnostics.normalize_warnings) ? diagnostics.normalize_warnings : [];
  const warningSummary = {};
  for (const entry of normalizeWarnings) {
    if (!entry || typeof entry !== 'object') continue;
    const code = entry.code || 'UNKNOWN';
    warningSummary[code] = (warningSummary[code] || 0) + 1;
  }

  writeJson(path.join(outDir, 'scene_config_audit.json'), report);
  writeJson(path.join(outDir, 'scene_config_warnings.json'), {
    total: normalizeWarnings.length,
    by_code: warningSummary,
  });
  log(`scenes: ${report.length}`);
  log(`warnings: ${normalizeWarnings.length}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[scene_config_audit] FAIL: ${err.message}`);
  process.exit(1);
});
