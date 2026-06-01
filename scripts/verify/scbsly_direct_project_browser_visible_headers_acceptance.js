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

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const OLD_BASE_URL = (process.env.SCBSLY_BASE_URL || 'https://www.builderp.cn/SCBSLY_V2').replace(/\/$/, '');
const OLD_LOGIN = process.env.SCBSLY_USERNAME || process.env.OLD_SCBS_USERNAME || '';
const OLD_PASSWORD = process.env.SCBSLY_PASSWORD || process.env.OLD_SCBS_PASSWORD || '';
const OLD_MENU_EVIDENCE = process.env.SCBSLY_MENU_EVIDENCE
  || 'artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json';
const HEADLESS = String(process.env.HEADLESS || '1').trim() !== '0';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const LABEL_FILTER = new Set(
  String(process.env.STRICT_ACCEPTANCE_LABELS || '')
    .split(/[,，]/)
    .map((item) => normalize(item))
    .filter(Boolean),
);
const CATEGORY_FILTER = normalize(process.env.STRICT_ACCEPTANCE_CATEGORY || '');
const OUT_DIR = path.join(
  ARTIFACTS_DIR,
  'browser',
  'scbsly-direct-project-visible-headers',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function loadJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function businessHeaders(headers) {
  const normalized = headers
    .map((item) => normalize(item))
    .filter((item) => item && item !== '序号' && item !== '列');
  if (normalized.length % 2 === 0) {
    const middle = normalized.length / 2;
    const left = normalized.slice(0, middle);
    const right = normalized.slice(middle);
    if (JSON.stringify(left) === JSON.stringify(right)) return left;
  }
  return normalized;
}

function diffHeaders(oldHeaders, newHeaders) {
  const max = Math.max(oldHeaders.length, newHeaders.length);
  const diffs = [];
  for (let index = 0; index < max; index += 1) {
    if ((oldHeaders[index] || '') !== (newHeaders[index] || '')) {
      diffs.push({
        index: index + 1,
        old: oldHeaders[index] || '',
        new: newHeaders[index] || '',
      });
    }
  }
  return diffs;
}

async function oldLogin(page) {
  if (!OLD_LOGIN || !OLD_PASSWORD) {
    throw new Error('SCBSLY_USERNAME/SCBSLY_PASSWORD are required');
  }
  await page.goto(`${OLD_BASE_URL}/System/User/Login`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.locator('input').nth(0).fill(OLD_LOGIN);
  await page.locator('input').nth(1).fill(OLD_PASSWORD);
  await page.locator('text=立即登录').click();
  await page.waitForURL(/\/System\/Project\/SelectDefaultProject|\/Home|\/Index|\/LowCode\//, {
    timeout: 60000,
  }).catch(() => undefined);
}

async function newLogin(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const dbInput = page.locator('input[autocomplete="off"]');
  if (await dbInput.isEditable().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
  await page.waitForSelector('[data-component="SidebarNav"] .menu', { timeout: 30000 });
}

async function expandAllVisibleMenuToggles(page) {
  for (let round = 0; round < 40; round += 1) {
    const clicked = await page.evaluate(() => {
      function isVisible(element) {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== 'none'
          && style.visibility !== 'hidden'
          && rect.width > 0
          && rect.height > 0;
      }
      const toggles = Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.toggle'))
        .filter((button) => isVisible(button) && String(button.textContent || '').includes('▸'));
      for (const button of toggles) button.click();
      return toggles.length;
    });
    if (!clicked) break;
    await page.waitForTimeout(120);
  }
}

async function renderedHeaders(page) {
  await page.waitForSelector('thead th, [role="columnheader"]', { timeout: 45000 });
  return page.evaluate(() => {
    function clean(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }
    const selectors = [
      'thead th',
      '.o_list_renderer table thead th',
      '.el-table__header th',
      '.vxe-table--header th',
      '[role="columnheader"]',
    ];
    for (const selector of selectors) {
      const headers = Array.from(document.querySelectorAll(selector))
        .map((node) => clean(node.innerText || node.textContent))
        .filter(Boolean);
      if (headers.length) return headers;
    }
    return [];
  });
}

async function openOldList(page, row, outDir) {
  await page.goto(`${OLD_BASE_URL}/${row.link_url}`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);
  const headers = await renderedHeaders(page);
  await page.screenshot({ path: path.join(outDir, `old-${row.label}.png`), fullPage: true }).catch(() => undefined);
  return headers;
}

async function openNewAcceptanceMenu(page, label, outDir) {
  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => undefined);
  await page.waitForSelector('[data-component="SidebarNav"] .menu', { timeout: 30000 });
  await expandAllVisibleMenuToggles(page);
  let clicked = await page.evaluate((targetLabel) => {
    function clean(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }
    const buttons = Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.label'));
    const button = buttons.find((item) => clean(item.textContent) === targetLabel);
    if (!button) return false;
    button.scrollIntoView({ block: 'center' });
    button.click();
    return true;
  }, label);
  if (!clicked) {
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => undefined);
    await page.waitForSelector('[data-component="SidebarNav"] .menu', { timeout: 30000 });
    await expandAllVisibleMenuToggles(page);
    clicked = await page.evaluate((targetLabel) => {
      function clean(value) {
        return String(value || '').replace(/\s+/g, ' ').trim();
      }
      const buttons = Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.label'));
      const button = buttons.find((item) => clean(item.textContent) === targetLabel);
      if (!button) return false;
      button.scrollIntoView({ block: 'center' });
      button.click();
      return true;
    }, label);
  }
  if (!clicked) {
    throw new Error(`new acceptance menu not found: ${label}`);
  }
  await page.waitForURL(/action_id=/, { timeout: 15000 }).catch(() => undefined);
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
  await page.waitForTimeout(1500);
  const headers = await renderedHeaders(page);
  await page.screenshot({ path: path.join(outDir, `new-${label}.png`), fullPage: true }).catch(() => undefined);
  return headers;
}

