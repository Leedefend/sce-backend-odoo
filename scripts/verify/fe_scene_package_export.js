#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const CONTRACT_ROOT = process.env.CONTRACT_ROOT || process.cwd();
const PACKAGE_NAME = (process.env.PACKAGE_NAME || 'scene-package').trim();
const PACKAGE_VERSION = (process.env.PACKAGE_VERSION || '1.0.0').trim();
const SCENE_CHANNEL = (process.env.SCENE_CHANNEL || 'stable').trim().toLowerCase();
const ADMIN_PASSWD = process.env.ADMIN_PASSWD || 'admin';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-package-export-v10_6', ts);

function log(msg) {
  console.log(`[fe_scene_package_export] ${msg}`);
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
  const traceId = `scene_package_export_${Date.now()}`;
  const summary = [];

  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: 'admin', password: ADMIN_PASSWD } },
    { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
  );
  if (loginResp.status >= 400 || !loginResp.body.ok) throw new Error(`login failed: ${loginResp.status}`);
  const token = (((loginResp.body || {}).data) || {}).token || '';
  if (!token) throw new Error('login token missing');
  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };

  const exportResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.export',
      params: {
        package_name: PACKAGE_NAME,
        package_version: PACKAGE_VERSION,
        scene_channel: SCENE_CHANNEL,
        reason: 'phase10.6 package export',
      },
    },
    auth
  );
  writeJson(path.join(outDir, 'scene_package_export.log'), exportResp);
  if (exportResp.status >= 400 || !exportResp.body.ok) {
    throw new Error(`scene.package.export failed: ${exportResp.status}`);
  }

  const data = (exportResp.body || {}).data || {};
  const pkg = data.package || {};
  if (!pkg.package_name || !pkg.package_version || !pkg.checksum || !Array.isArray(pkg.scenes)) {
    throw new Error('export package contract invalid');
  }

  const outPath = path.join(
    CONTRACT_ROOT,
    'docs/contract/packages/scenes',
    `${PACKAGE_NAME}-${PACKAGE_VERSION}.json`
  );
  writeJson(outPath, pkg);

  summary.push(`trace_id: ${traceId}`);
  summary.push(`package_name: ${pkg.package_name}`);
  summary.push(`package_version: ${pkg.package_version}`);
  summary.push(`scene_count: ${(pkg.scenes || []).length}`);
  summary.push(`checksum: ${pkg.checksum}`);
  summary.push(`out: ${outPath}`);
  writeSummary(summary);

  log('PASS scene package export');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_package_export] FAIL: ${err.message}`);
  process.exit(1);
});
