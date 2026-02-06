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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-health-pagination-v10_4', ts);

function log(msg) {
  console.log(`[fe_scene_health_pagination_smoke] ${msg}`);
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
  const traceId = `scene_health_page_${Date.now()}`;
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

  const full1 = await requestJson(
    intentUrl,
    { intent: 'scene.health', params: { mode: 'full', limit: 1, offset: 0 } },
    auth
  );
  writeJson(path.join(outDir, 'full_limit_1_offset_0.log'), full1);
  if (full1.status >= 400 || !full1.body.ok) throw new Error(`full1 failed: ${full1.status}`);
  const fullData1 = (full1.body || {}).data || {};
  if (!('details' in fullData1)) throw new Error('full mode missing details');

  const details1 = fullData1.details || {};
  for (const key of ['resolve_errors', 'drift', 'debt']) {
    const rows = details1[key];
    if (!Array.isArray(rows)) throw new Error(`details.${key} not array`);
    if (rows.length > 1) throw new Error(`limit not applied for ${key}`);
  }

  const full2 = await requestJson(
    intentUrl,
    { intent: 'scene.health', params: { mode: 'full', limit: 1, offset: 1 } },
    auth
  );
  writeJson(path.join(outDir, 'full_limit_1_offset_1.log'), full2);
  if (full2.status >= 400 || !full2.body.ok) throw new Error(`full2 failed: ${full2.status}`);
  const fullData2 = (full2.body || {}).data || {};
  const query2 = fullData2.query || {};
  if (String(query2.offset || '') !== '1') throw new Error('offset not reflected in query');

  const summaryMode = await requestJson(
    intentUrl,
    { intent: 'scene.health', params: { mode: 'summary', since: '2026-01-01T00:00:00Z' } },
    auth
  );
  writeJson(path.join(outDir, 'summary_mode.log'), summaryMode);
  if (summaryMode.status >= 400 || !summaryMode.body.ok) throw new Error(`summary mode failed: ${summaryMode.status}`);
  const summaryData = (summaryMode.body || {}).data || {};
  if ('details' in summaryData) throw new Error('summary mode should not return details');

  summary.push(`trace_id: ${traceId}`);
  summary.push(`full_limit_1_offset_0: ok`);
  summary.push(`full_limit_1_offset_1: ok`);
  summary.push(`summary_mode_no_details: ok`);
  writeSummary(summary);
  log('PASS scene health pagination');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_health_pagination_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
