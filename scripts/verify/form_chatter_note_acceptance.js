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
const outDir = path.join(ARTIFACTS_DIR, 'form-chatter-note', ts);

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
  await page.locator('.template-layout-shell input.input').first().waitFor({ timeout: 30000 });
  await page.locator('.native-chatter-block').first().waitFor({ timeout: 15000 });
}

async function readChatterContract(page) {
  return page.evaluate(() => {
    const raw = window.localStorage.getItem('sc:last-contract');
    if (!raw) return {};
    try {
      const contract = JSON.parse(raw);
      return contract?.views?.form?.chatter || {};
    } catch {
      return {};
    }
  }).catch(() => ({}));
}

async function exerciseLogNote(page) {
  const chatter = page.locator('.native-chatter-block').first();
  const actions = await chatter.locator('button.chip-btn').evaluateAll((nodes) => nodes.map((node) => ({
    text: (node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: node.hasAttribute('disabled'),
  })));
  const noteAction = chatter.getByRole('button', { name: /^记录备注$/ }).first();
  await noteAction.click();
  const body = `P17 note acceptance ${Date.now()}`;
  await chatter.locator('textarea.native-chatter-input').fill(body);
  await chatter.getByRole('button', { name: /^记录备注$/ }).last().click();
  await page.getByText(body, { exact: false }).waitFor({ timeout: 20000 });
  const visibleTimelineRows = await page.locator('li.native-chatter-entry').evaluateAll((nodes) => nodes.map((node) => ({
    type: (node.querySelector('.native-chatter-type')?.textContent || '').replace(/\s+/g, ' ').trim(),
    body: (node.querySelector('.native-chatter-body')?.textContent || '').replace(/\s+/g, ' ').trim(),
    meta: (node.querySelector('.native-chatter-meta')?.textContent || '').replace(/\s+/g, ' ').trim(),
  })));
  const matchingRow = visibleTimelineRows.find((row) => row.body.includes(body));
  return {
    path_id: 'P17',
    level: 'L4',
    name: 'chatter log note reachable',
    status: actions.some((row) => row.text === '记录备注' && !row.disabled)
      && Boolean(matchingRow)
      && matchingRow.type === '备注'
      ? 'pass'
      : 'fail',
    actions,
    note_body: body,
    expected_type_label: '备注',
    matching_row: matchingRow || null,
  };
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
    contract: {},
    path: null,
  };

  try {
    const context = await browser.newContext({ locale: 'zh-CN' });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);
    await openForm(page);
    result.contract = await readChatterContract(page);
    result.path = await exerciseLogNote(page);
    result.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'custom_final.png'), fullPage: true });
    await context.close();
    result.pass = result.path.status === 'pass' && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_chatter_note_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      path: result.path,
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_chatter_note_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
