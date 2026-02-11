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
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = Number(process.env.RECORD_ID || 0);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-6', ts);

function log(msg) {
  console.log(`[fe_write_conflict_smoke] ${msg}`);
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

  let targetId = RECORD_ID;
  if (!targetId) {
    log('api.data.list');
    const listPayload = {
      intent: 'api.data',
      params: { op: 'list', model: MODEL, fields: ['id'], domain: [], limit: 1 },
    };
    const listResp = await requestJson(intentUrl, listPayload, authHeader);
    writeJson(path.join(outDir, 'list.log'), listResp);
    assertIntentEnvelope(listResp, 'api.data');
    const listRecords = (listResp.body.data || {}).records || [];
    if (!listRecords.length) {
      throw new Error('no records found for model');
    }
    targetId = Number(listRecords[0].id);
  }

  log('api.data.read');
  const readPayload = {
    intent: 'api.data',
    params: { op: 'read', model: MODEL, ids: [targetId], fields: ['id', 'name', 'write_date'] },
  };
  const readResp = await requestJson(intentUrl, readPayload, authHeader);
  writeJson(path.join(outDir, 'read.log'), readResp);
  assertIntentEnvelope(readResp, 'api.data');
  const readData = (readResp.body && readResp.body.data) || {};
  const records = Array.isArray(readData.records) ? readData.records : [];
  const record = records[0] || {};
  const originalWriteDate = record.write_date || '';
  if (!originalWriteDate) {
    throw new Error('missing write_date');
  }

  log('api.data.write (conflict)');
  const conflictPayload = {
    intent: 'api.data.write',
    params: {
      model: MODEL,
      ids: [targetId],
      vals: { name: `Codex Conflict Retry ${Date.now()}` },
      if_match: `stale-${originalWriteDate}`,
    },
  };
  const conflictResp = await requestJson(intentUrl, conflictPayload, authHeader);
  writeJson(path.join(outDir, 'conflict.log'), conflictResp);

  summary.push(`record_id: ${targetId}`);
  summary.push(`conflict_status: ${conflictResp.status}`);
  summary.push(`error_code: ${(conflictResp.body && conflictResp.body.error && conflictResp.body.error.code) || '-'}`);

  writeSummary(summary);

  if (conflictResp.status !== 409) {
    throw new Error(`expected 409, got ${conflictResp.status}`);
  }

  log('PASS write conflict');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_write_conflict_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
