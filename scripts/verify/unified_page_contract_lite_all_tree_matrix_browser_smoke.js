#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { createRequire } = require('module');

const requireFromWeb = createRequire(path.join(process.cwd(), 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5176';
const API_BASE_URL = process.env.E2E_BASE_URL || process.env.API_BASE_URL || 'http://127.0.0.1:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'cost1';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MATRIX_LIMIT = Number(process.env.LITE_ALL_TREE_MATRIX_LIMIT || 8);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUIRED_DEV_SERVER_FLAG = 'VITE_LITE_CONTRACT_ROLLOUT=all_tree';

const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, '');
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'lite_all_tree_matrix_rollout', ts);

function log(message) {
  console.log(`[lite_all_tree_matrix_browser_smoke] ${message}`);
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

function fail(message) {
  throw new Error(message);
}

function requestJson(baseUrl, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL('/api/v1/intent', baseUrl);
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
      res.on('data', (chunk) => { data += chunk; });
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
  if (body && typeof body === 'object' && body.data && typeof body.data === 'object') return body.data;
  return body || {};
}

function collectActionIds(nodes, out = new Set()) {
  (nodes || []).forEach((node) => {
    const actionId = Number(node && node.meta ? node.meta.action_id || 0 : 0);
    if (Number.isFinite(actionId) && actionId > 0) out.add(actionId);
    if (node && Array.isArray(node.children)) collectActionIds(node.children, out);
  });
  return out;
}

function parseIntentPostData(request) {
  const postData = request.postData();
  if (!postData) return null;
  try {
    return JSON.parse(postData);
  } catch {
    return null;
  }
}

function pickIntent(payload) {
  if (!payload || typeof payload !== 'object') return '';
  return String(payload.intent || payload.name || '');
}

function isIntentRequest(request) {
  return request.url().includes('/api/v1/intent');
}

function isLitePreviewResponse(body) {
  if (!body || typeof body !== 'object') return false;
  const envelope = body.lite_preview
    || (body.data && typeof body.data === 'object' ? body.data.lite_preview : null)
    || (body.data && body.data.data && typeof body.data.data === 'object' ? body.data.data.lite_preview : null);
  if (!envelope || typeof envelope !== 'object') return false;
  return envelope.payloadType === 'lite_contract'
    && envelope.contractVersion === '2.0.0'
    && envelope.payload
    && typeof envelope.payload === 'object';
}

function summarizeIntentRequest(entry) {
  return {
    intent: entry.intent,
    op: entry.payload && entry.payload.params ? entry.payload.params.op : undefined,
    actionId: entry.payload && entry.payload.params ? entry.payload.params.action_id : undefined,
    contractMode: entry.payload && entry.payload.params ? entry.payload.params.contractMode : undefined,
    contractVersion: entry.payload && entry.payload.params ? entry.payload.params.contractVersion : undefined,
    entryPoint: entry.payload && entry.payload.params ? entry.payload.params.entryPoint : undefined,
  };
}

async function discoverMatrix() {
  log(`discover matrix from ${API_BASE_URL}`);
  const loginResp = await requestJson(API_BASE_URL, {
    intent: 'login',
    params: { db: DB_NAME, login: LOGIN, password: PASSWORD },
  }, { 'X-Anonymous-Intent': '1' });
  if (loginResp.status >= 400 || !unwrap(loginResp.body).token) {
    fail(`login failed during matrix discovery: status=${loginResp.status}`);
  }
  const token = unwrap(loginResp.body).token;
  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const initResp = await requestJson(API_BASE_URL, {
    intent: 'system.init',
    params: { db: DB_NAME, with_preload: false },
  }, authHeader);
  if (initResp.status >= 400) fail(`system.init failed during matrix discovery: status=${initResp.status}`);
  const actionIds = Array.from(collectActionIds(unwrap(initResp.body).nav || []));
  const rows = [];
  for (const actionId of actionIds) {
    const contractResp = await requestJson(API_BASE_URL, {
      intent: 'ui.contract',
      params: { db: DB_NAME, op: 'action_open', action_id: actionId },
    }, authHeader);
    if (contractResp.status >= 400) {
      rows.push({ actionId, expected: 'error', status: contractResp.status });
      continue;
    }
    const contract = unwrap(contractResp.body);
    const viewType = String((contract.head && contract.head.view_type) || contract.view_type || '').trim().toLowerCase();
    const model = String((contract.head && contract.head.model) || contract.model || '').trim();
    const expected = viewType === 'tree' || viewType === 'list' ? 'lite' : 'legacy';
    rows.push({ actionId, expected, viewType, model });
  }

  const lite = rows.filter((row) => row.expected === 'lite').slice(0, MATRIX_LIMIT);
  const legacy = rows.filter((row) => row.expected === 'legacy').slice(0, MATRIX_LIMIT);
  if (!lite.length) fail('matrix discovery found no tree/list action');
  if (!legacy.length) fail('matrix discovery found no non-tree action');
  return { discovered: rows, cases: [...lite, ...legacy] };
}

async function fillLogin(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
  const inputs = page.locator('form input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.locator('form button[type="submit"]').click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
}

async function runCase(page, row, actionIntentRequests, actionIntentResponses, summary) {
  const requestStart = actionIntentRequests.length;
  const responseStart = actionIntentResponses.length;
  const actionUrl = `${FRONTEND_URL}/a/${encodeURIComponent(row.actionId)}?db=${encodeURIComponent(DB_NAME)}&lite_all_tree_matrix_smoke=${Date.now()}`;
  log(`open action=${row.actionId} expected=${row.expected} view=${row.viewType}`);
  await page.goto(actionUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);
  await page.screenshot({ path: path.join(outDir, `action_${row.actionId}_${row.expected}.png`), fullPage: true });

  const requests = actionIntentRequests.slice(requestStart);
  const responses = actionIntentResponses.slice(responseStart);
  const loadContractCount = requests.filter((entry) => entry.intent === 'load_contract').length;
  const uiContractCount = requests.filter((entry) => entry.intent === 'ui.contract').length;
  const litePreviewCount = responses.filter((entry) => entry.intent === 'load_contract' && entry.litePreview).length;
  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  const rows = page.locator('.table table tbody tr');
  const rowCount = await rows.count().catch(() => 0);

  const result = {
    ...row,
    loadContractCount,
    uiContractCount,
    litePreviewCount,
    rowCount,
    bodyTextLength: String(bodyText || '').trim().length,
  };
  summary.results.push(result);

  if (row.expected === 'lite') {
    if (loadContractCount < 1) fail(`action ${row.actionId} did not dispatch load_contract`);
    if (litePreviewCount < 1) fail(`action ${row.actionId} did not receive Lite preview`);
    if (uiContractCount > 1) fail(`action ${row.actionId} repeatedly called ui.contract`);
    if (rowCount < 1) fail(`action ${row.actionId} Lite page rendered no rows`);
  } else {
    if (loadContractCount > 0) fail(`legacy action ${row.actionId} dispatched load_contract`);
    if (uiContractCount < 1) fail(`legacy action ${row.actionId} did not use ui.contract`);
    if (result.bodyTextLength < 1) fail(`legacy action ${row.actionId} rendered blank page`);
  }
}

async function run() {
  fs.mkdirSync(outDir, { recursive: true });
  const matrix = await discoverMatrix();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const consoleErrors = [];
  const pageErrors = [];
  const actionIntentRequests = [];
  const actionIntentResponses = [];
  let actionPhase = false;

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
  });
  page.on('request', (request) => {
    if (!actionPhase || !isIntentRequest(request)) return;
    const payload = parseIntentPostData(request);
    actionIntentRequests.push({ url: request.url(), intent: pickIntent(payload), payload });
  });
  page.on('response', async (response) => {
    const request = response.request();
    if (!actionPhase || !isIntentRequest(request)) return;
    const payload = parseIntentPostData(request);
    const intent = pickIntent(payload);
    if (intent !== 'load_contract') return;
    let body = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    actionIntentResponses.push({ status: response.status(), intent, litePreview: isLitePreviewResponse(body) });
  });

  const summary = {
    ok: false,
    frontendUrl: FRONTEND_URL,
    apiBaseUrl: API_BASE_URL,
    dbName: DB_NAME,
    requiredDevServerFlag: REQUIRED_DEV_SERVER_FLAG,
    discovered: matrix.discovered,
    cases: matrix.cases,
    results: [],
    actionIntentRequests: [],
    actionIntentResponses: [],
    consoleErrors: [],
    pageErrors: [],
  };

  try {
    log(`browser login ${LOGIN}@${DB_NAME}`);
    await fillLogin(page);
    await page.goto(`${FRONTEND_URL}/my-work?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
    actionPhase = true;

    for (const row of matrix.cases) {
      await runCase(page, row, actionIntentRequests, actionIntentResponses, summary);
    }

    summary.actionIntentRequests = actionIntentRequests.map(summarizeIntentRequest);
    summary.actionIntentResponses = actionIntentResponses;
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;
    if (consoleErrors.length) fail('browser console errors detected');
    if (pageErrors.length) fail('browser page errors detected');
    summary.ok = true;
    writeJson(path.join(outDir, 'summary.json'), summary);
    log('passed');
    log(`report: ${path.join(outDir, 'summary.json')}`);
    await browser.close();
  } catch (err) {
    summary.ok = false;
    summary.error = err && err.message ? err.message : String(err);
    summary.actionIntentRequests = actionIntentRequests.map(summarizeIntentRequest);
    summary.actionIntentResponses = actionIntentResponses;
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;
    await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true }).catch(() => undefined);
    writeJson(path.join(outDir, 'summary.json'), summary);
    await browser.close().catch(() => undefined);
    console.error(`[lite_all_tree_matrix_browser_smoke] failed: ${summary.error}`);
    console.error(`[lite_all_tree_matrix_browser_smoke] report: ${path.join(outDir, 'summary.json')}`);
    process.exitCode = 1;
  }
}

run();
