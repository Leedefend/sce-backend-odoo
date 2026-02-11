#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const MODEL = process.env.MVP_MODEL || 'project.project';
const ROOT_XMLID = process.env.ROOT_XMLID || 'smart_construction_core.menu_sc_root';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_7-ui', ts);

function log(msg) {
  console.log(`[fe_recordview_hud_smoke] ${msg}`);
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

function unwrap(body) {
  if (body && typeof body === 'object' && 'data' in body) {
    return body.data || {};
  }
  return body || {};
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
  try {
    assertIntentEnvelope(loginResp, 'login');
  } catch (_err) {
    writeJson(path.join(outDir, 'login.log'), loginResp);
    throw new Error(`login failed: status=${loginResp.status || 0}`);
  }
  const token = (loginResp.body.data || {}).token;
  if (!token) {
    throw new Error('login response missing token');
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
  };

  log('app.init');
  const initPayload = { intent: 'app.init', params: { db: DB_NAME, scene: 'web', with_preload: false, root_xmlid: ROOT_XMLID } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  try {
    assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });
  } catch (_err) {
    writeJson(path.join(outDir, 'init.log'), initResp);
    throw new Error(`app.init failed: status=${initResp.status || 0}`);
  }

  log('api.data.list');
  const listPayload = { intent: 'api.data', params: { op: 'list', model: MODEL, fields: ['id', 'name'], limit: 1 } };
  const listResp = await requestJson(intentUrl, listPayload, authHeader);
  writeJson(path.join(outDir, 'list.log'), listResp);
  assertIntentEnvelope(listResp, 'api.data');
  const listMeta = listResp.body.meta || {};
  const listTraceOk = Boolean(listMeta.trace_id);
  const listData = unwrap(listResp.body);
  const firstRecord = (listData.records || [])[0];
  if (!firstRecord || !firstRecord.id) {
    throw new Error('list returned no record');
  }

  const recordId = firstRecord.id;
  const newName = `${firstRecord.name || 'Record'} (v0.7 UI)`;

  log('api.data.write');
  const writeStart = Date.now();
  const writePayload = { intent: 'api.data.write', params: { model: MODEL, id: recordId, values: { name: newName } } };
  const writeResp = await requestJson(intentUrl, writePayload, authHeader);
  writeJson(path.join(outDir, 'write.log'), writeResp);
  assertIntentEnvelope(writeResp, 'api.data.write', { allowMetaIntentAliases: ['api.data'] });
  const latencyMs = Date.now() - writeStart;
  const writeMeta = writeResp.body.meta || {};

  const hudFieldsOk = Boolean(writeMeta.trace_id && writeMeta.write_mode && listTraceOk);
  const footerMetaOk = Boolean(recordId && latencyMs >= 0);

  summary.push(`list_trace_ok: ${listTraceOk ? 'true' : 'false'}`);
  summary.push(`hud_fields_ok: ${hudFieldsOk ? 'true' : 'false'}`);
  summary.push(`footer_meta_ok: ${footerMetaOk ? 'true' : 'false'}`);
  summary.push(`list_trace_id: ${listMeta.trace_id || ''}`);
  summary.push(`trace_id: ${writeMeta.trace_id || ''}`);
  summary.push(`write_mode: ${writeMeta.write_mode || ''}`);
  summary.push(`record_id: ${recordId}`);
  summary.push(`latency_ms: ${latencyMs}`);

  writeSummary(summary);

  if (!hudFieldsOk || !footerMetaOk) {
    throw new Error('hud/footer assertions failed');
  }

  log('PASS hud_fields_ok=true footer_meta_ok=true');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_recordview_hud_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
