#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = Number(process.env.RECORD_ID || 771);
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-navigation-recovery', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function formUrl(recordId = RECORD_ID) {
  return `${FRONTEND_URL}/r/${MODEL}/${recordId}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`;
}

function listUrl() {
  return `${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}`;
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  await submitLoginForm(page);
}

async function submitLoginForm(page) {
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function clearBrowserAuth(page) {
  await page.context().clearCookies();
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const shell = document.querySelector('.template-layout-shell');
    const text = String(shell?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function waitForListReady(page) {
  await page.locator('table tbody tr').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const bodyText = String(document.body?.textContent || '');
    if (bodyText.includes('页面加载失败') || bodyText.includes('页面渲染失败')) return true;
    return !bodyText.includes('正在加载') && document.querySelectorAll('table tbody tr').length > 0;
  }, null, { timeout: 30000 });
}

async function formSnapshot(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const shell = document.querySelector('.template-layout-shell');
    return {
      url: window.location.href,
      title: clean(document.querySelector('.template-page-title, h1, .title')?.textContent || ''),
      shell_count: document.querySelectorAll('.template-layout-shell').length,
      statusbar_count: document.querySelectorAll('.native-statusbar-step').length,
      chatter_count: document.querySelectorAll('.native-chatter-block').length,
      input_count: document.querySelectorAll('.template-layout-shell input, .template-layout-shell textarea, .template-layout-shell select').length,
      has_error: clean(shell?.textContent || '').includes('页面加载失败') || clean(shell?.textContent || '').includes('页面渲染失败'),
      text_sample: clean(shell?.textContent || '').slice(0, 600),
    };
  });
}

async function listSnapshot(page) {
  return page.evaluate(() => ({
    url: window.location.href,
    row_count: document.querySelectorAll('table tbody tr').length,
    text_sample: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 600),
  }));
}

function formRenderable(snapshot, expectedRecordId = RECORD_ID) {
  return snapshot.url.includes(`/r/${MODEL}/${expectedRecordId}`)
    && snapshot.shell_count === 1
    && snapshot.statusbar_count > 0
    && snapshot.input_count > 0
    && snapshot.has_error === false;
}

async function openForm(page) {
  await page.goto(formUrl(), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
}

async function exerciseReload(page) {
  await openForm(page);
  const before = await formSnapshot(page);
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
  const after = await formSnapshot(page);
  return {
    path_id: 'P25',
    level: 'L4',
    scenario: 'record_form_reload',
    status: formRenderable(before) && formRenderable(after) ? 'pass' : 'fail',
    before,
    after,
  };
}

async function exerciseBackForward(page) {
  await page.goto(listUrl(), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForListReady(page);
  const listBefore = await listSnapshot(page);
  await openForm(page);
  const formBeforeBack = await formSnapshot(page);
  await page.goBack({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForListReady(page);
  const afterBack = await listSnapshot(page);
  await page.goForward({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
  const afterForward = await formSnapshot(page);
  return {
    path_id: 'P25',
    level: 'L4',
    scenario: 'browser_back_forward',
    status: listBefore.row_count > 0
      && formRenderable(formBeforeBack)
      && afterBack.row_count > 0
      && formRenderable(afterForward)
      ? 'pass'
      : 'fail',
    list_before: listBefore,
    form_before_back: formBeforeBack,
    after_back: afterBack,
    after_forward: afterForward,
  };
}

async function exerciseUnauthenticatedDeepLinkRedirect(browser) {
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 1100 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  await clearBrowserAuth(page);
  await page.goto(formUrl(), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout: 20000 });
  const loginUrl = page.url();
  const redirectParam = new URL(loginUrl).searchParams.get('redirect') || '';
  await submitLoginForm(page);
  await waitForFormReady(page);
  const afterLogin = await formSnapshot(page);
  const result = {
    path_id: 'P25',
    level: 'L4',
    scenario: 'unauthenticated_deep_link_login_return',
    status: loginUrl.includes('/login')
      && redirectParam.includes(`/r/${MODEL}/${RECORD_ID}`)
      && redirectParam.includes(`action_id=${ACTION_ID}`)
      && formRenderable(afterLogin)
      ? 'pass'
      : 'fail',
    login_url: loginUrl,
    redirect_param: redirectParam,
    after_login: afterLogin,
    console_errors: page.__consoleErrors || [],
  };
  await context.close();
  return result;
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    artifacts: outDir,
    paths: [],
  };

  try {
    const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 1100 } });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);
    result.paths.push(await exerciseReload(page));
    result.paths.push(await exerciseBackForward(page));
    result.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'authenticated_final.png'), fullPage: true });
    await context.close();

    const deepLinkResult = await exerciseUnauthenticatedDeepLinkRedirect(browser);
    result.paths.push(deepLinkResult);
    result.console_errors = result.console_errors.concat(deepLinkResult.console_errors || []);
    result.pass = result.paths.every((row) => row.status === 'pass') && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_navigation_recovery_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths.map((row) => ({ scenario: row.scenario, status: row.status })),
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_navigation_recovery_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
