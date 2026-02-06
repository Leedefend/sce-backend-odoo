#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ADMIN_PASSWD = process.env.ADMIN_PASSWD || 'admin';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-package-dry-run-v10_6', ts);

function log(msg) {
  console.log(`[fe_scene_package_dry_run_smoke] ${msg}`);
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
  const traceId = `scene_package_dry_run_${Date.now()}`;
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

  const beforeParamResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'ir.config_parameter',
        fields: ['id', 'key', 'value'],
        domain: [['key', '=', 'sc.scene.package.imported_scenes']],
        limit: 1,
      },
    },
    auth
  );
  const beforeRows = ((((beforeParamResp.body || {}).data) || {}).records) || [];
  const beforeValue = beforeRows.length ? String(beforeRows[0].value || '') : '';

  const exportResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.export',
      params: {
        package_name: 'dry-run-smoke',
        package_version: '1.0.0',
        scene_channel: 'stable',
        reason: 'phase10.6 dry-run export',
      },
    },
    auth
  );
  if (exportResp.status >= 400 || !exportResp.body.ok) throw new Error(`scene.package.export failed: ${exportResp.status}`);
  const pkg = (((exportResp.body || {}).data) || {}).package;
  if (!pkg || typeof pkg !== 'object') throw new Error('export package missing');

  const dryRunResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.dry_run_import',
      params: { package: pkg },
    },
    auth
  );
  writeJson(path.join(outDir, 'scene_package_dry_run.log'), dryRunResp);
  if (dryRunResp.status >= 400 || !dryRunResp.body.ok) {
    throw new Error(`scene.package.dry_run_import failed: ${dryRunResp.status}`);
  }
  const dryData = (dryRunResp.body || {}).data || {};
  if (dryData.dry_run !== true || !dryData.report || !dryData.summary) {
    throw new Error('dry-run contract invalid');
  }

  const afterParamResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'ir.config_parameter',
        fields: ['id', 'key', 'value'],
        domain: [['key', '=', 'sc.scene.package.imported_scenes']],
        limit: 1,
      },
    },
    auth
  );
  const afterRows = ((((afterParamResp.body || {}).data) || {}).records) || [];
  const afterValue = afterRows.length ? String(afterRows[0].value || '') : '';
  if (beforeValue !== afterValue) {
    throw new Error('dry-run mutated sc.scene.package.imported_scenes');
  }

  summary.push(`trace_id: ${traceId}`);
  summary.push(`dry_run: true`);
  summary.push(`summary.scene_count: ${dryData.summary.scene_count}`);
  summary.push(`summary.additions_count: ${dryData.summary.additions_count}`);
  summary.push(`summary.conflicts_count: ${dryData.summary.conflicts_count}`);
  writeSummary(summary);

  log('PASS scene package dry-run smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_package_dry_run_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
