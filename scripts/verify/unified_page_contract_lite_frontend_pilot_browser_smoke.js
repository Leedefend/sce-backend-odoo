#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireFromWeb = createRequire(path.join(process.cwd(), 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'cost1';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = process.env.LITE_PILOT_ACTION_ID || '506';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUIRED_DEV_SERVER_FLAG = 'VITE_LITE_CONTRACT_PILOT=1';

const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, '');
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'lite_frontend_pilot', ts);

function log(message) {
  console.log(`[lite_frontend_pilot_browser_smoke] ${message}`);
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

function fail(message) {
  const error = new Error(message);
  throw error;
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

async function run() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const consoleErrors = [];
  const pageErrors = [];
  const actionIntentRequests = [];
  const actionIntentResponses = [];
  let actionPhase = false;
  let loadContractSeen = false;
  let loadContractLitePreviewSeen = false;
  let uiContractActionPhaseCount = 0;

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
  });
  page.on('request', (request) => {
    if (!actionPhase || !isIntentRequest(request)) return;
    const payload = parseIntentPostData(request);
    const intent = pickIntent(payload);
    actionIntentRequests.push({ url: request.url(), intent, payload });
    if (intent === 'load_contract') loadContractSeen = true;
    if (intent === 'ui.contract') uiContractActionPhaseCount += 1;
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
    const litePreview = isLitePreviewResponse(body);
    if (litePreview) loadContractLitePreviewSeen = true;
    actionIntentResponses.push({ status: response.status(), intent, litePreview });
  });

  const summary = {
    ok: false,
    frontendUrl: FRONTEND_URL,
    dbName: DB_NAME,
    actionId: ACTION_ID,
    requiredDevServerFlag: REQUIRED_DEV_SERVER_FLAG,
    checks: {},
    actionIntentRequests: [],
    actionIntentResponses: [],
    consoleErrors: [],
    pageErrors: [],
  };

  try {
    log(`login ${LOGIN}@${DB_NAME}`);
    await fillLogin(page);

    await page.goto(`${FRONTEND_URL}/my-work?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);

    actionPhase = true;
    const actionUrl = `${FRONTEND_URL}/a/${encodeURIComponent(ACTION_ID)}?db=${encodeURIComponent(DB_NAME)}&lite_pilot_smoke=${Date.now()}`;
    log(`open ${actionUrl}`);
    await page.goto(actionUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);

    const rows = page.locator('.table table tbody tr');
    await rows.first().waitFor({ timeout: 45000 });
    const rowCount = await rows.count();
    const title = await page.locator('.list-title h2').first().textContent({ timeout: 5000 }).catch(() => '');
    const headerText = await page.locator('.table table thead').first().innerText({ timeout: 5000 }).catch(() => '');
    await page.screenshot({ path: path.join(outDir, 'project_tree_lite_pilot.png'), fullPage: true });

    summary.checks = {
      loadContractSeen,
      loadContractLitePreviewSeen,
      uiContractActionPhaseCount,
      rowCount,
      title: String(title || '').trim(),
      headerText: String(headerText || '').trim(),
    };
    summary.actionIntentRequests = actionIntentRequests.map((entry) => ({
      intent: entry.intent,
      payloadKeys: entry.payload && typeof entry.payload === 'object' ? Object.keys(entry.payload).sort() : [],
      contractMode: entry.payload && entry.payload.params ? entry.payload.params.contractMode : undefined,
      contractVersion: entry.payload && entry.payload.params ? entry.payload.params.contractVersion : undefined,
      entryPoint: entry.payload && entry.payload.params ? entry.payload.params.entryPoint : undefined,
    }));
    summary.actionIntentResponses = actionIntentResponses;
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;

    if (!loadContractSeen) fail('action route did not dispatch load_contract');
    if (!loadContractLitePreviewSeen) fail('load_contract did not return Lite v2.0 preview envelope');
    if (uiContractActionPhaseCount > 0) fail('action route fell back to ui.contract during Lite pilot');
    if (rowCount < 1) fail('project tree did not render rows');
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
    summary.actionIntentRequests = actionIntentRequests.map((entry) => ({
      intent: entry.intent,
      payloadKeys: entry.payload && typeof entry.payload === 'object' ? Object.keys(entry.payload).sort() : [],
      contractMode: entry.payload && entry.payload.params ? entry.payload.params.contractMode : undefined,
      contractVersion: entry.payload && entry.payload.params ? entry.payload.params.contractVersion : undefined,
      entryPoint: entry.payload && entry.payload.params ? entry.payload.params.entryPoint : undefined,
    }));
    summary.actionIntentResponses = actionIntentResponses;
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;
    await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true }).catch(() => undefined);
    writeJson(path.join(outDir, 'summary.json'), summary);
    await browser.close().catch(() => undefined);
    console.error(`[lite_frontend_pilot_browser_smoke] failed: ${summary.error}`);
    console.error(`[lite_frontend_pilot_browser_smoke] report: ${path.join(outDir, 'summary.json')}`);
    process.exitCode = 1;
  }
}

run();
