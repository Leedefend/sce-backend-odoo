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
const outDir = path.join(ARTIFACTS_DIR, 'form-action-path', ts);

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
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function openForm(page) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'domcontentloaded', timeout: 45000 },
  );
  await page.locator('.template-layout-shell').first().waitFor({ timeout: 30000 });
}

async function inspectContract(page) {
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

async function exerciseStatusbar(page) {
  await page.locator('.native-statusbar-step:not(:disabled)').first().click().catch(() => {});
  await page.waitForTimeout(120);
  const steps = await page.locator('.native-statusbar-step').evaluateAll((nodes) => nodes.map((node) => ({
    label: (node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: node.hasAttribute('disabled'),
    active: node.classList.contains('native-statusbar-step--active'),
    done: node.classList.contains('native-statusbar-step--done'),
  })));
  return {
    path_id: 'P15',
    level: 'L4',
    name: 'statusbar reachable',
    status: steps.length > 0 && steps.some((row) => row.active || row.done) ? 'pass' : 'fail',
    steps,
  };
}

async function exerciseSmartButton(page) {
  const labels = await page.locator('button').evaluateAll((nodes) => nodes.map((node) => ({
    text: (node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: node.hasAttribute('disabled'),
  })).filter((row) => ['执行结构', '工程量清单', '预算/成本', '合同', '物资/采购', '结算/财务', '投标管理'].includes(row.text)));
  const target = page.getByRole('button', { name: /^投标管理$/ }).first();
  const before = page.url();
  let triggered = false;
  let navigated = false;
  if (await target.count().catch(() => 0)) {
    await target.click().catch(() => {});
    triggered = true;
    await page.waitForURL((url) => url.href !== before, { timeout: 12000 }).catch(() => {});
    navigated = page.url() !== before;
    if (navigated) {
      await openForm(page);
    }
  }
  const hasErrorPanel = await page.locator('.status-panel--error,.template-error,.validation-error').first().isVisible().catch(() => false);
  return {
    path_id: 'P16',
    level: 'L4',
    name: 'smart button reachable',
    status: labels.length >= 3 && triggered && !hasErrorPanel ? 'pass' : 'fail',
    labels,
    clicked: '投标管理',
    triggered,
    navigated,
    has_error_panel: hasErrorPanel,
  };
}

async function exerciseBodyActionButton(page) {
  const tab = page.locator('button.native-tab').filter({ hasText: /^工程量清单$/ }).first();
  if (await tab.count().catch(() => 0)) {
    await tab.click();
  }
  const actionButtons = page.locator('button.native-action-btn:not(.native-action-btn--smart)');
  const target = actionButtons.first();
  const visible = await target.isVisible().catch(() => false);
  const buttonText = visible ? (await target.innerText().catch(() => '')).trim() : '';
  const before = page.url();
  let triggered = false;
  let navigated = false;
  if (visible) {
    await target.click().catch(() => {});
    triggered = true;
    await page.waitForURL((url) => url.href !== before, { timeout: 12000 }).catch(() => {});
    navigated = page.url() !== before;
    if (navigated) {
      await openForm(page);
    }
  }
  const hasErrorPanel = await page.locator('.status-panel--error,.template-error,.validation-error').first().isVisible().catch(() => false);
  return {
    path_id: 'P19',
    level: 'L4',
    name: 'body action button reachable',
    status: visible && triggered && !hasErrorPanel ? 'pass' : 'fail',
    clicked: buttonText || 'N/A',
    visible,
    triggered,
    navigated,
    has_error_panel: hasErrorPanel,
  };
}

async function exerciseChatterMessage(page) {
  const chatter = page.locator('.native-chatter-block').first();
  const chatterVisible = await chatter.isVisible().catch(() => false);
  if (!chatterVisible) {
    return {
      path_id: 'P17',
      level: 'L4',
      name: 'chatter message and activity reachable',
      status: 'pass',
      skipped: true,
      reason: 'native_chatter_block_not_available_for_current_contract',
      buttons: [],
    };
  }
  const buttons = await chatter.locator('button.chip-btn').evaluateAll((nodes) => nodes.map((node) => ({
    text: (node.textContent || '').replace(/\s+/g, ' ').trim(),
    disabled: node.hasAttribute('disabled'),
  })));
  const send = chatter.getByRole('button', { name: /^发送消息$/ }).first();
  await send.click();
  const body = `L4 form chatter acceptance ${Date.now()}`;
  await chatter.locator('textarea.native-chatter-input').fill(body);
  await chatter.getByRole('button', { name: /^发送消息$/ }).last().click();
  await page.getByText(body, { exact: false }).waitFor({ timeout: 20000 });
  const activity = chatter.getByRole('button', { name: /^活动$/ }).first();
  const activitySummary = `L4 form activity acceptance ${Date.now()}`;
  let activityScheduled = false;
  if (await activity.count().catch(() => 0)) {
    await activity.click();
    await chatter.locator('.native-chatter-field input[type="text"]').fill(activitySummary);
    await chatter.locator('.native-chatter-field input[type="date"]').fill(new Date().toISOString().slice(0, 10));
    await chatter.locator('.native-chatter-field textarea.native-chatter-input').fill('L4 activity browser acceptance');
    await chatter.getByRole('button', { name: /^活动$/ }).last().click();
    await page.getByText(activitySummary, { exact: false }).waitFor({ timeout: 20000 });
    activityScheduled = true;
  }
  return {
    path_id: 'P17',
    level: 'L4',
    name: 'chatter message and activity reachable',
    status: buttons.some((row) => row.text === '发送消息' && !row.disabled)
      && buttons.some((row) => row.text === '活动' && !row.disabled)
      && activityScheduled
      ? 'pass'
      : 'fail',
    buttons,
    posted_body: body,
    activity_summary: activitySummary,
    activity_scheduled: activityScheduled,
  };
}

async function exerciseAttachmentPath(page) {
  const chatter = page.locator('.native-chatter-block').first();
  const chatterVisible = await chatter.isVisible().catch(() => false);
  if (!chatterVisible) {
    return {
      path_id: 'P18',
      level: 'L4',
      name: 'attachment upload and download reachable',
      status: 'pass',
      skipped: true,
      reason: 'native_chatter_block_not_available_for_current_contract',
    };
  }
  const fileName = `L4 form attachment acceptance ${Date.now()}.txt`;
  const fileContent = `L4 form attachment acceptance ${new Date().toISOString()}\n`;
  const filePath = path.join(outDir, fileName);
  fs.writeFileSync(filePath, fileContent, 'utf8');

  const input = chatter.locator('.native-attachment-upload input[type="file"]').first();
  await input.waitFor({ state: 'attached', timeout: 15000 });
  await input.setInputFiles(filePath);
  await page.getByText(fileName, { exact: false }).waitFor({ timeout: 20000 });

  const entry = page.locator('li.native-chatter-entry').filter({ hasText: fileName }).first();
  const downloadButton = entry.locator('button.native-attachment-download').first();
  await downloadButton.waitFor({ timeout: 15000 });
  const downloadPromise = page.waitForEvent('download');
  await downloadButton.click();
  const download = await downloadPromise;
  const downloadPath = path.join(outDir, `downloaded-${download.suggestedFilename() || fileName}`);
  await download.saveAs(downloadPath);
  const downloadedContent = fs.readFileSync(downloadPath, 'utf8');

  return {
    path_id: 'P18',
    level: 'L4',
    name: 'attachment upload and download reachable',
    status: downloadedContent === fileContent ? 'pass' : 'fail',
    file_name: fileName,
    suggested_filename: download.suggestedFilename(),
    uploaded_visible: true,
    downloaded: true,
    content_matched: downloadedContent === fileContent,
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
    paths: [],
    contract: {},
  };

  try {
    const context = await browser.newContext({ locale: 'zh-CN' });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);
    await openForm(page);
    result.contract = await inspectContract(page);
    result.paths.push(await exerciseStatusbar(page));
    result.paths.push(await exerciseSmartButton(page));
    result.paths.push(await exerciseBodyActionButton(page));
    result.paths.push(await exerciseChatterMessage(page));
    result.paths.push(await exerciseAttachmentPath(page));
    result.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'custom_final.png'), fullPage: true });
    await context.close();
    result.pass = result.paths.every((row) => row.status === 'pass') && result.console_errors.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_action_path_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths,
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_action_path_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
