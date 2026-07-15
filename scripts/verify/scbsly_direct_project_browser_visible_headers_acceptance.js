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
const { requireOnlineCapture } = require('./online_capture_security');

const OLD_CAPTURE = requireOnlineCapture('scbsly');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || '';
const PASSWORD = process.env.E2E_PASSWORD || '';
const OLD_BASE_URL = OLD_CAPTURE.baseUrl;
const OLD_LOGIN = OLD_CAPTURE.username;
const OLD_PASSWORD = OLD_CAPTURE.password;
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
const NEW_DIRECT_ROUTES = {
  '施工合同': { menuId: 743, actionId: 909 },
  '分包合同': { menuId: 744, actionId: 910 },
  '租赁合同': { menuId: 745, actionId: 911 },
  '供货合同': { menuId: 746, actionId: 912 },
  '供货合同（数据）': { menuId: 802, actionId: 900 },
  '劳务合同': { menuId: 747, actionId: 913 },
  '机械合同（合同）': { menuId: 748, actionId: 914 },
  '材料计划': { menuId: 749, actionId: 915 },
  '报价单': { menuId: 750, actionId: 916 },
  '入库': { menuId: 751, actionId: 917 },
  '材料结算单': { menuId: 752, actionId: 918 },
  '方单': { menuId: 754, actionId: 919 },
  '零星用工': { menuId: 755, actionId: 920 },
  '劳务结算': { menuId: 756, actionId: 921 },
  '分包方单': { menuId: 757, actionId: 922 },
  '分包结算单': { menuId: 758, actionId: 923 },
  '机械台班记录': { menuId: 759, actionId: 924 },
  '机械结算单': { menuId: 760, actionId: 925 },
  '租入': { menuId: 761, actionId: 935 },
  '还租': { menuId: 762, actionId: 936 },
  '租赁结算单': { menuId: 763, actionId: 926 },
  '项目费用报销单': { menuId: 764, actionId: 927 },
  '管理人员工资表': { menuId: 765, actionId: 928 },
  '油卡登记': { menuId: 766, actionId: 937 },
  '充值登记': { menuId: 767, actionId: 938 },
  '加油登记': { menuId: 768, actionId: 939 },
  '支付申请': { menuId: 769, actionId: 929 },
  '工程进度收款': { menuId: 770, actionId: 940 },
  '往来单位付款': { menuId: 771, actionId: 930 },
  '工程结算单': { menuId: 772, actionId: 931 },
  '进项上报': { menuId: 773, actionId: 932 },
  '总包进项上报': { menuId: 774, actionId: 933 },
  '施工日志（新）': { menuId: 776, actionId: 934 },
};
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
  function canonicalHeader(value) {
    return normalize(value).replace(/^查询\s+/, '');
  }
  const normalized = headers
    .map((item) => canonicalHeader(item))
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
  const directRoute = NEW_DIRECT_ROUTES[label];
  if (directRoute) {
    const actionId = Number(directRoute.actionId);
    const menuId = Number(directRoute.menuId);
    await page.goto(`${FRONTEND_URL}/a/${actionId}?menu_id=${menuId}&action_id=${actionId}`, {
      waitUntil: 'networkidle',
      timeout: 45000,
    });
    await page.waitForTimeout(1500);
    const headers = await renderedHeaders(page);
    await page.screenshot({ path: path.join(outDir, `new-${label}.png`), fullPage: true }).catch(() => undefined);
    return headers;
  }
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
