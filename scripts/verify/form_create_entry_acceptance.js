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
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const RECORD_ID = Number(process.env.RECORD_ID || 771);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-create-entry', ts);

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

async function openProjectList(page) {
  await page.goto(`${FRONTEND_URL}/a/${ACTION_ID}?menu_id=${MENU_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('table tbody tr').first().waitFor({ timeout: 30000 });
}

async function openProjectForm(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function openProjectCreateForm(page) {
  await page.goto(`${FRONTEND_URL}/f/project.project/new?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
}

async function formSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      text: clean(document.body?.textContent || '').slice(0, 2400),
      labels: Array.from(document.querySelectorAll('.field .label')).map((node) =>
        clean(node.textContent).replace(/\*$/, ''),
      ).filter(Boolean),
      required_labels: Array.from(document.querySelectorAll('.field')).filter((field) =>
        Boolean(field.querySelector('.required')),
      ).map((field) => clean(field.querySelector('.label')?.textContent || '').replace(/\*$/, '')).filter(Boolean),
      save_buttons: Array.from(document.querySelectorAll('button')).map((button) => clean(button.textContent))
        .filter((text) => text === '保存'),
      technical_labels: Array.from(document.querySelectorAll('.field .label')).map((node) =>
        clean(node.textContent).replace(/\*$/, ''),
      ).filter((label) => ['ID', '创建人', '创建时间', '最后更新人', '最后更新时间'].includes(label)),
      shell_count: document.querySelectorAll('.template-layout-shell').length,
      validation_errors: Array.from(document.querySelectorAll('.error, .status-error, .validation-error')).map((node) =>
        clean(node.textContent),
      ).filter(Boolean),
    };
  });
}

async function exerciseListCreateEntry(page) {
  await openProjectList(page);
  await page.getByRole('button', { name: /^新建$/ }).first().click();
  await page.waitForURL((url) => url.pathname === '/f/project.project/new', { timeout: 15000 });
  await waitForFormReady(page);
  const surface = await formSurface(page);
  return {
    path_id: 'P03',
    level: 'L4',
    scenario: 'list_create_project_entry',
    status: surface.url.includes('/f/project.project/new')
      && surface.shell_count === 1
      && surface.save_buttons.length > 0
      && surface.required_labels.includes('名称')
      && !surface.text.includes('页面加载失败')
      && surface.technical_labels.length === 0
      ? 'pass'
      : 'fail',
    surface,
  };
}

async function exerciseRelationCreateEntry(page) {
  await openProjectForm(page);
  let customerField = page.locator('.field').filter({ has: page.locator('.label', { hasText: /^客户\*?$/ }) }).first();
  let maintainButton = customerField.locator('.many2one-combobox button').filter({ hasText: '新建并维护' }).first();
  if (!await maintainButton.count()) {
    await openProjectCreateForm(page);
    customerField = page.locator('.field').filter({ has: page.locator('.label', { hasText: /^客户\*?$/ }) }).first();
    maintainButton = customerField.locator('.many2one-combobox button').filter({ hasText: '新建并维护' }).first();
  }
  await maintainButton.click();
  await page.waitForURL((url) => url.pathname === '/f/res.partner/new', { timeout: 15000 });
  await waitForFormReady(page);
  const surface = await formSurface(page);
  const url = new URL(surface.url);
  return {
    path_id: 'P03',
    level: 'L4',
    scenario: 'many2one_create_and_edit_entry',
    status: surface.url.includes('/f/res.partner/new')
      && surface.shell_count === 1
      && surface.save_buttons.length > 0
      && surface.labels.includes('名称')
      && url.searchParams.get('return_field') === 'partner_id'
      && url.searchParams.get('return_model') === 'project.project'
      && !surface.text.includes('页面加载失败')
      && surface.technical_labels.length === 0
      ? 'pass'
      : 'fail',
    native_required_fact: {
      model: 'res.partner',
      field: 'name',
      required: false,
      evidence: 'Odoo shell: env[res.partner]._fields[name].required == False',
    },
    return_field: url.searchParams.get('return_field'),
    return_model: url.searchParams.get('return_model'),
    return_action_id: url.searchParams.get('return_action_id'),
    surface,
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
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    record_id: RECORD_ID,
    frontend_url: FRONTEND_URL,
    artifact_dir: outDir,
    paths: [],
  };

  try {
    await login(page);
    summary.paths.push(await exerciseListCreateEntry(page));
    await page.screenshot({ path: path.join(outDir, 'project-create-form.png'), fullPage: true });
    summary.paths.push(await exerciseRelationCreateEntry(page));
    await page.screenshot({ path: path.join(outDir, 'partner-relation-create-form.png'), fullPage: true });
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = summary.paths.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
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
