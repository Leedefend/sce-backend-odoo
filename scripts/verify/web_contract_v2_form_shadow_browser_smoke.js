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
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = Number(process.env.RECORD_ID || 908);
const ACTION_ID = Number(process.env.ACTION_ID || 0);
const MENU_ID = Number(process.env.MENU_ID || 0);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const CHROMIUM_EXECUTABLE_PATH = process.env.CHROMIUM_EXECUTABLE_PATH || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || '';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'playwright', 'web-contract-v2-form-shadow', ts);

function ensureOutDir() {
  fs.mkdirSync(outDir, { recursive: true });
}

function writeJson(name, data) {
  ensureOutDir();
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.__resourceNotFound = [];
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (text.includes('Failed to load resource: the server responded with a status of 404')) return;
    page.__consoleErrors.push(text);
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
  page.on('response', (response) => {
    if (response.status() === 404) page.__resourceNotFound.push(response.url());
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if (await dbInput.isEnabled().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
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

function projectUrl() {
  const query = new URLSearchParams({ hud: '1' });
  if (ACTION_ID > 0) query.set('action_id', String(ACTION_ID));
  if (MENU_ID > 0) query.set('menu_id', String(MENU_ID));
  return `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?${query.toString()}`;
}

async function readHud(page) {
  return page.evaluate(() => {
    const rows = {};
    document.querySelectorAll('.hud .row').forEach((row) => {
      const label = String(row.querySelector('.label')?.textContent || '').trim();
      const value = String(row.querySelector('.value')?.textContent || '').trim();
      if (label) rows[label] = value;
    });
    return rows;
  });
}

async function readShadowAttrs(page) {
  return page.evaluate(() => {
    const shell = document.querySelector('.template-layout-shell');
    return {
      store: String(shell?.getAttribute('data-v2-shadow-store') || ''),
      widgets: String(shell?.getAttribute('data-v2-shadow-widgets') || ''),
      actions: String(shell?.getAttribute('data-v2-shadow-actions') || ''),
      button_statuses: String(shell?.getAttribute('data-v2-shadow-button-statuses') || ''),
      field_codes: String(shell?.getAttribute('data-v2-shadow-field-codes') || ''),
      field_overlap: String(shell?.getAttribute('data-v2-shadow-field-overlap') || ''),
      field_missing: String(shell?.getAttribute('data-v2-shadow-field-missing') || ''),
      layout_source: String(shell?.getAttribute('data-v2-shadow-layout-source') || ''),
      global_source: String(shell?.getAttribute('data-v2-shadow-global-source') || ''),
      source_context: String(shell?.getAttribute('data-v2-shadow-source-context') || ''),
      status_fields: String(shell?.getAttribute('data-v2-shadow-status-fields') || ''),
      value_fields: String(shell?.getAttribute('data-v2-shadow-value-fields') || ''),
      main_data_fields: String(shell?.getAttribute('data-v2-shadow-main-data-fields') || ''),
      readonly_values: String(shell?.getAttribute('data-v2-shadow-readonly-values') || ''),
      value_source: String(shell?.getAttribute('data-v2-shadow-value-source') || ''),
      error: String(shell?.getAttribute('data-v2-shadow-error') || ''),
    };
  });
}

async function pageSnapshot(page) {
  return page.evaluate(() => ({
    title: String(document.title || ''),
    url: String(window.location.href || ''),
    body_text: String(document.body?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 2000),
    shell_count: document.querySelectorAll('.template-layout-shell').length,
    hud_count: document.querySelectorAll('.hud').length,
    field_count: document.querySelectorAll('.template-form-section .field, .native-form-tree .field, .form-field, .native-form-field, .field-row').length,
  }));
}

async function main() {
  ensureOutDir();
  const launchOptions = CHROMIUM_EXECUTABLE_PATH
    ? { headless: true, executablePath: CHROMIUM_EXECUTABLE_PATH, args: ['--no-sandbox'] }
    : { headless: true };
  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const summary = {
    pass: false,
    frontend_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    hud: {},
    snapshot: {},
    console_errors: [],
  };

  try {
    await login(page);
    await page.goto(projectUrl(), { waitUntil: 'domcontentloaded', timeout: 45000 });
    await waitForFormReady(page);
    await page.locator('.template-layout-shell[data-v2-shadow-store]').waitFor({ timeout: 15000 });
    summary.hud = await readHud(page);
    summary.shadow_attrs = await readShadowAttrs(page);
    summary.snapshot = await pageSnapshot(page);
    summary.console_errors = (page.__consoleErrors || []).slice(0, 20);
    summary.resource_not_found = (page.__resourceNotFound || []).slice(0, 20);
    await page.screenshot({ path: path.join(outDir, 'form-shadow.png'), fullPage: true });

    const shadowStore = String(summary.shadow_attrs.store || summary.hud.v2_shadow_store || '').toLowerCase() === 'true';
    const shadowWidgets = Number(summary.shadow_attrs.widgets || summary.hud.v2_shadow_widgets || 0);
    const shadowButtonStatuses = Number(summary.shadow_attrs.button_statuses || summary.hud.v2_shadow_button_statuses || 0);
    const shadowFieldCodes = Number(summary.shadow_attrs.field_codes || summary.hud.v2_shadow_field_codes || 0);
    const shadowFieldOverlap = Number(summary.shadow_attrs.field_overlap || summary.hud.v2_shadow_field_overlap || 0);
    const shadowLayoutSource = String(summary.shadow_attrs.layout_source || summary.hud.v2_shadow_layout_source || '').trim();
    const shadowGlobalSource = String(summary.shadow_attrs.global_source || summary.hud.v2_shadow_global_source || '').trim();
    const shadowStatusFields = Number(summary.shadow_attrs.status_fields || summary.hud.v2_shadow_status_fields || 0);
    const shadowValueFields = Number(summary.shadow_attrs.value_fields || summary.hud.v2_shadow_value_fields || 0);
    const shadowMainDataFields = Number(summary.shadow_attrs.main_data_fields || summary.hud.v2_shadow_main_data_fields || 0);
    const shadowValueSource = String(summary.shadow_attrs.value_source || summary.hud.v2_shadow_value_source || '').trim();
    const shadowError = String(summary.shadow_attrs.error || summary.hud.v2_shadow_error || '').trim();
    const rendered = summary.snapshot.shell_count === 1 && !summary.snapshot.body_text.includes('页面加载失败');
    summary.pass = Boolean(
      rendered &&
      summary.snapshot.field_count > 0 &&
      shadowStore &&
      shadowWidgets > 0 &&
      shadowButtonStatuses > 0 &&
      shadowFieldCodes > 0 &&
      shadowFieldOverlap > 0 &&
      shadowLayoutSource === 'v2_store' &&
      shadowGlobalSource === 'v2_store' &&
      shadowStatusFields > 0 &&
      shadowValueFields > 0 &&
      shadowMainDataFields > 0 &&
      shadowValueSource !== 'none' &&
      (!shadowError || shadowError === '-') &&
      summary.console_errors.length === 0
    );
  } catch (err) {
    summary.error = err instanceof Error ? err.message : String(err);
    summary.console_errors = (page.__consoleErrors || []).slice(0, 20);
    summary.resource_not_found = (page.__resourceNotFound || []).slice(0, 20);
    try {
      summary.hud = await readHud(page);
      summary.shadow_attrs = await readShadowAttrs(page);
      summary.snapshot = await pageSnapshot(page);
      await page.screenshot({ path: path.join(outDir, 'form-shadow-failure.png'), fullPage: true });
    } catch {
      // keep original failure
    }
  } finally {
    writeJson('summary.json', summary);
    await browser.close();
  }

  if (!summary.pass) {
    console.error('[web_contract_v2_form_shadow_browser_smoke] FAIL');
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  }
  console.log('[web_contract_v2_form_shadow_browser_smoke] PASS');
  console.log(JSON.stringify({
    artifact_dir: outDir,
    url: summary.snapshot.url,
    v2_shadow_widgets: summary.shadow_attrs?.widgets || summary.hud.v2_shadow_widgets,
    v2_shadow_actions: summary.shadow_attrs?.actions || summary.hud.v2_shadow_actions,
    v2_shadow_button_statuses: summary.shadow_attrs?.button_statuses || summary.hud.v2_shadow_button_statuses,
    v2_shadow_field_codes: summary.shadow_attrs?.field_codes || summary.hud.v2_shadow_field_codes,
    v2_shadow_field_overlap: summary.shadow_attrs?.field_overlap || summary.hud.v2_shadow_field_overlap,
    v2_shadow_field_missing: summary.shadow_attrs?.field_missing || summary.hud.v2_shadow_field_missing,
    v2_shadow_layout_source: summary.shadow_attrs?.layout_source || summary.hud.v2_shadow_layout_source,
    v2_shadow_global_source: summary.shadow_attrs?.global_source || summary.hud.v2_shadow_global_source,
    v2_shadow_source_context: summary.shadow_attrs?.source_context || summary.hud.v2_shadow_source_context,
    v2_shadow_status_fields: summary.shadow_attrs?.status_fields || summary.hud.v2_shadow_status_fields,
    v2_shadow_value_fields: summary.shadow_attrs?.value_fields || summary.hud.v2_shadow_value_fields,
    v2_shadow_main_data_fields: summary.shadow_attrs?.main_data_fields || summary.hud.v2_shadow_main_data_fields,
    v2_shadow_readonly_values: summary.shadow_attrs?.readonly_values || summary.hud.v2_shadow_readonly_values,
    v2_shadow_value_source: summary.shadow_attrs?.value_source || summary.hud.v2_shadow_value_source,
  }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
