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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-package-import-v10_6', ts);

function log(msg) {
  console.log(`[fe_scene_package_import_smoke] ${msg}`);
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
  const traceId = `scene_package_import_${Date.now()}`;
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
        package_name: 'import-smoke',
        package_version: '1.0.0',
        scene_channel: 'stable',
        reason: 'phase10.6 import smoke export',
      },
    },
    auth
  );
  if (exportResp.status >= 400 || !exportResp.body.ok) throw new Error(`scene.package.export failed: ${exportResp.status}`);
  const pkg = (((exportResp.body || {}).data) || {}).package;
  if (!pkg || typeof pkg !== 'object') throw new Error('export package missing');

  const importResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.package.import',
      params: {
        package: pkg,
        strategy: 'rename_on_conflict',
        reason: 'phase10.6 import smoke',
      },
    },
    auth
  );
  writeJson(path.join(outDir, 'scene_package_import.log'), importResp);
  if (importResp.status >= 400 || !importResp.body.ok) {
    throw new Error(`scene.package.import failed: ${importResp.status}`);
  }
  const importData = (importResp.body || {}).data || {};
  if (!Array.isArray(importData.imported_scene_keys) || !importData.summary) {
    throw new Error('scene.package.import contract invalid');
  }

  const healthResp = await requestJson(intentUrl, { intent: 'scene.health', params: { mode: 'summary' } }, auth);
  writeJson(path.join(outDir, 'scene_health.log'), healthResp);
  if (healthResp.status >= 400 || !healthResp.body.ok) {
    throw new Error(`scene.health failed after import: ${healthResp.status}`);
  }
  const healthData = (healthResp.body || {}).data || {};
  const summaryObj = healthData.summary || {};
  if (Number(summaryObj.critical_resolve_errors_count || 0) > 0) {
    throw new Error('critical resolve errors found after import');
  }

  let govResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'sc.scene.governance.log',
        fields: ['id', 'action', 'trace_id', 'created_at'],
        domain: [['trace_id', '=', traceId], ['action', '=', 'package_import']],
        limit: 10,
      },
    },
    auth
  );
  if (govResp.status < 400 && !govResp.body.ok) {
    const errMsg = String(((govResp.body || {}).error || {}).message || '');
    if (errMsg.indexOf('未知模型: sc.scene.governance.log') >= 0) {
      govResp = await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'list',
            model: 'sc.audit.log',
            fields: ['id', 'event_code', 'action', 'trace_id', 'ts'],
            domain: [['trace_id', '=', traceId], ['event_code', '=', 'SCENE_GOVERNANCE_ACTION']],
            limit: 10,
          },
        },
        auth
      );
    }
  }
  writeJson(path.join(outDir, 'governance_log.log'), govResp);
  if (govResp.status >= 400 || !govResp.body.ok) {
    throw new Error(`governance log query failed: ${govResp.status}`);
  }
  const rows = ((((govResp.body || {}).data) || {}).records) || [];
  if (!Array.isArray(rows) || rows.length < 1) {
    throw new Error('missing package import governance log');
  }

  summary.push(`trace_id: ${traceId}`);
  summary.push(`imported_count: ${importData.summary.imported_count}`);
  summary.push(`renamed_count: ${importData.summary.renamed_count}`);
  summary.push(`critical_resolve_errors_count: ${summaryObj.critical_resolve_errors_count}`);
  summary.push(`governance_log_rows: ${rows.length}`);
  writeSummary(summary);

  log('PASS scene package import smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_package_import_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
