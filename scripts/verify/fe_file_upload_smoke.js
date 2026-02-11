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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-5', ts);

function log(msg) {
  console.log(`[fe_file_upload_smoke] ${msg}`);
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
    log('api.data.list (model)');
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

  log('file.upload');
  const payload = {
    intent: 'file.upload',
    params: {
      model: MODEL,
      res_id: targetId,
      name: `codex-attach-${Date.now()}.txt`,
      mimetype: 'text/plain',
      data: Buffer.from(`codex-upload-${Date.now()}`).toString('base64'),
    },
  };
  const uploadResp = await requestJson(intentUrl, payload, authHeader);
  writeJson(path.join(outDir, 'upload.log'), uploadResp);
  assertIntentEnvelope(uploadResp, 'file.upload');

  const attachmentId = (uploadResp.body.data || {}).id;
  if (!attachmentId) {
    throw new Error('upload response missing id');
  }

  log('file.download');
  const downloadPayload = { intent: 'file.download', params: { id: attachmentId } };
  const downloadResp = await requestJson(intentUrl, downloadPayload, authHeader);
  writeJson(path.join(outDir, 'download.log'), downloadResp);
  assertIntentEnvelope(downloadResp, 'file.download');

  const downloadData = downloadResp.body.data || {};
  if (!downloadData.datas) {
    throw new Error('download response missing datas');
  }

  summary.push(`record_id: ${targetId}`);
  summary.push(`attachment_id: ${attachmentId}`);
  writeSummary(summary);

  log(`PASS upload id=${attachmentId}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_file_upload_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
