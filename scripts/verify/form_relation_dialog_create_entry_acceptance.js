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
const outDir = path.join(ARTIFACTS_DIR, 'form-relation-dialog-create-entry', ts);

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

async function openCustomerSearchMore(page) {
  await relationBox(page, 0).locator('button').filter({ hasText: '搜索更多' }).first().click();
  await page.locator('.relation-dialog').waitFor({ timeout: 10000 });
  await page.locator('.relation-dialog tbody tr').first().waitFor({ timeout: 15000 });
}

async function dialogSnapshot(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      title: clean(document.querySelector('.relation-dialog h3')?.textContent),
      headers: Array.from(document.querySelectorAll('.relation-dialog th')).map((node) => clean(node.textContent)).filter(Boolean),
      rows: document.querySelectorAll('.relation-dialog tbody tr').length,
      buttons: Array.from(document.querySelectorAll('.relation-dialog-footer button')).map((button) => ({
        text: clean(button.textContent),
        disabled: Boolean(button.disabled),
      })),
    };
  });
}

async function formSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      labels: Array.from(document.querySelectorAll('.field .label')).map((node) =>
        clean(node.textContent).replace(/\*$/, ''),
      ).filter(Boolean),
      buttons: Array.from(document.querySelectorAll('.template-page-header-actions button')).map((button) => ({
        text: clean(button.textContent),
        disabled: Boolean(button.disabled),
      })),
      technical_labels: Array.from(document.querySelectorAll('.field .label')).map((node) =>
        clean(node.textContent).replace(/\*$/, ''),
      ).filter((label) => ['ID', '创建人', '创建时间', '最后更新人', '最后更新时间'].includes(label)),
      text: clean(document.body?.textContent || '').slice(0, 1600),
    };
  });
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
    await openProject(page);
    await openCustomerSearchMore(page);
    const dialog = await dialogSnapshot(page);
    await page.locator('.relation-dialog-footer button').filter({ hasText: /^新建$/ }).click();
    await page.waitForURL((url) => url.pathname === '/f/res.partner/new', { timeout: 15000 });
    await waitForFormReady(page);
    const surface = await formSurface(page);
    const url = new URL(surface.url);
    summary.checks.push({
      path_id: 'P08',
      level: 'L4',
      scenario: 'search_more_create_and_edit_entry',
      status: dialog.title === '客户：搜索更多'
        && dialog.rows > 0
        && dialog.buttons.some((button) => button.text === '新建' && !button.disabled)
        && surface.url.includes('/f/res.partner/new')
        && surface.labels.includes('名称')
        && surface.buttons.some((button) => button.text === '保存')
        && url.searchParams.get('return_field') === 'partner_id'
        && url.searchParams.get('return_model') === 'project.project'
        && url.searchParams.get('return_action_id') === String(ACTION_ID)
        && surface.technical_labels.length === 0
        && !surface.text.includes('页面加载失败')
        ? 'pass'
        : 'fail',
      dialog,
      surface,
      return_field: url.searchParams.get('return_field'),
      return_model: url.searchParams.get('return_model'),
      return_action_id: url.searchParams.get('return_action_id'),
      return_menu_id: url.searchParams.get('return_menu_id'),
    });
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
    await page.screenshot({ path: path.join(outDir, 'relation-dialog-create-form.png'), fullPage: true });
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
