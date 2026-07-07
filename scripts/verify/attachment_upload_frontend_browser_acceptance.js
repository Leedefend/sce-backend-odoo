#!/usr/bin/env node
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5179';
const DB_NAME = process.env.DB_NAME || 'sc_prod';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = Number(process.env.RECORD_ID || 0);
const ACTION_ID = process.env.ACTION_ID || '';
const MENU_ID = process.env.MENU_ID || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'attachment-upload-frontend-browser', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function routeForRecord() {
  if (!RECORD_ID) {
    throw new Error('RECORD_ID is required');
  }
  const params = new URLSearchParams();
  if (MENU_ID) params.set('menu_id', MENU_ID);
  if (ACTION_ID) params.set('action_id', ACTION_ID);
  const qs = params.toString();
  return `${FRONTEND_URL}/r/${encodeURIComponent(MODEL)}/${RECORD_ID}${qs ? `?${qs}` : ''}`;
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.__httpErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      let intent = '';
      try {
        const body = response.request().postData() || '';
        const parsed = body ? JSON.parse(body) : {};
        intent = parsed.intent || '';
      } catch {
        intent = '';
      }
      page.__httpErrors.push({
        status: response.status(),
        url: response.url(),
        method: response.request().method(),
        intent,
      });
    }
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
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ dbName, bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `attachment-upload-browser-${Date.now()}`,
      },
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
  }, { dbName: DB_NAME, bearer: token, intentName: intent, payload: params });
}

async function openForm(page) {
  await page.goto(routeForRecord(), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.template-layout-shell').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const shell = document.querySelector('.template-layout-shell');
    const text = String(shell?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function uploadViaNativeForm(page, fixturePath, fileName) {
  const uploadResponsePromise = page.waitForResponse(async (response) => {
    if (!response.url().includes('/api/v1/intent')) return false;
    if (response.request().method() !== 'POST') return false;
    const body = response.request().postData() || '';
    return body.includes('"file.upload"');
  }, { timeout: 30000 });

  const input = page.locator('.native-attachment-upload input[type="file"]').first();
  await input.waitFor({ state: 'attached', timeout: 20000 });
  await input.setInputFiles(fixturePath);
  const uploadResponse = await uploadResponsePromise;
  const uploadBody = await uploadResponse.json().catch(() => ({}));
  if (uploadResponse.status() !== 200 || uploadBody.ok !== true) {
    throw new Error(`file.upload failed status=${uploadResponse.status()} body=${JSON.stringify(uploadBody).slice(0, 500)}`);
  }
  const attachmentId = Number(uploadBody?.data?.id || 0);
  if (!attachmentId) throw new Error('file.upload response missing attachment id');

  await page.getByText(fileName, { exact: false }).waitFor({ timeout: 30000 });
  return { attachmentId, uploadBody };
}

async function downloadViaUi(page, fileName, expectedBuffer) {
  const entry = page.locator('li.native-chatter-entry').filter({ hasText: fileName }).first();
  const openButton = entry.locator('button.native-attachment-download').first();
  await openButton.waitFor({ timeout: 20000 });
  await openButton.click();
  const viewer = page.locator('.attachment-viewer').first();
  await viewer.waitFor({ timeout: 20000 });
  await viewer.getByText(fileName, { exact: false }).waitFor({ timeout: 20000 });
  await viewer.locator('.attachment-viewer-state--error').waitFor({ state: 'detached', timeout: 20000 }).catch(() => {});
  const downloadButton = viewer.getByRole('button', { name: /^下载$/ }).first();
  await downloadButton.waitFor({ timeout: 20000 });
  const downloadPromise = page.waitForEvent('download');
  await downloadButton.click();
  const download = await downloadPromise;
  const suggested = download.suggestedFilename() || fileName;
  const savedPath = path.join(outDir, `downloaded-${suggested}`);
  await download.saveAs(savedPath);
  const actual = fs.readFileSync(savedPath);
  return {
    suggested_filename: suggested,
    saved_path: savedPath,
    size: actual.length,
    sha256: sha256(actual),
    content_matched: actual.equals(expectedBuffer),
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const fileName = `production upload acceptance ${Date.now()}.txt`;
  const fixtureText = `production upload acceptance\nmodel=${MODEL}\nrecord_id=${RECORD_ID}\ndb=${DB_NAME}\nts=${new Date().toISOString()}\n`;
  const fixtureBuffer = Buffer.from(fixtureText, 'utf8');
  const fixturePath = path.join(outDir, fileName);
  fs.writeFileSync(fixturePath, fixtureBuffer);

  const result = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID || null,
    menu_id: MENU_ID || null,
    frontend_url: FRONTEND_URL,
    artifact_dir: outDir,
    fixture: {
      file_name: fileName,
      path: fixturePath,
      size: fixtureBuffer.length,
      sha256: sha256(fixtureBuffer),
    },
  };

  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);
    await openForm(page);
    await page.screenshot({ path: path.join(outDir, 'before_upload.png'), fullPage: true });

    const upload = await uploadViaNativeForm(page, fixturePath, fileName);
    result.upload = {
      attachment_id: upload.attachmentId,
      response: upload.uploadBody,
    };

    const downloadResp = await intentRequest(page, 'file.download', { id: upload.attachmentId });
    const downloadedByIntent = Buffer.from(downloadResp.data?.datas || '', 'base64');
    result.intent_download = {
      status: downloadResp.status,
      ok: downloadResp.ok,
      size: downloadedByIntent.length,
      sha256: sha256(downloadedByIntent),
      content_matched: downloadedByIntent.equals(fixtureBuffer),
      name: downloadResp.data?.name || '',
      mimetype: downloadResp.data?.mimetype || '',
      type: downloadResp.data?.type || '',
    };

    result.ui_download = await downloadViaUi(page, fileName, fixtureBuffer);
    result.console_errors = page.__consoleErrors || [];
    result.http_errors = page.__httpErrors || [];
    await page.screenshot({ path: path.join(outDir, 'after_upload.png'), fullPage: true });
    await context.close();

    result.pass = Boolean(
      result.upload.attachment_id
      && result.intent_download.ok
      && result.intent_download.content_matched
      && result.ui_download.content_matched
      && result.console_errors.length === 0,
    );
    writeJson('summary.json', result);
    console.log(JSON.stringify({
      pass: result.pass,
      artifact_dir: result.artifact_dir,
      attachment_id: result.upload.attachment_id,
      fixture_sha256: result.fixture.sha256,
      intent_download_sha256: result.intent_download.sha256,
      ui_download_sha256: result.ui_download.sha256,
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(JSON.stringify({ pass: false, artifact_dir: outDir, error: result.error }, null, 2));
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
