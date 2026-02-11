#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ADMIN_PASSWD = process.env.ADMIN_PASSWD || 'admin';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-package-installed-v10_7', ts);

function log(msg) {
  console.log(`[fe_scene_package_installed_smoke] ${msg}`);
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
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `scene_package_installed_${Date.now()}`;
  const summary = [];

  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: 'admin', password: ADMIN_PASSWD } },
    { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
  );
  assertIntentEnvelope(loginResp, 'login');
  const token = (((loginResp.body || {}).data) || {}).token || '';
  if (!token) throw new Error('login token missing');
  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };

  // Ensure at least one installed package exists.
  const exportResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.export',
      params: {
        package_name: 'installed-smoke',
        package_version: '1.1.0',
        scene_channel: 'stable',
        reason: 'phase10.7 installed smoke export',
      },
    },
    auth
  );
  assertIntentEnvelope(exportResp, 'scene.package.export');
  const pkg = (((exportResp.body || {}).data) || {}).package;
  if (!pkg || typeof pkg !== 'object') throw new Error('export package missing');

  const importResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.import',
      params: {
        package: pkg,
        strategy: 'rename_on_conflict',
        reason: 'phase10.7 installed smoke import',
      },
    },
    auth
  );
  assertIntentEnvelope(importResp, 'scene.package.import');

  const installedResp = await requestJson(intentUrl, { intent: 'scene.packages.installed', params: {} }, auth);
  writeJson(path.join(outDir, 'scene_packages_installed.log'), installedResp);
  assertIntentEnvelope(installedResp, 'scene.packages.installed');
  const packages = ((((installedResp.body || {}).data) || {}).packages) || [];
  if (!Array.isArray(packages) || packages.length < 1) {
    throw new Error('expected at least one installed package');
  }

  const activeCounter = new Map();
  for (const row of packages) {
    if (!row || typeof row !== 'object') throw new Error('invalid package row');
    if (!row.package_name || !row.installed_version || typeof row.active !== 'boolean') {
      throw new Error('missing required installed package fields');
    }
    if (row.active) {
      const key = String(row.package_name);
      activeCounter.set(key, (activeCounter.get(key) || 0) + 1);
    }
  }
  for (const [name, count] of activeCounter.entries()) {
    if (count > 1) {
      throw new Error(`active=true appears multiple times for package_name=${name}`);
    }
  }

  summary.push(`trace_id: ${traceId}`);
  summary.push(`package_count: ${packages.length}`);
  summary.push(`active_package_names: ${Array.from(activeCounter.keys()).join(',') || '-'}`);
  writeSummary(summary);

  log('PASS scene package installed smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_package_installed_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
