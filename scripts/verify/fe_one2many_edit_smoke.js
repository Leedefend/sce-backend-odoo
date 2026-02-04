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
const VIEW_TYPE = process.env.MVP_VIEW_TYPE || 'form';
const RECORD_ID = Number(process.env.RECORD_ID || 0);
const ONE2MANY_FIELD = process.env.ONE2MANY_FIELD || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-5', ts);

function log(msg) {
  console.log(`[fe_one2many_edit_smoke] ${msg}`);
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

function collectLayoutFields(layout) {
  const names = new Set();
  if (!layout || typeof layout !== 'object') return names;
  const pushField = (field) => {
    if (field && typeof field === 'object' && field.name) {
      names.add(field.name);
    }
  };
  const walkGroup = (group) => {
    if (!group || typeof group !== 'object') return;
    (group.fields || []).forEach(pushField);
    (group.sub_groups || []).forEach(walkGroup);
  };
  (layout.groups || []).forEach(walkGroup);
  (layout.notebooks || []).forEach((notebook) => {
    (notebook.pages || []).forEach((page) => {
      (page.groups || []).forEach(walkGroup);
    });
  });
  return names;
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

  log('load_view');
  const viewPayload = { intent: 'load_view', params: { model: MODEL, view_type: VIEW_TYPE } };
  const viewResp = await requestJson(intentUrl, viewPayload, authHeader);
  writeJson(path.join(outDir, 'load_view.log'), viewResp);
  if (viewResp.status >= 400 || !viewResp.body.ok) {
    throw new Error(`load_view failed: status=${viewResp.status}`);
  }

  const viewData = viewResp.body.data || {};
  const fields = viewData.fields || {};
  const layout = viewData.layout || {};
  const layoutFields = collectLayoutFields(layout);

  let fieldName = '';
  let descriptor = null;
  if (ONE2MANY_FIELD) {
    const candidate = fields[ONE2MANY_FIELD];
    const candidateType = candidate ? candidate.ttype || candidate.type : '';
    if (!candidate || candidateType !== 'one2many') {
      writeSummary([`one2many_field: ${ONE2MANY_FIELD}`, 'error: invalid one2many field']);
      throw new Error(`ONE2MANY_FIELD=${ONE2MANY_FIELD} not found or not one2many`);
    }
    fieldName = ONE2MANY_FIELD;
    descriptor = candidate;
  } else {
    const one2manyEntry = Object.entries(fields).find(([, desc]) => desc && (desc.ttype === 'one2many' || desc.type === 'one2many'));
    if (!one2manyEntry) {
      writeSummary(['one2many_field: none']);
      throw new Error('no one2many field found in view contract (set ONE2MANY_FIELD or MVP_MODEL)');
    }
    [fieldName, descriptor] = one2manyEntry;
  }

  const relation = descriptor.relation;
  const relationField = descriptor.relation_field;
  if (!relation || !relationField) {
    throw new Error('missing relation or relation_field for one2many');
  }
  const inLayout = layoutFields.has(fieldName);
  summary.push(`one2many_field: ${fieldName}`);
  summary.push(`relation: ${relation}`);
  summary.push(`relation_field: ${relationField}`);
  summary.push(`in_layout: ${inLayout ? 'true' : 'false'}`);
  if (!inLayout) {
    writeSummary(summary);
    throw new Error('one2many field not found in layout');
  }

  let targetId = RECORD_ID;
  if (!targetId) {
    log('api.data.list');
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

  log('api.data.list (relation)');
  const relListPayload = {
    intent: 'api.data',
    params: { op: 'list', model: relation, fields: ['id', 'name'], domain: [], limit: 1 },
  };
  const relListResp = await requestJson(intentUrl, relListPayload, authHeader);
  writeJson(path.join(outDir, 'relation_list.log'), relListResp);
  if (relListResp.status >= 400 || !relListResp.body.ok) {
    throw new Error(`relation list failed: status=${relListResp.status}`);
  }
  const relRecords = (relListResp.body.data || {}).records || [];
  const existingId = relRecords.length ? Number(relRecords[0].id) : 0;

  log('api.data.create (dry_run)');
  const createPayload = {
    intent: 'api.data.create',
    params: {
      model: relation,
      vals: { name: `Codex Task ${Date.now()}`, [relationField]: targetId },
      dry_run: 1,
    },
  };
  const createResp = await requestJson(intentUrl, createPayload, authHeader);
  writeJson(path.join(outDir, 'create.log'), createResp);
  if (createResp.status >= 400 || !createResp.body.ok) {
    throw new Error(`create failed: status=${createResp.status}`);
  }

  if (existingId) {
    log('api.data.write (dry_run)');
    const writePayload = {
      intent: 'api.data.write',
      params: {
        model: relation,
        ids: [existingId],
        vals: { name: `Codex Task Updated ${Date.now()}` },
        dry_run: 1,
      },
    };
    const writeResp = await requestJson(intentUrl, writePayload, authHeader);
    writeJson(path.join(outDir, 'write.log'), writeResp);
    if (writeResp.status >= 400 || !writeResp.body.ok) {
      throw new Error(`write failed: status=${writeResp.status}`);
    }

    log('api.data.unlink (dry_run)');
    const unlinkPayload = {
      intent: 'api.data.unlink',
      params: { model: relation, ids: [existingId], dry_run: 1 },
    };
    const unlinkResp = await requestJson(intentUrl, unlinkPayload, authHeader);
    writeJson(path.join(outDir, 'unlink.log'), unlinkResp);
    if (unlinkResp.status >= 400 || !unlinkResp.body.ok) {
      throw new Error(`unlink failed: status=${unlinkResp.status}`);
    }
  }

  summary.push(`record_id: ${targetId}`);
  summary.push(`relation_sample_id: ${existingId || 0}`);
  writeSummary(summary);

  log(`PASS one2many_edit field=${fieldName}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_one2many_edit_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
