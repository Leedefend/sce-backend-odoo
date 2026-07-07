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

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5179';
const DB_NAME = process.env.DB_NAME || 'sc_prod';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const SAMPLE_JSON = process.env.LEGACY_ATTACHMENT_BROWSER_SAMPLES || '';

const DEFAULT_SAMPLES = [
  {
    label: 'legacy-image',
    mode: 'preview',
    id: 971,
    name: '2.jpg',
    mimetype: 'image/jpeg',
  },
  {
    label: 'legacy-pdf',
    mode: 'preview',
    id: 977,
    name: '施工合同.pdf',
    mimetype: 'application/pdf',
  },
  {
    label: 'legacy-docx',
    mode: 'download',
    id: 999,
    name: '董礼兵身份证.docx',
    mimetype: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  },
];

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'legacy-attachment-frontend-browser', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function parseSamples() {
  if (!SAMPLE_JSON) return DEFAULT_SAMPLES;
  const parsed = JSON.parse(SAMPLE_JSON);
  if (!Array.isArray(parsed) || !parsed.length) {
    throw new Error('LEGACY_ATTACHMENT_BROWSER_SAMPLES must be a non-empty JSON array');
  }
  return parsed;
}

function redactToken(value) {
  const text = String(value || '');
  if (!text) return '';
  return `${text.slice(0, 12)}...${text.slice(-8)}`;
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).count().catch(() => 0)) {
    const disabled = await inputs.nth(2).isDisabled().catch(() => false);
    if (!disabled) await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForTimeout(3500);
  const token = await page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
  if (!token) {
    throw new Error('frontend login did not create auth token');
  }
  return token;
}

async function intentFileDownload(page, token, params) {
  return page.evaluate(async ({ dbName, authToken, requestParams }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        'X-Odoo-DB': dbName,
        'X-Trace-Id': `legacy_attachment_browser_${Date.now()}`,
      },
      credentials: 'omit',
      body: JSON.stringify({
        intent: 'file.download',
        params: requestParams,
        meta: { startup_chain_bypass: true },
      }),
    });
    const body = await response.json().catch(() => ({}));
    return { status: response.status, body };
  }, { dbName: DB_NAME, authToken: token, requestParams: params });
}

async function renderPreview(page, sample, payload) {
  return page.evaluate(async ({ label, name, mimetype, datas }) => {
    const binary = atob(datas || '');
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    const blob = new Blob([bytes], { type: mimetype || 'application/octet-stream' });
    const objectUrl = URL.createObjectURL(blob);
    const root = document.createElement('section');
    root.setAttribute('data-legacy-attachment-preview', label);
    root.style.cssText = 'padding:16px;font-family:Arial, sans-serif;';
    const title = document.createElement('h1');
    title.textContent = name;
    title.style.cssText = 'font-size:18px;margin:0 0 12px;';
    root.appendChild(title);
    document.body.replaceChildren(root);
    if ((mimetype || '').startsWith('image/')) {
      const image = document.createElement('img');
      image.src = objectUrl;
      image.alt = name;
      image.style.cssText = 'max-width:720px;max-height:520px;border:1px solid #d7dee8;';
      root.appendChild(image);
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = () => reject(new Error('image preview failed to load'));
      });
      return {
        preview_kind: 'image',
        natural_width: image.naturalWidth,
        natural_height: image.naturalHeight,
        object_url_created: objectUrl.startsWith('blob:'),
      };
    }
    const iframe = document.createElement('iframe');
    iframe.src = objectUrl;
    iframe.title = name;
    iframe.style.cssText = 'width:760px;height:540px;border:1px solid #d7dee8;';
    root.appendChild(iframe);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    return {
      preview_kind: 'iframe',
      object_url_created: objectUrl.startsWith('blob:'),
      bytes: bytes.length,
      header: Array.from(bytes.slice(0, 5)).map((item) => String.fromCharCode(item)).join(''),
    };
  }, {
    label: sample.label,
    name: payload.name || sample.name,
    mimetype: payload.mimetype || sample.mimetype,
    datas: payload.datas || '',
  });
}

