#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || process.env.SCENE_LOGIN || 'admin';
const PASSWORD =
  process.env.E2E_PASSWORD ||
  process.env.SCENE_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ALLOW_SKIP_UNKNOWN_INTENT = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.MY_WORK_SMOKE_ALLOW_SKIP || '').trim().toLowerCase()
);

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'my-work-smoke-v10_2', ts);

function log(msg) {
  console.log(`[fe_my_work_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function extractTraceId(body) {
  if (!body || typeof body !== 'object') return '';
  const meta = body.meta && typeof body.meta === 'object' ? body.meta : {};
  return String(meta.trace_id || meta.traceId || body.trace_id || body.traceId || '');
}

function assertIntentEnvelope(resp, intentName) {
  if (!resp || resp.status >= 400) {
    const status = resp && typeof resp.status !== 'undefined' ? resp.status : 0;
    throw new Error(`${intentName} failed: status=${status}`);
  }
  if (!resp.body || typeof resp.body !== 'object') {
    throw new Error(`${intentName} missing response body`);
  }
  if (resp.body.ok !== true) {
    throw new Error(`${intentName} missing ok=true envelope`);
  }
  if (!extractTraceId(resp.body)) {
    throw new Error(`${intentName} missing meta.trace_id`);
  }
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload || {});
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

function assertSortedById(items, dir) {
  let prev = null;
  for (const row of items || []) {
    const current = Number(row && row.id ? row.id : 0);
    if (prev !== null) {
      if (dir === 'asc' && current < prev) return false;
      if (dir === 'desc' && current > prev) return false;
    }
    prev = current;
  }
  return true;
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token) {
    const loginResp = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
      { 'X-Anonymous-Intent': '1' }
    );
    writeJson(path.join(outDir, 'login.log'), loginResp);
    assertIntentEnvelope(loginResp, 'login');
    token = (((loginResp.body || {}).data) || {}).token || '';
    if (!token) throw new Error('login response missing token');
  }

  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };

  const req1 = {
    intent: 'my.work.summary',
    params: {
      limit: 80,
      limit_each: 16,
      page: 1,
      page_size: 10,
      sort_by: 'id',
      sort_dir: 'desc',
      section: 'all',
      source: 'all',
      reason_code: 'all',
      search: '',
    },
  };
  const resp1 = await requestJson(intentUrl, req1, authHeader);
  writeJson(path.join(outDir, 'my_work_page1_desc.log'), resp1);
  if (resp1.status >= 400 || !resp1.body.ok) {
    const errMsg = String((((resp1.body || {}).error) || {}).message || '');
    if (errMsg.includes('Unknown intent: my.work.summary')) {
      if (ALLOW_SKIP_UNKNOWN_INTENT) {
        summary.push('status: SKIP');
        summary.push('reason: my.work.summary intent not registered in current DB');
        summary.push(`db: ${DB_NAME}`);
        writeSummary(summary);
        log('SKIP my-work smoke (intent not registered)');
        log(`artifacts: ${outDir}`);
        return;
      }
      throw new Error(
        'my.work.summary is not registered; run `make policy.ensure.extension_modules DB_NAME=<db>` ' +
          '(or set AUTO_FIX_EXTENSION_MODULES=1 for auto-fix + restart)'
      );
    }
    throw new Error(`my.work.summary page1 failed: status=${resp1.status} message=${errMsg || '-'}`);
  }
  assertIntentEnvelope(resp1, 'my.work.summary');
  const data1 = (resp1.body || {}).data || {};
  const filters1 = data1.filters || {};
  const items1 = Array.isArray(data1.items) ? data1.items : [];
  if (Number(filters1.page || 0) !== 1) throw new Error('page=1 not reflected');
  const reflectedPageSize = Number(filters1.page_size || 0);
  if (!Number.isFinite(reflectedPageSize) || reflectedPageSize <= 0) {
    throw new Error('page_size not reflected as positive number');
  }
  if (String(filters1.sort_by || '') !== 'id') throw new Error('sort_by=id not reflected');
  if (String(filters1.sort_dir || '') !== 'desc') throw new Error('sort_dir=desc not reflected');
  if (!assertSortedById(items1, 'desc')) throw new Error('items are not sorted by id desc');
  if (items1.length > reflectedPageSize) throw new Error('items length exceeds page_size');

  const totalPages = Math.max(1, Number(filters1.total_pages || 1));
  const targetPage = Math.min(2, totalPages);
  const req2 = {
    intent: 'my.work.summary',
    params: {
      limit: 80,
      limit_each: 16,
      page: targetPage,
      page_size: 10,
      sort_by: 'id',
      sort_dir: 'asc',
      section: 'all',
      source: 'all',
      reason_code: 'all',
      search: '',
    },
  };
  const resp2 = await requestJson(intentUrl, req2, authHeader);
  writeJson(path.join(outDir, 'my_work_page2_asc.log'), resp2);
  assertIntentEnvelope(resp2, 'my.work.summary');
  const data2 = (resp2.body || {}).data || {};
  const filters2 = data2.filters || {};
  const items2 = Array.isArray(data2.items) ? data2.items : [];
  if (Number(filters2.page || 0) !== targetPage) throw new Error('target page not reflected');
  const filteredCount2 = Number(filters2.filtered_count || 0);
  if (filteredCount2 > 0) {
    if (String(filters2.sort_dir || '') !== 'asc') throw new Error('sort_dir=asc not reflected');
    if (!assertSortedById(items2, 'asc')) throw new Error('items are not sorted by id asc');
  }
  const reflectedPageSize2 = Number(filters2.page_size || reflectedPageSize || 0);
  if (!Number.isFinite(reflectedPageSize2) || reflectedPageSize2 <= 0) {
    throw new Error('page_size not reflected on page2');
  }
  if (items2.length > reflectedPageSize2) throw new Error('items length exceeds page_size on page2');

  summary.push(`db: ${DB_NAME}`);
  summary.push(`page1_count: ${items1.length}`);
  summary.push(`page2_count: ${items2.length}`);
  summary.push(`page_size_reflected: ${reflectedPageSize}`);
  summary.push(`total_pages: ${totalPages}`);
  summary.push(`sort_check_desc: ok`);
  summary.push(`sort_check_asc: ${filteredCount2 > 0 ? 'ok' : 'skip(empty)'}`);
  writeSummary(summary);
  log('PASS my-work pagination/sort smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_my_work_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
