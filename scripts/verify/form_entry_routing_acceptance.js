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
const outDir = path.join(ARTIFACTS_DIR, 'form-entry-routing', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
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
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
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

async function openProjectForm(page, recordId = RECORD_ID) {
  await page.goto(`${FRONTEND_URL}/r/${MODEL}/${recordId}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function openProjectList(page, extraQuery = '') {
  const suffix = extraQuery ? `&${extraQuery.replace(/^\?+|^&+/, '')}` : '';
  await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}${suffix}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForListReady(page);
}

async function inspectLastContract(page) {
  return page.evaluate(() => {
    const raw = window.localStorage.getItem('sc:last-contract');
    if (!raw) return {};
    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }).catch(() => ({}));
}

async function bodySnapshot(page) {
  return page.evaluate(() => ({
    title: String(document.title || ''),
    text: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 2000),
    statusbar_count: document.querySelectorAll('.native-statusbar-step').length,
    form_shell_count: document.querySelectorAll('.template-layout-shell').length,
    list_row_count: document.querySelectorAll('table tbody tr').length,
  }));
}

async function exerciseDirectUrl(page) {
  await openProjectForm(page);
  const contract = await inspectLastContract(page);
  const snapshot = await bodySnapshot(page);
  const url = page.url();
  return {
    path_id: 'P01',
    level: 'L4',
    scenario: 'direct_record_url',
    status: url.includes(`/r/${MODEL}/${RECORD_ID}`)
      && snapshot.form_shell_count === 1
      && snapshot.statusbar_count > 0
      && !snapshot.text.includes('页面加载失败')
      ? 'pass'
      : 'fail',
    url,
    contract_model: contract?.params?.model || contract?.data?.model || contract?.model || null,
    contract_action_id: contract?.params?.action_id || contract?.action_id || null,
    snapshot,
  };
}

async function exerciseActionListRoute(page) {
  await openProjectList(page);
  const contract = await inspectLastContract(page);
  const snapshot = await bodySnapshot(page);
  const url = page.url();
  return {
    path_id: 'P01',
    level: 'L4',
    scenario: 'action_list_route',
    status: url.includes(`/a/${ACTION_ID}`)
      && snapshot.list_row_count > 0
      && !snapshot.text.includes('页面加载失败')
      ? 'pass'
      : 'fail',
    url,
    contract_model: contract?.params?.model || contract?.data?.model || contract?.model || null,
    contract_view_type: contract?.head?.view_type || contract?.view_type || null,
    snapshot,
  };
}

async function exerciseListRowOpen(page) {
  await openProjectList(page);
  const firstRow = page.locator('table tbody tr').first();
  const rowText = normalize(await firstRow.innerText());
  await firstRow.click();
  await page.waitForURL((url) => url.pathname.includes(`/r/${MODEL}/`), { timeout: 20000 });
  await waitForFormReady(page);
  const snapshot = await bodySnapshot(page);
  const url = page.url();
  const match = url.match(new RegExp(`/r/${MODEL.replace('.', '\\.')}/(\\d+)`));
  const openedRecordId = match ? Number(match[1]) : 0;
  return {
    path_id: 'P01',
    level: 'L4',
    scenario: 'list_row_open',
    status: openedRecordId > 0
      && snapshot.form_shell_count === 1
      && snapshot.statusbar_count > 0
      && rowText
      && snapshot.text.includes(rowText.split(/\s+/)[0])
      ? 'pass'
      : 'fail',
    row_text: rowText,
    url,
    opened_record_id: openedRecordId,
    snapshot,
  };
}

async function exerciseSmartButtonRoute(page) {
  await openProjectForm(page);
  const smartButtons = await page.locator('button.native-action-btn--smart').evaluateAll((nodes) => nodes.map((node) => ({
    text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: Boolean(node.disabled),
  }))).catch(() => []);
  const target = page.getByRole('button', { name: /^投标管理$/ }).first();
  const visible = await target.isVisible().catch(() => false);
  const before = page.url();
  let after = before;
  if (visible) {
    await target.click();
    await page.waitForURL((url) => url.href !== before, { timeout: 15000 }).catch(() => {});
    after = page.url();
  }
  const navigated = after !== before && (/\/a\/\d+/.test(after) || new RegExp(`/r/${MODEL}/\\d+`).test(after));
  await openProjectForm(page);
  return {
    path_id: 'P01',
    level: 'L4',
    scenario: 'smart_button_route',
    status: visible && navigated ? 'pass' : 'fail',
    clicked: '投标管理',
    before_url: before,
    after_url: after,
    smart_buttons: smartButtons,
  };
}

async function exerciseRelationDialogRoute(page) {
  await openProjectForm(page);
  const box = page.locator('.many2one-combobox').nth(1);
  const beforeValue = await box.locator('input').inputValue();
  await box.locator('button').filter({ hasText: '搜索更多' }).first().click();
  await page.locator('.relation-dialog').waitFor({ timeout: 10000 });
  await page.locator('.relation-dialog tbody tr').first().waitFor({ timeout: 15000 });
  const dialogBeforeSelect = await page.evaluate(() => ({
    title: String(document.querySelector('.relation-dialog h3')?.textContent || '').replace(/\s+/g, ' ').trim(),
    headers: Array.from(document.querySelectorAll('.relation-dialog th')).map((node) =>
      String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    ).filter(Boolean),
    rows: document.querySelectorAll('.relation-dialog tbody tr').length,
    select_disabled: Boolean(document.querySelector('.relation-dialog-footer button.primary')?.disabled),
  }));
  const firstRow = page.locator('.relation-dialog tbody tr').first();
  const rowText = normalize(await firstRow.innerText());
  await firstRow.click();
  const select = page.locator('.relation-dialog-footer button.primary').filter({ hasText: '选择' }).first();
  const selectEnabled = !(await select.isDisabled());
  await select.click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const afterValue = await box.locator('input').inputValue();
  await openProjectForm(page);
  return {
    path_id: 'P01',
    level: 'L4',
    scenario: 'relation_dialog_entry',
    status: dialogBeforeSelect.title === '项目管理员：搜索更多'
      && dialogBeforeSelect.rows > 0
      && dialogBeforeSelect.select_disabled
      && selectEnabled
      && afterValue
      && rowText.includes(afterValue)
      ? 'pass'
      : 'fail',
    before_value: beforeValue,
    after_value: afterValue,
    selected_row_text: rowText,
    dialog: dialogBeforeSelect,
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    artifact_dir: outDir,
    paths: [],
  };

  try {
    await login(page);
    summary.paths.push(await exerciseDirectUrl(page));
    summary.paths.push(await exerciseActionListRoute(page));
    summary.paths.push(await exerciseListRowOpen(page));
    summary.paths.push(await exerciseSmartButtonRoute(page));
    summary.paths.push(await exerciseRelationDialogRoute(page));
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = summary.paths.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
    await page.screenshot({ path: path.join(outDir, 'final-project-form.png'), fullPage: true });
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.actionable_console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true }).catch(() => {});
  } finally {
    writeJson('summary.json', summary);
    await browser.close();
  }

  if (!summary.pass) {
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(summary, null, 2));
}

main();
