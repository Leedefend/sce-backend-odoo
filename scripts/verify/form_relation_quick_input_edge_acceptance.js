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
const RECORD_ID = Number(process.env.RECORD_ID || 771);
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-relation-quick-input-edge', ts);

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

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `form-relation-edge-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return body.data || {};
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

async function listPartners(page, keyword) {
  const data = await intentRequest(page, 'api.data', {
    op: 'list',
    model: 'res.partner',
    fields: ['id', 'name', 'display_name'],
    search_term: keyword,
    limit: 8,
    order: 'id desc',
    context: {},
  });
  return Array.isArray(data.records) ? data.records : [];
}

async function readProject(page) {
  const data = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [RECORD_ID],
    fields: ['id', 'name', 'partner_id', 'user_id'],
    context: {},
  });
  const row = Array.isArray(data.records) ? data.records[0] : null;
  if (!row) throw new Error(`project.project/${RECORD_ID} not found`);
  return row;
}

async function findAmbiguousPartnerKeyword(page) {
  const candidates = ['公司', '工程', '四川', '建设', '项目', '有限'];
  const attempts = [];
  for (const keyword of candidates) {
    const rows = await listPartners(page, keyword);
    attempts.push({
      keyword,
      count: rows.length,
      sample: rows.map((row) => normalize(row.display_name || row.name || `#${row.id}`)).slice(0, 5),
    });
    if (rows.length > 1) return { keyword, rows, attempts };
  }
  return { keyword: '', rows: [], attempts };
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openProject(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

function relationBox(page, index) {
  return page.locator('.many2one-combobox').nth(index);
}

async function relationValue(page, index) {
  return relationBox(page, index).locator('input').inputValue();
}

async function dialogSnapshot(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      title: clean(document.querySelector('.relation-dialog h3')?.textContent),
      keyword: document.querySelector('.relation-dialog input.input')?.value || '',
      headers: Array.from(document.querySelectorAll('.relation-dialog th')).map((node) => clean(node.textContent)).filter(Boolean),
      rows: Array.from(document.querySelectorAll('.relation-dialog tbody tr')).map((row) => clean(row.textContent)),
      select_disabled: Boolean(document.querySelector('.relation-dialog-footer button.primary')?.disabled),
    };
  });
}

async function discardIfPresent(page) {
  const discard = page.getByRole('button', { name: /^放弃$/ }).first();
  if (await discard.isVisible().catch(() => false)) {
    await discard.click();
    await waitForFormReady(page);
  }
}

async function exerciseAmbiguousQuickInput(page) {
  const match = await findAmbiguousPartnerKeyword(page);
  if (!match.keyword) {
    return {
      path_id: 'P07',
      level: 'L4',
      scenario: 'multiple_match_requires_dialog_selection',
      status: 'fail',
      reason: 'no ambiguous res.partner keyword found',
      attempts: match.attempts,
    };
  }
  await openProject(page);
  const input = relationBox(page, 0).locator('input');
  await input.fill(match.keyword);
  await input.press('Enter');
  await page.locator('.relation-dialog').waitFor({ timeout: 15000 });
  await page.locator('.relation-dialog tbody tr').first().waitFor({ timeout: 15000 });
  const snapshot = await dialogSnapshot(page);
  await page.locator('.relation-dialog-footer button').filter({ hasText: '取消' }).click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const afterCancel = await relationValue(page, 0);
  await discardIfPresent(page);
  return {
    path_id: 'P07',
    level: 'L4',
    scenario: 'multiple_match_requires_dialog_selection',
    status: snapshot.title === '客户：搜索更多'
      && snapshot.keyword === match.keyword
      && snapshot.rows.length > 1
      && snapshot.select_disabled
      && afterCancel === match.keyword
      ? 'pass'
      : 'fail',
    keyword: match.keyword,
    api_match_count: match.rows.length,
    api_sample: match.rows.map((row) => normalize(row.display_name || row.name || `#${row.id}`)).slice(0, 5),
    snapshot,
    after_cancel_input: afterCancel,
    attempts: match.attempts,
  };
}

async function exerciseClearWithoutSave(page) {
  const beforeProject = await readProject(page);
  await openProject(page);
  const beforeValue = await relationValue(page, 1);
  const input = relationBox(page, 1).locator('input');
  await input.fill('');
  await input.blur();
  await page.waitForTimeout(500);
  const afterClearInput = await relationValue(page, 1);
  const buttonsAfterClear = await page.locator('.template-page-header-actions button').evaluateAll((nodes) => nodes.map((node) => ({
    text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: Boolean(node.disabled),
  })));
  await discardIfPresent(page);
  const afterDiscardInput = await relationValue(page, 1);
  const afterProject = await readProject(page);
  return {
    path_id: 'P07',
    level: 'L4',
    scenario: 'clear_many2one_without_save_then_discard',
    status: beforeValue
      && afterClearInput === ''
      && buttonsAfterClear.some((button) => button.text === '放弃' && !button.disabled)
      && afterDiscardInput === beforeValue
      && JSON.stringify(afterProject.user_id || false) === JSON.stringify(beforeProject.user_id || false)
      ? 'pass'
      : 'fail',
    before_input: beforeValue,
    after_clear_input: afterClearInput,
    after_discard_input: afterDiscardInput,
    before_user_id: beforeProject.user_id,
    after_user_id: afterProject.user_id,
    buttons_after_clear: buttonsAfterClear,
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
    model: 'project.project',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(page);
    summary.checks.push(await exerciseAmbiguousQuickInput(page));
    summary.checks.push(await exerciseClearWithoutSave(page));
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
    await page.screenshot({ path: path.join(outDir, 'project-relation-edge-final.png'), fullPage: true });
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
