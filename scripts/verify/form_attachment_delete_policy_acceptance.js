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
const outDir = path.join(ARTIFACTS_DIR, 'form-attachment-delete-policy', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
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

async function intentRequest(page, intent, params) {
  return page.evaluate(async ({ dbName, intentName, payload }) => {
    const token = sessionStorage.getItem(`sc_auth_token:${dbName}`);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
      meta: body.meta || {},
    };
  }, { dbName: DB_NAME, intentName: intent, payload: params });
}

async function domAttachmentDeleteSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      upload_buttons: Array.from(document.querySelectorAll('.native-attachment-upload')).map((node) => clean(node.textContent)),
      download_buttons: document.querySelectorAll('.native-attachment-download').length,
      delete_buttons: document.querySelectorAll('.native-attachment-delete').length,
      attachment_block_count: document.querySelectorAll('.native-attachment-tools').length,
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
    const contractResp = await intentRequest(page, 'ui.contract', {
      op: 'action_open',
      action_id: ACTION_ID,
      record_id: RECORD_ID,
      render_profile: 'edit',
    });
    const attachments = contractResp.data?.views?.form?.attachments || {};
    const deleteContract = attachments.delete || {};
    const deletePolicy = deleteContract.delete_policy || {};
    const dom = await domAttachmentDeleteSurface(page);
    const dryRun = await intentRequest(page, 'api.data.unlink', {
      model: 'ir.attachment',
      ids: [1],
      dry_run: true,
      context: {},
    });

    summary.checks.push({
      path_id: 'P18',
      level: 'L4',
      scenario: 'attachment_delete_policy_denied_no_ui_delete',
      status: contractResp.ok
        && attachments.enabled === true
        && deleteContract.intent === 'api.data.unlink'
        && deleteContract.model === 'ir.attachment'
        && deleteContract.enabled === false
        && deletePolicy.reason_code === 'DELETE_POLICY_DENIED'
        && dom.attachment_block_count > 0
        && dom.delete_buttons === 0
        && dryRun.status === 403
        && dryRun.ok === false
        && dryRun.error?.reason_code === 'DELETE_POLICY_DENIED'
        ? 'pass'
        : 'fail',
      attachment_delete_contract: deleteContract,
      dom,
      dry_run_unlink: dryRun,
    });
    summary.actionable_console_errors = page.__consoleErrors.filter((line) =>
      !String(line).includes('favicon')
      && !String(line).includes('ResizeObserver')
      && !String(line).includes('403 (FORBIDDEN)'),
    );
    summary.pass = summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0;
    await page.screenshot({ path: path.join(outDir, 'attachment-delete-policy.png'), fullPage: true });
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
