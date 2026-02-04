#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

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
  console.log(`[fe_file_guard_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
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

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
    });
    if (bootstrapResp.status >= 400 || !bootstrapResp.body.ok) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    if (loginResp.status >= 400 || !loginResp.body.ok) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status}`);
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
    if (listResp.status >= 400 || !listResp.body.ok) {
      throw new Error(`list failed: status=${listResp.status}`);
    }
    const listRecords = (listResp.body.data || {}).records || [];
    if (!listRecords.length) {
      throw new Error('no records found for model');
    }
    targetId = Number(listRecords[0].id);
  }

  log('file.upload (deny)');
  const uploadPayload = {
    intent: 'file.upload',
    params: {
      model: 'res.users',
      res_id: 1,
      name: 'blocked.txt',
      mimetype: 'text/plain',
      data: Buffer.from('blocked').toString('base64'),
    },
  };
  const uploadResp = await requestJson(intentUrl, uploadPayload, authHeader);
  writeJson(path.join(outDir, 'upload_block.log'), uploadResp);
  if (uploadResp.status < 400) {
    throw new Error('expected upload blocked for res.users');
  }

  log('file.download (deny)');
  const attListPayload = {
    intent: 'api.data',
    params: {
      op: 'list',
      model: 'ir.attachment',
      fields: ['id', 'res_model'],
      domain: [['res_model', 'not in', ['project.project', 'project.task']]],
      limit: 1,
    },
  };
  const attListResp = await requestJson(intentUrl, attListPayload, authHeader);
  writeJson(path.join(outDir, 'attachment_list.log'), attListResp);
  if (attListResp.status >= 400 || !attListResp.body.ok) {
    throw new Error(`attachment list failed: status=${attListResp.status}`);
  }
  const attachments = (attListResp.body.data || {}).records || [];
  if (attachments.length) {
    const attId = attachments[0].id;
    const downloadPayload = { intent: 'file.download', params: { id: attId } };
    const downloadResp = await requestJson(intentUrl, downloadPayload, authHeader);
    writeJson(path.join(outDir, 'download_block.log'), downloadResp);
    if (downloadResp.status < 400) {
      throw new Error('expected download blocked for non-allowed attachment');
    }
  }

  log('PASS file guard');
  console.log(`[fe_file_guard_smoke] artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_file_guard_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