async function triggerBrowserDownload(page, sample, payload) {
  const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
  await page.evaluate(({ name, mimetype, datas }) => {
    const binary = atob(datas || '');
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    const blob = new Blob([bytes], { type: mimetype || 'application/octet-stream' });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = name || 'download';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }, {
    name: payload.name || sample.name,
    mimetype: payload.mimetype || sample.mimetype,
    datas: payload.datas || '',
  });
  const download = await downloadPromise;
  const targetPath = path.join(outDir, `downloaded-${sample.label}-${download.suggestedFilename() || sample.name || 'file'}`);
  await download.saveAs(targetPath);
  const file = fs.readFileSync(targetPath);
  return {
    suggested_filename: download.suggestedFilename(),
    saved_path: targetPath,
    saved_bytes: file.length,
    zip_header: file.slice(0, 2).toString('ascii') === 'PK',
  };
}

function responseData(envelope) {
  const body = envelope.body || {};
  if (body.ok === false) {
    throw new Error(`file.download failed: ${JSON.stringify(body.error || body)}`);
  }
  if (body.data && body.data.datas !== undefined) return body.data;
  if (body.result && body.result.datas !== undefined) return body.result;
  throw new Error(`file.download response missing data: ${JSON.stringify(body).slice(0, 500)}`);
}

async function main() {
  const samples = parseSamples();
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    scope: 'legacy_attachment_frontend_browser_acceptance',
    frontend_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    artifacts: outDir,
    samples: [],
    pass: false,
  };
  try {
    const context = await browser.newContext({ locale: 'zh-CN', acceptDownloads: true });
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));
    const token = await login(page);
    result.token = redactToken(token);

    for (const sample of samples) {
      const params = sample.url
        ? {
          url: sample.url,
          model: sample.res_model,
          res_id: sample.res_id,
          name: sample.name,
        }
        : { id: sample.id, name: sample.name };
      const envelope = await intentFileDownload(page, token, params);
      const payload = responseData(envelope);
      const datas = String(payload.datas || '');
      const buffer = Buffer.from(datas, 'base64');
      const item = {
        label: sample.label,
        id: sample.id,
        request_mode: sample.url ? 'url' : 'id',
        name: payload.name,
        mimetype: payload.mimetype,
        res_model: payload.res_model,
        res_id: payload.res_id,
        http_status: envelope.status,
        has_datas: Boolean(datas),
        decoded_bytes: buffer.length,
        legacy_url_prefix: String(payload.legacy_url || payload.url || '').slice(0, 32),
      };
      if (!item.has_datas || item.decoded_bytes <= 0) {
        item.status = 'fail';
        item.error = 'download returned empty datas';
      } else if (sample.mode === 'download') {
        item.browser_download = await triggerBrowserDownload(page, sample, payload);
        item.status = item.browser_download.saved_bytes === item.decoded_bytes ? 'pass' : 'fail';
      } else {
        item.preview = await renderPreview(page, sample, payload);
        await page.screenshot({ path: path.join(outDir, `${sample.label}.png`), fullPage: true });
        if ((payload.mimetype || '').startsWith('image/')) {
          item.status = item.preview.natural_width > 0 && item.preview.natural_height > 0 ? 'pass' : 'fail';
        } else if (payload.mimetype === 'application/pdf') {
          item.status = item.preview.header === '%PDF-' ? 'pass' : 'fail';
        } else {
          item.status = item.preview.object_url_created ? 'pass' : 'fail';
        }
      }
      result.samples.push(item);
    }
    result.console_errors = consoleErrors;
    result.pass = result.samples.every((item) => item.status === 'pass') && consoleErrors.length === 0;
    await context.close();
    writeJson('summary.json', result);
    console.log(JSON.stringify({ pass: result.pass, artifacts: outDir, samples: result.samples }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(JSON.stringify({ pass: false, artifacts: outDir, error: result.error }, null, 2));
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
