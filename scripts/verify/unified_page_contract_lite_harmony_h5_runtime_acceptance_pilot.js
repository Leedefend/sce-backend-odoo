#!/usr/bin/env node
'use strict';

const fs = require('fs');
const http = require('http');
const path = require('path');
const { createRequire } = require('module');

const root = process.cwd();
const requireFromWeb = createRequire(path.join(root, 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const distRoot = path.join(root, 'frontend/apps/mobile/dist/build/h5');
const makefilePath = path.join(root, 'Makefile');
const reportPath = process.env.REPORT || path.join(root, 'artifacts/backend/unified_page_contract_lite_harmony_h5_runtime_acceptance_pilot.json');

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

function fail(message) {
  throw new Error(message);
}

function contentType(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8';
  if (file.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (file.endsWith('.css')) return 'text/css; charset=utf-8';
  if (file.endsWith('.json')) return 'application/json; charset=utf-8';
  return 'application/octet-stream';
}

function createStaticServer(rootDir) {
  return http.createServer((req, res) => {
    const requestPath = decodeURIComponent((req.url || '/').split('?')[0]);
    const relativePath = requestPath === '/' ? 'index.html' : requestPath.replace(/^\/+/, '');
    const filePath = path.normalize(path.join(rootDir, relativePath));
    if (!filePath.startsWith(rootDir)) {
      res.writeHead(403);
      res.end('forbidden');
      return;
    }
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      res.writeHead(404);
      res.end('not found');
      return;
    }
    res.writeHead(200, { 'content-type': contentType(filePath) });
    fs.createReadStream(filePath).pipe(res);
  });
}

async function listen(server) {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  if (!address || typeof address === 'string') fail('failed to allocate local static server port');
  return `http://127.0.0.1:${address.port}`;
}

async function main() {
  const errors = [];
  const observations = [];
  const makefile = fs.existsSync(makefilePath) ? fs.readFileSync(makefilePath, 'utf8') : '';
  if (!makefile.includes('verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host')) {
    errors.push('Makefile target missing: verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host');
  }

  const requiredFiles = [
    'index.html',
  ];
  const assetFiles = fs.existsSync(path.join(distRoot, 'assets'))
    ? fs.readdirSync(path.join(distRoot, 'assets')).map((name) => `assets/${name}`)
    : [];
  if (!assetFiles.some((name) => /^assets\/index-.+\.js$/.test(name))) {
    errors.push('missing compiled H5 index JavaScript asset');
  }
  if (!assetFiles.some((name) => /^assets\/pages-contract-index\..+\.js$/.test(name))) {
    errors.push('missing compiled H5 contract page JavaScript asset');
  }
  if (!assetFiles.some((name) => /^assets\/pages-login-index\..+\.js$/.test(name))) {
    errors.push('missing compiled H5 login page JavaScript asset');
  }
  if (!assetFiles.some((name) => /^assets\/pages-home-index\..+\.js$/.test(name))) {
    errors.push('missing compiled H5 home page JavaScript asset');
  }
  if (!assetFiles.some((name) => /^assets\/uni\..+\.css$/.test(name))) {
    errors.push('missing compiled H5 UniApp CSS asset');
  }
  for (const file of requiredFiles) {
    const absolute = path.join(distRoot, file);
    if (fs.existsSync(absolute)) observations.push(`artifact exists: ${path.relative(root, absolute)}`);
    else errors.push(`missing compiled artifact: ${path.relative(root, absolute)}`);
  }

  let browser;
  let server;
  let renderedText = '';
  let url = '';
  const consoleErrors = [];
  const pageErrors = [];
  try {
    if (errors.length) fail(errors.join('; '));
    server = createStaticServer(distRoot);
    url = await listen(server);
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, locale: 'zh-CN' });
    page.on('console', (message) => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });
    page.on('pageerror', (error) => pageErrors.push(error.message));
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.getByText('智能工程项目管理系统').waitFor({ timeout: 10000 });
    renderedText = await page.locator('body').innerText({ timeout: 5000 });
    if (!renderedText.includes('智能工程项目管理系统') || !renderedText.includes('服务地址')) {
      errors.push('H5 page did not render mobile login text');
    }
    if (consoleErrors.length) errors.push('browser console errors detected');
    if (pageErrors.length) errors.push('browser page errors detected');
  } catch (error) {
    errors.push(error.message);
  } finally {
    if (browser) await browser.close().catch(() => undefined);
    if (server) await new Promise((resolve) => server.close(resolve));
  }

  const report = {
    ok: errors.length === 0,
    clientType: 'harmony_h5',
    decision: errors.length === 0 ? 'harmony_h5_runtime_browser_acceptance_pilot_passed' : 'blocked',
    distRoot: path.relative(root, distRoot),
    url,
    renderedText,
    consoleErrors,
    pageErrors,
    observations,
    errors,
  };
  writeJson(reportPath, report);

  if (errors.length) {
    console.error('Unified Semantic Page Contract Lite harmony_h5 runtime browser acceptance pilot failed:');
    for (const error of errors) console.error(`- ${error}`);
    console.error(`- report: ${reportPath}`);
    process.exit(1);
  }

  console.log('Unified Semantic Page Contract Lite harmony_h5 runtime browser acceptance pilot passed');
  console.log('- decision: harmony_h5_runtime_browser_acceptance_pilot_passed');
  console.log(`- report: ${reportPath}`);
}

main().catch((error) => {
  writeJson(reportPath, {
    ok: false,
    clientType: 'harmony_h5',
    decision: 'blocked',
    errors: [error.message],
  });
  console.error(`Unified Semantic Page Contract Lite harmony_h5 runtime browser acceptance pilot failed: ${error.message}`);
  process.exit(1);
});
