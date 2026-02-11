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
const ROOT_XMLID = process.env.ROOT_XMLID || 'smart_construction_core.menu_sc_root';
const MODEL = process.env.MVP_MODEL || 'project.project';
const CREATE_NAME = process.env.CREATE_NAME || 'Portal Shell v0.6';
const UPDATE_NAME = process.env.UPDATE_NAME || 'Portal Shell v0.6 Updated';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_6', ts);

function log(msg) {
  console.log(`[fe_mvp_write_smoke] ${msg}`);
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

function isModelMissing(resp) {
  const msg = String((((resp || {}).body || {}).error || {}).message || '');
  return msg.includes('未知模型') || msg.toLowerCase().includes('unknown model');
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

  log('api.data.create');
  const candidateModels = Array.from(new Set([MODEL, 'res.partner']));
  let createResp = null;
  let createIntentUsed = '';
  let recordId = 0;
  let modelUsed = '';
  for (const candidate of candidateModels) {
    const primaryPayload = { intent: 'api.data.create', params: { model: candidate, values: { name: CREATE_NAME } } };
    const primaryResp = await requestJson(intentUrl, primaryPayload, authHeader);
    writeJson(path.join(outDir, `write_create.${candidate.replace(/\./g, '_')}.api_data_create.log`), primaryResp);
    if (primaryResp.status < 400 && (primaryResp.body || {}).ok === true) {
      const data = unwrap(primaryResp.body);
      if (data.id) {
        createResp = primaryResp;
        createIntentUsed = 'api.data.create';
        recordId = data.id;
        modelUsed = candidate;
        break;
      }
    }
    const fallbackPayload = {
      intent: 'api.data',
      params: { op: 'create', model: candidate, values: { name: CREATE_NAME }, sudo: true },
    };
    const fallbackResp = await requestJson(intentUrl, fallbackPayload, authHeader);
    writeJson(path.join(outDir, `write_create.${candidate.replace(/\./g, '_')}.api_data.log`), fallbackResp);
    if (fallbackResp.status < 400 && (fallbackResp.body || {}).ok === true) {
      const data = unwrap(fallbackResp.body);
      if (data.id) {
        createResp = fallbackResp;
        createIntentUsed = 'api.data';
        recordId = data.id;
        modelUsed = candidate;
        break;
      }
    }
    if (!isModelMissing(primaryResp) && !isModelMissing(fallbackResp)) {
      // Non-model-related failure: stop early and surface it.
      createResp = fallbackResp;
      createIntentUsed = 'api.data';
      break;
    }
  }
  writeJson(path.join(outDir, 'write_create.log'), { model_used: modelUsed, intent_used: createIntentUsed, response: createResp });
  if (!createResp || !recordId || !modelUsed) {
    throw new Error('create failed for all candidate models');
  }
  assertIntentEnvelope(createResp, createIntentUsed, { allowMetaIntentAliases: ['api.data.create', 'api.data'] });
  summary.push(`model_used: ${modelUsed}`);

  log('api.data.write invalid field');
  const invalidPayload = { intent: 'api.data.write', params: { model: modelUsed, id: recordId, values: { __illegal_field: 'x' } } };
  let invalidResp = await requestJson(intentUrl, invalidPayload, authHeader);
  let invalidIntentUsed = 'api.data.write';
  if (invalidResp.status === 403 || invalidResp.status === 404) {
    const fallbackPayload = { intent: 'api.data', params: { op: 'write', model: modelUsed, ids: [recordId], values: { __illegal_field: 'x' }, sudo: true } };
    invalidResp = await requestJson(intentUrl, fallbackPayload, authHeader);
    invalidIntentUsed = 'api.data';
  }
  writeJson(path.join(outDir, 'write_invalid.log'), { intent_used: invalidIntentUsed, response: invalidResp });
  const invalidOk = Boolean((invalidResp.body && invalidResp.body.ok === false) || invalidResp.status >= 400);
  summary.push(`write_invalid_ok: ${invalidOk ? 'true' : 'false'}`);

  log('api.data.write');
  const writePayload = { intent: 'api.data.write', params: { model: modelUsed, id: recordId, values: { name: UPDATE_NAME } } };
  let writeResp = await requestJson(intentUrl, writePayload, authHeader);
  let writeIntentUsed = 'api.data.write';
  if (writeResp.status === 403 || writeResp.status === 404) {
    const fallbackPayload = { intent: 'api.data', params: { op: 'write', model: modelUsed, ids: [recordId], values: { name: UPDATE_NAME }, sudo: true } };
    writeResp = await requestJson(intentUrl, fallbackPayload, authHeader);
    writeIntentUsed = 'api.data';
  }
  writeJson(path.join(outDir, 'write_update.log'), { intent_used: writeIntentUsed, response: writeResp });
  assertIntentEnvelope(writeResp, writeIntentUsed, { allowMetaIntentAliases: ['api.data.write', 'api.data'] });
  const writeMeta = writeResp.body.meta || {};
  const writeTraceId = writeMeta.trace_id || '';

  log('api.data.read');
  const readPayload = { intent: 'api.data', params: { op: 'read', model: modelUsed, ids: [recordId], fields: ['id', 'name'] } };
  const readResp = await requestJson(intentUrl, readPayload, authHeader);
  writeJson(path.join(outDir, 'read_back.log'), readResp);
  assertIntentEnvelope(readResp, 'api.data');
  const readData = unwrap(readResp.body);
  const record = (readData.records || [])[0] || {};
  const readBackMatch = record.name === UPDATE_NAME;

  summary.push(`write_status: ok`);
  summary.push(`read_back_match: ${readBackMatch ? 'true' : 'false'}`);
  summary.push(`trace_id: ${writeTraceId}`);
  summary.push(`record_id: ${recordId}`);

  writeSummary(summary);

  if (!readBackMatch || !invalidOk) {
    throw new Error('write smoke assertions failed');
  }

  log(`PASS write_status=ok read_back_match=${readBackMatch}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_mvp_write_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
