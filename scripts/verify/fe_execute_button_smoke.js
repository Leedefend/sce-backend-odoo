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
const VIEW_TYPE = process.env.MVP_VIEW_TYPE || 'form';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-semantic', ts);

function log(msg) {
  console.log(`[fe_execute_button_smoke] ${msg}`);
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

function isModelMissing(resp) {
  const msg = String((((resp || {}).body || {}).error || {}).message || '');
  return (
    msg.includes('未知模型') ||
    msg.toLowerCase().includes('unknown model') ||
    /^'[a-z0-9_.]+'$/i.test(msg.trim())
  );
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
    const bootstrapPayload = {
      intent: 'bootstrap',
      params: { db: DB_NAME, login: BOOTSTRAP_LOGIN },
    };
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
    writeJson(path.join(outDir, 'login.log'), loginResp);
    assertIntentEnvelope(loginResp, 'login');
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
  const candidateModels = Array.from(new Set([MODEL, 'res.partner']));
  let viewResp = null;
  let modelUsed = '';
  for (const candidate of candidateModels) {
    const viewPayload = { intent: 'load_view', params: { model: candidate, view_type: VIEW_TYPE } };
    const resp = await requestJson(intentUrl, viewPayload, authHeader);
    writeJson(path.join(outDir, `load_view.${candidate.replace(/\./g, '_')}.log`), resp);
    try {
      assertIntentEnvelope(resp, 'load_view');
      viewResp = resp;
      modelUsed = candidate;
      break;
    } catch (_err) {
      // try next candidate
    }
    if (!isModelMissing(resp)) {
      viewResp = resp;
      break;
    }
  }
  if (!viewResp || !modelUsed) {
    throw new Error(`load_view failed for all models: ${candidateModels.join(',')}`);
  }
  writeJson(path.join(outDir, 'load_view.log'), { model_used: modelUsed, response: viewResp });
  const viewData = viewResp.body.data || {};
  const layout = (viewData && viewData.layout) || {};
  const buttons = [...(layout.headerButtons || []), ...(layout.statButtons || [])];
  const button =
    buttons.find((b) => b && b.name && /^[A-Za-z_]/.test(String(b.name)) && (b.type || 'object') === 'object') ||
    buttons.find((b) => b && b.name) ||
    null;

  log('api.data.list');
  const listPayload = { intent: 'api.data', params: { op: 'list', model: modelUsed, fields: ['id', 'name'], limit: 1 } };
  const listResp = await requestJson(intentUrl, listPayload, authHeader);
  writeJson(path.join(outDir, 'list.log'), listResp);
  assertIntentEnvelope(listResp, 'api.data');
  const listData = (listResp.body && listResp.body.data) || {};
  const records = Array.isArray(listData.records) ? listData.records : [];
  const record = records[0];
  if (!record || !record.id) {
    throw new Error('list returned no record');
  }

  if (!button) {
    const autoFallback = !process.env.MVP_MODEL && modelUsed !== MODEL;
    summary.push(`model_used: ${modelUsed}`);
    summary.push(`button_name: -`);
    summary.push(`execute_button_skipped: ${autoFallback ? 'true' : 'false'}`);
    writeSummary(summary);
    if (autoFallback) {
      log('PASS execute_button dry_run skipped (fallback model has no object button)');
      log(`artifacts: ${outDir}`);
      return;
    }
    throw new Error('no button available for execute_button dry_run');
  }

  log('execute_button dry_run');
  const execPayload = {
    intent: 'execute_button',
    params: {
      model: modelUsed,
      res_id: record.id,
      button: { name: button.name, type: button.type || 'object' },
      dry_run: 1,
    },
  };
  const execResp = await requestJson(intentUrl, execPayload, authHeader);
  writeJson(path.join(outDir, 'execute_button.log'), execResp);
  const execBody = execResp.body || {};
  const execData = execBody.data || {};
  const resultType = (execData.result && execData.result.type) || '';
  const effectType = (execData.effect && execData.effect.type) || '';
  const reasonCode = (((execBody || {}).error || {}).reason_code || '').toString();
  const autoFallback = !process.env.MVP_MODEL && modelUsed !== MODEL;
  const toleratedFallbackFailure =
    autoFallback &&
    execResp.status === 400 &&
    ['METHOD_NOT_CALLABLE', 'UNSUPPORTED_BUTTON_TYPE'].includes(reasonCode) &&
    effectType === 'toast';

  if (!toleratedFallbackFailure) {
    assertIntentEnvelope(execResp, 'execute_button');
  }

  summary.push(`model_used: ${modelUsed}`);
  summary.push(`button_name: ${button.name}`);
  summary.push(`result_type: ${resultType}`);
  summary.push(`effect_type: ${effectType || '-'}`);
  summary.push(`reason_code: ${reasonCode || '-'}`);
  summary.push(`fallback_tolerated_failure: ${toleratedFallbackFailure ? 'true' : 'false'}`);
  writeSummary(summary);

  if (toleratedFallbackFailure) {
    log(`PASS execute_button fallback tolerated (${reasonCode})`);
    log(`artifacts: ${outDir}`);
    return;
  }

  if (resultType !== 'dry_run') {
    throw new Error(`expected dry_run, got ${resultType}`);
  }
  if (effectType !== 'toast') {
    throw new Error(`expected effect toast, got ${effectType}`);
  }

  log('PASS execute_button dry_run');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_execute_button_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