async function main() {
  ensureDir(OUT_DIR);
  const evidence = loadJson(OLD_MENU_EVIDENCE);
  const rows = (evidence.rows || [])
    .filter((row) => !CATEGORY_FILTER || normalize(row.category) === CATEGORY_FILTER)
    .filter((row) => LABEL_FILTER.size === 0 || LABEL_FILTER.has(normalize(row.label)))
    .filter((row) => normalize(row.route_kind) === 'lowcode_form_list' && normalize(row.link_url));
  if (!rows.length) {
    throw new Error('no form-list rows matched the requested filters');
  }

  const browser = await chromium.launch({ headless: HEADLESS });
  const oldPage = await browser.newPage({ locale: 'zh-CN', viewport: { width: 1800, height: 1000 } });
  const newPage = await browser.newPage({ locale: 'zh-CN', viewport: { width: 1800, height: 1000 } });
  const resultRows = [];
  try {
    await oldLogin(oldPage);
    await newLogin(newPage);
    for (const row of rows) {
      const label = normalize(row.label);
      const oldRawHeaders = await openOldList(oldPage, row, OUT_DIR);
      const newRawHeaders = await openNewAcceptanceMenu(newPage, label, OUT_DIR);
      const oldHeaders = businessHeaders(oldRawHeaders);
      const newHeaders = businessHeaders(newRawHeaders);
      const diffs = diffHeaders(oldHeaders, newHeaders);
      resultRows.push({
        label,
        category: normalize(row.category),
        status: diffs.length ? 'FAIL' : 'PASS',
        old_header_count: oldHeaders.length,
        new_header_count: newHeaders.length,
        old_headers: oldHeaders,
        new_headers: newHeaders,
        raw_old_headers: oldRawHeaders,
        raw_new_headers: newRawHeaders,
        diff_sample: diffs.slice(0, 20),
      });
      console.log(`${label}: old=${oldHeaders.length} new=${newHeaders.length} ${diffs.length ? 'FAIL' : 'PASS'}`);
    }
  } finally {
    await browser.close();
  }

  const failures = resultRows.filter((row) => row.status !== 'PASS');
  const report = {
    ok: failures.length === 0,
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    old_base_url: OLD_BASE_URL,
    filters: {
      category: CATEGORY_FILTER,
      labels: Array.from(LABEL_FILTER),
    },
    out_dir: OUT_DIR,
    rows: resultRows,
    failures,
  };
  fs.writeFileSync(path.join(OUT_DIR, 'report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(`SCBSLY_DIRECT_PROJECT_BROWSER_VISIBLE_HEADERS=${report.ok ? 'PASS' : 'FAIL'} output=${path.join(OUT_DIR, 'report.json')}`);
  if (!report.ok) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
