#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireFromWeb = createRequire(path.join(process.cwd(), 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5176';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'cost1';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ACTION_ID = process.env.LITE_ALL_TREE_LEGACY_ACTION_ID || '642';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REQUIRED_DEV_SERVER_FLAG = 'VITE_LITE_CONTRACT_ROLLOUT=all_tree';

const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, '');
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'lite_all_tree_legacy_rollout', ts);

function log(message) {
  console.log(`[lite_all_tree_legacy_browser_smoke] ${message}`);
}

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

function fail(message) {
  throw new Error(message);
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

function summarizeIntentRequest(entry) {
  return {
    intent: entry.intent,
    payloadKeys: entry.payload && typeof entry.payload === 'object' ? Object.keys(entry.payload).sort() : [],
    op: entry.payload && entry.payload.params ? entry.payload.params.op : undefined,
    actionId: entry.payload && entry.payload.params ? entry.payload.params.action_id : undefined,
    contractMode: entry.payload && entry.payload.params ? entry.payload.params.contractMode : undefined,
    contractVersion: entry.payload && entry.payload.params ? entry.payload.params.contractVersion : undefined,
    entryPoint: entry.payload && entry.payload.params ? entry.payload.params.entryPoint : undefined,
  };
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

  const summary = {
    ok: false,
    frontendUrl: FRONTEND_URL,
    dbName: DB_NAME,
    actionId: ACTION_ID,
    requiredDevServerFlag: REQUIRED_DEV_SERVER_FLAG,
    checks: {},
    actionIntentRequests: [],
    consoleErrors: [],
    pageErrors: [],
  };

  try {
    log(`login ${LOGIN}@${DB_NAME}`);
    await fillLogin(page);

    await page.goto(`${FRONTEND_URL}/my-work?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);

    actionPhase = true;
    const actionUrl = `${FRONTEND_URL}/a/${encodeURIComponent(ACTION_ID)}?db=${encodeURIComponent(DB_NAME)}&lite_all_tree_legacy_smoke=${Date.now()}`;
    log(`open ${actionUrl}`);
    await page.goto(actionUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);

    const shellText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    await page.screenshot({ path: path.join(outDir, `action_${ACTION_ID}_legacy.png`), fullPage: true });

    const loadContractCount = actionIntentRequests.filter((entry) => entry.intent === 'load_contract').length;
    const uiContractActionPhaseCount = actionIntentRequests.filter((entry) => entry.intent === 'ui.contract').length;
    const apiDataCount = actionIntentRequests.filter((entry) => entry.intent === 'api.data').length;

    summary.checks = {
      loadContractCount,
      uiContractActionPhaseCount,
      apiDataCount,
      bodyTextLength: String(shellText || '').trim().length,
    };
    summary.actionIntentRequests = actionIntentRequests.map(summarizeIntentRequest);
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;

    if (loadContractCount > 0) fail('non-tree action dispatched load_contract under all_tree rollout');
    if (uiContractActionPhaseCount < 1) fail('non-tree action did not stay on legacy ui.contract');
    if (String(shellText || '').trim().length < 1) fail('non-tree legacy action rendered blank page');
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
    summary.consoleErrors = consoleErrors;
    summary.pageErrors = pageErrors;
    await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true }).catch(() => undefined);
    writeJson(path.join(outDir, 'summary.json'), summary);
    await browser.close().catch(() => undefined);
    console.error(`[lite_all_tree_legacy_browser_smoke] failed: ${summary.error}`);
    console.error(`[lite_all_tree_legacy_browser_smoke] report: ${path.join(outDir, 'summary.json')}`);
    process.exitCode = 1;
  }
}

run();
