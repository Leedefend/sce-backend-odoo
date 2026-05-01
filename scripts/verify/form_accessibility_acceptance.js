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
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-accessibility', ts);

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
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function openForm(page) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'domcontentloaded', timeout: 45000 },
  );
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('页面加载失败') && !text.includes('页面渲染失败');
  }, null, { timeout: 30000 });
}

async function collectButtonNames(page) {
  return page.evaluate(() => {
    const normalizeText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return Array.from(document.querySelectorAll('button, [role="button"], input[type="file"]')).map((node) => ({
      tag: node.tagName.toLowerCase(),
      text: normalizeText(node.textContent),
      aria_label: normalizeText(node.getAttribute('aria-label')),
      title: normalizeText(node.getAttribute('title')),
      class_name: normalizeText(node.getAttribute('class')),
      disabled: Boolean(node.disabled || node.getAttribute('aria-disabled') === 'true'),
      type: normalizeText(node.getAttribute('type')),
      hidden: Boolean(node.hidden || node.getAttribute('aria-hidden') === 'true' || node.closest('[hidden]')),
    }));
  });
}

async function exerciseNamedControls(page) {
  const controls = await collectButtonNames(page);
  const missingName = controls.filter((control) => {
    if (control.class_name.includes('native-attachment-upload')) return false;
    if (control.type === 'file') return false;
    if (control.hidden) return false;
    return !control.text && !control.aria_label && !control.title;
  });
  const required = [
    { key: 'statusbar', pass: controls.some((row) => row.class_name.includes('native-statusbar-step') && row.text) },
    { key: 'smart_button', pass: controls.some((row) => row.class_name.includes('native-action-btn--smart') && row.text === '投标管理') },
    { key: 'chatter_message', pass: controls.some((row) => row.text === '发送消息' && !row.disabled) },
    { key: 'chatter_activity', pass: controls.some((row) => row.text === '活动' && !row.disabled) },
    { key: 'relation_search_more', pass: controls.some((row) => row.text.includes('搜索更多') && !row.disabled) },
  ];
  return {
    path_id: 'P27',
    level: 'L4',
    scenario: 'named_control_semantics',
    status: missingName.length === 0 && required.every((row) => row.pass) ? 'pass' : 'fail',
    required,
    missing_accessible_name: missingName,
  };
}

async function exerciseKeyboardFocus(page) {
  const focusSamples = [];
  await page.keyboard.press('Tab');
  for (let index = 0; index < 90; index += 1) {
    focusSamples.push(await page.evaluate(() => {
      const node = document.activeElement;
      if (!node) return {};
      return {
        tag: node.tagName.toLowerCase(),
        text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
        aria_label: String(node.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(),
        class_name: String(node.getAttribute('class') || '').replace(/\s+/g, ' ').trim(),
        type: String(node.getAttribute('type') || ''),
      };
    }));
    await page.keyboard.press('Tab');
  }
  const hasStatusbar = focusSamples.some((row) => row.class_name.includes('native-statusbar-step'));
  const hasChatter = focusSamples.some((row) => ['发送消息', '活动'].includes(row.text));
  const hasSearchMore = focusSamples.some((row) => row.text.includes('搜索更多'));
  return {
    path_id: 'P27',
    level: 'L4',
    scenario: 'keyboard_tab_reaches_critical_controls',
    status: hasStatusbar && hasChatter && hasSearchMore ? 'pass' : 'fail',
    reached: { statusbar: hasStatusbar, chatter: hasChatter, search_more: hasSearchMore },
    samples: focusSamples.filter((row) => row.text || row.aria_label || row.class_name).slice(0, 40),
  };
}

async function openSearchMore(page) {
  const button = page.locator('.many2one-combobox button').filter({ hasText: '搜索更多' }).first();
  await button.click();
  await page.locator('.relation-dialog').waitFor({ timeout: 10000 });
}

async function exerciseRelationDialog(page) {
  await openSearchMore(page);
  const before = await page.evaluate(() => ({
    title: String(document.querySelector('.relation-dialog h3')?.textContent || '').replace(/\s+/g, ' ').trim(),
    role: document.querySelector('.relation-dialog-backdrop')?.getAttribute('role'),
    modal: document.querySelector('.relation-dialog-backdrop')?.getAttribute('aria-modal'),
    close_label: String(document.querySelector('.relation-dialog-close')?.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(),
    select_disabled: Boolean(document.querySelector('.relation-dialog-footer button.primary')?.disabled),
    row_count: document.querySelectorAll('.relation-dialog tbody tr').length,
    buttons: Array.from(document.querySelectorAll('.relation-dialog button')).map((button) =>
      String(button.textContent || button.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(),
    ),
  }));
  await page.keyboard.press('Escape');
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const escapeClosed = !(await page.locator('.relation-dialog').count());

  await openSearchMore(page);
  await page.locator('.relation-dialog-close').click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const closeClosed = !(await page.locator('.relation-dialog').count());

  await openSearchMore(page);
  const firstRow = page.locator('.relation-dialog tbody tr').first();
  await firstRow.click();
  const selectEnabled = !(await page.locator('.relation-dialog-footer button.primary').first().isDisabled());
  await page.locator('.relation-dialog-footer button').filter({ hasText: '取消' }).click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });

  return {
    path_id: 'P27',
    level: 'L4',
    scenario: 'relation_dialog_escape_close_select_semantics',
    status: before.role === 'dialog'
      && before.modal === 'true'
      && Boolean(before.close_label)
      && before.select_disabled
      && escapeClosed
      && closeClosed
      && selectEnabled
      ? 'pass'
      : 'fail',
    before,
    escape_closed: escapeClosed,
    close_button_closed: closeClosed,
    select_enabled_after_row: selectEnabled,
  };
}

async function exerciseChatterComposer(page) {
  const chatter = page.locator('.native-chatter-block').first();
  await chatter.waitFor({ timeout: 15000 });
  await chatter.getByRole('button', { name: /^活动$/ }).first().click();
  const composerVisible = await chatter.locator('.native-chatter-compose').isVisible();
  const submit = chatter.locator('.native-chatter-compose-actions button.primary').first();
  const disabledBefore = await submit.isDisabled();
  await chatter.locator('.native-chatter-field input[type="text"]').fill(`P27 accessibility ${Date.now()}`);
  const enabledAfterSummary = !(await submit.isDisabled());
  await chatter.locator('.native-chatter-compose-actions button.ghost').filter({ hasText: '取消' }).click();
  const closed = !(await chatter.locator('.native-chatter-compose').count());
  return {
    path_id: 'P27',
    level: 'L4',
    scenario: 'chatter_activity_composer_disabled_semantics',
    status: composerVisible && disabledBefore && enabledAfterSummary && closed ? 'pass' : 'fail',
    composer_visible: composerVisible,
    submit_disabled_before_summary: disabledBefore,
    submit_enabled_after_summary: enabledAfterSummary,
    closed_after_cancel: closed,
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  let context;
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
    context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);
    await openForm(page);
    result.paths.push(await exerciseNamedControls(page));
    result.paths.push(await exerciseKeyboardFocus(page));
    result.paths.push(await exerciseRelationDialog(page));
    result.paths.push(await exerciseChatterComposer(page));
    result.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'custom_form_p27.png'), fullPage: true });
    result.pass = result.paths.every((row) => row.status === 'pass') && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_accessibility_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths.map((row) => ({ scenario: row.scenario, status: row.status })),
      console_errors: result.console_errors.length,
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    if (context) await context.close();
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_accessibility_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
