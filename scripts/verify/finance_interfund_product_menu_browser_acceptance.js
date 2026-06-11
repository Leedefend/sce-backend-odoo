#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

function loadPlaywright() {
  const candidates = [
    path.join(process.cwd(), 'frontend/apps/web/package.json'),
    path.join(process.cwd(), 'package.json'),
    '/tmp/sc-pw/package.json',
  ];
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) continue;
    try {
      return createRequire(candidate)('playwright');
    } catch (_err) {
      // Try the next candidate.
    }
  }
  return require('playwright');
}

const { chromium } = loadPlaywright();

const FRONTEND_URL = (process.env.FRONTEND_URL || 'http://127.0.0.1:18081').replace(/\/$/, '');
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const PRODUCT_KEY = process.env.PRODUCT_KEY || 'construction.standard';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts/verify';
const outDir = path.join(ARTIFACTS_DIR, 'finance-interfund-product-menu-browser', new Date().toISOString().replace(/[-:]/g, '').slice(0, 15));

const TARGET_MENU_XMLIDS = [
  'smart_construction_core.menu_sc_finance_project_capital_position',
  'smart_construction_core.menu_sc_finance_counterparty_position_summary',
  'smart_construction_core.menu_sc_finance_project_counterparty_position',
  'smart_construction_core.menu_sc_company_contractor_responsibility_summary',
  'smart_construction_core.menu_sc_company_contractor_responsibility_fact',
];

const DRILLDOWN_BUTTONS_BY_MODEL = {
  'sc.finance.project.capital.position': ['查看收付款明细', '查看借还调拨明细'],
  'sc.finance.project.counterparty.position': ['查看收付款明细', '查看借还调拨明细'],
  'sc.finance.counterparty.position.summary': ['查看项目资金往来'],
};

const EXPECTED_DRILLDOWN_ACTION_BY_LABEL = {
  查看收付款明细: 970,
  查看借还调拨明细: 969,
  查看项目资金往来: 974,
};

const FAIL_HINTS = ['页面加载失败', '无权以 write 访问模型', 'Access Error', 'RPC_ERROR', '当前视图使用可读降级渲染'];

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if ((await inputs.count()) > 2 && await inputs.nth(2).isEnabled().catch(() => false)) {
    await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const token = await authToken(page);
  const response = await page.evaluate(async ({ dbName, bearer, intentName, payload }) => {
    const resp = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Odoo-DB': dbName,
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `finance-interfund-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: { db: dbName, ...payload } }),
    });
    const body = await resp.json().catch(() => ({}));
    return { status: resp.status, body };
  }, { dbName: DB_NAME, bearer: token, intentName: intent, payload: params });
  if (response.body?.ok !== true) {
    throw new Error(`${intent} failed: ${JSON.stringify(response.body?.error || response.body).slice(0, 1000)}`);
  }
  return response.body.data || {};
}

async function listFirstRecordId(page, model) {
  const data = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    fields: ['id', 'display_name'],
    domain: [],
    limit: 1,
    offset: 0,
    order: '',
    context: {},
  });
  const records = Array.isArray(data.records) ? data.records : [];
  return Number(records[0]?.id || 0);
}

function walkMenuGroups(groups) {
  const rows = [];
  for (const group of Array.isArray(groups) ? groups : []) {
    for (const menu of Array.isArray(group.menus) ? group.menus : []) {
      rows.push({
        group: group.group_label || group.label || '',
        label: menu.label || menu.name || '',
        menuXmlid: menu.menu_xmlid || menu.menu_key || menu.page_key || '',
        actionId: Number(menu.action_id || 0),
        menuId: Number(menu.menu_id || 0),
        model: menu.res_model || '',
        route: menu.route || '',
      });
    }
  }
  return rows;
}

function walkNav(nodes, group = '') {
  const rows = [];
  for (const node of Array.isArray(nodes) ? nodes : []) {
    const meta = node.meta || {};
    const label = node.label || node.name || node.title || '';
    const xmlid = node.xmlid || node.menu_xmlid || meta.xmlid || meta.menu_xmlid || '';
    const actionId = Number(meta.action_id || node.action_id || 0);
    const menuId = Number(node.menu_id || meta.menu_id || node.id || 0);
    if (actionId && menuId) {
      rows.push({
        group,
        label,
        menuXmlid: xmlid,
        actionId,
        menuId,
        model: meta.model || node.model || '',
        route: node.route || meta.route || '',
      });
    }
    rows.push(...walkNav(node.children, group || label));
  }
  return rows;
}

async function runtimeProductMenus(page) {
  const nav = await intentRequest(page, 'system.init', {
    scene: 'web',
    with_preload: false,
    scene_ready_mode: 'registry',
    with: ['workspace_home'],
  });
  writeJson('system_init_debug.json', {
    keys: Object.keys(nav || {}),
    nav_sample: Array.isArray(nav?.nav) ? nav.nav.slice(0, 3) : null,
    release_nav_sample: Array.isArray(nav?.release_navigation_v1?.nav) ? nav.release_navigation_v1.nav.slice(0, 3) : null,
    delivery_nav_sample: Array.isArray(nav?.delivery_engine_v1?.nav) ? nav.delivery_engine_v1.nav.slice(0, 3) : null,
  });
  const candidates = [nav?.release_navigation_v1?.nav, nav?.delivery_engine_v1?.nav, nav?.nav];
  const navRows = walkNav(candidates.find((entry) => Array.isArray(entry)) || []);
  const groupRows = walkMenuGroups(nav?.menu_groups || nav?.nav?.menu_groups || []);
  const rows = [...navRows, ...groupRows];
  const byXmlid = rows.filter((row) => TARGET_MENU_XMLIDS.includes(row.menuXmlid));
  if (byXmlid.length) return byXmlid;
  const byLabel = rows.filter((row) => ['项目资金总览', '往来对象资金总览', '项目与对象资金往来', '公司-承包人资金责任余额', '公司-承包人资金责任明细'].includes(row.label));
  writeJson('runtime_menu_debug.json', {
    target_xmlids: TARGET_MENU_XMLIDS,
    matched_by_label: byLabel,
    finance_like_rows: rows.filter((row) => /资金|往来|口径/.test(row.label)).slice(0, 100),
  });
  return byLabel;
}

async function verifyMenu(browser, menu, index, storageState, token) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN', storageState });
  const page = await context.newPage();
  const consoleRows = [];
  const responseRows = [];
  const intentErrorRows = [];
  const pageErrors = [];
  const onConsole = (msg) => {
    if (['error', 'warning'].includes(msg.type())) {
      consoleRows.push({ type: msg.type(), text: msg.text().slice(0, 1000) });
    }
  };
  const onResponse = async (resp) => {
    const url = resp.url();
    if (!url.includes('/api/') && !url.includes('/web/')) return;
    let body = '';
    try {
      body = (await resp.text()).slice(0, 1200);
    } catch (_err) {
      body = '';
    }
    if (url.includes('/api/v1/intent') && body.includes('"intent":"execute_button"') && !body.includes('"ok":true')) {
      intentErrorRows.push({ status: resp.status(), url, body });
    }
    if (resp.status() >= 400) {
      responseRows.push({ status: resp.status(), url, body });
    }
  };
  const onPageError = (err) => pageErrors.push({ message: err.message, stack: String(err.stack || '').slice(0, 1200) });

  page.on('console', onConsole);
  page.on('response', onResponse);
  page.on('pageerror', onPageError);
  try {
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.evaluate(({ dbName, bearer }) => {
      sessionStorage.setItem(`sc_auth_token:${dbName}`, bearer);
    }, { dbName: DB_NAME, bearer: token });
    const contract = await intentRequest(page, 'ui.contract.v2', {
      op: 'action_open',
      action_id: menu.actionId,
      client_type: 'web_pc',
      delivery_profile: 'full',
    });
    writeJson(`contract_${index + 1}_${menu.menuXmlid.split('.').pop()}.json`, contract);
    const url = `${FRONTEND_URL}/a/${menu.actionId}?menu_id=${menu.menuId}`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForFunction(() => {
      const text = String(document.body?.textContent || '');
      return !text.includes('正在加载页面') && !text.includes('Loading');
    }, null, { timeout: 60000 }).catch(() => {});
    await page.waitForFunction((label) => {
      const text = String(document.body?.textContent || '');
      return text.includes(label)
        && !text.includes('正在加载列表')
        && !text.includes('正在加载页面')
        && !text.includes('Loading');
    }, menu.label, { timeout: 90000 }).catch(() => {});
    await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(1000);
    const bodyText = normalize(await page.locator('body').textContent().catch(() => ''));
    const screenshot = path.join(outDir, `menu_${index + 1}_${menu.menuXmlid.split('.').pop()}.png`);
    await page.screenshot({ path: screenshot, fullPage: true }).catch(() => {});
    const errors = [];
    for (const hint of FAIL_HINTS) {
      if (bodyText.includes(hint)) errors.push(`page_contains:${hint}`);
    }
    for (const row of responseRows) {
      errors.push(`http_${row.status}:${row.url}`);
    }
    for (const err of pageErrors) {
      errors.push(`pageerror:${err.message}`);
    }
    if (!bodyText.includes(menu.label)) {
      errors.push(`missing_page_label:${menu.label}`);
    }
    if (!bodyText) {
      errors.push('empty_body');
    }
    if (bodyText.includes('正在加载列表') || bodyText.includes('正在加载页面')) {
      errors.push('page_still_loading');
    }
    return {
      ...menu,
      status: errors.length ? 'FAIL' : 'PASS',
      errors,
      pageName: contract?.pageInfo?.pageName || '',
      viewType: contract?.pageInfo?.viewType || '',
      bodyExcerpt: bodyText.slice(0, 1200),
      console: consoleRows,
      responses: responseRows,
      pageErrors,
      screenshot,
    };
  } finally {
    page.off('console', onConsole);
    page.off('response', onResponse);
    page.off('pageerror', onPageError);
    await context.close().catch(() => {});
  }
}

async function verifyRecordDrilldown(browser, menu, index, storageState, token) {
  const buttons = DRILLDOWN_BUTTONS_BY_MODEL[menu.model] || [];
  if (!buttons.length) {
    return {
      ...menu,
      status: 'PASS',
      errors: [],
      skipped: 'no_drilldown_buttons',
    };
  }
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN', storageState });
  const page = await context.newPage();
  const consoleRows = [];
  const responseRows = [];
  const intentErrorRows = [];
  const pageErrors = [];
  const onConsole = (msg) => {
    if (['error', 'warning'].includes(msg.type())) {
      consoleRows.push({ type: msg.type(), text: msg.text().slice(0, 1000) });
    }
  };
  const onResponse = async (resp) => {
    const url = resp.url();
    if (!url.includes('/api/') && !url.includes('/web/')) return;
    let body = '';
    try {
      body = (await resp.text()).slice(0, 1200);
    } catch (_err) {
      body = '';
    }
    if (url.includes('/api/v1/intent') && body.includes('"intent":"execute_button"') && !body.includes('"ok":true')) {
      intentErrorRows.push({ status: resp.status(), url, body });
    }
    if (resp.status() >= 400) {
      responseRows.push({ status: resp.status(), url, body });
    }
  };
  const onPageError = (err) => pageErrors.push({ message: err.message, stack: String(err.stack || '').slice(0, 1200) });

  page.on('console', onConsole);
  page.on('response', onResponse);
  page.on('pageerror', onPageError);
  try {
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.evaluate(({ dbName, bearer }) => {
      sessionStorage.setItem(`sc_auth_token:${dbName}`, bearer);
    }, { dbName: DB_NAME, bearer: token });
    const recordId = await listFirstRecordId(page, menu.model);
    const errors = [];
    const buttonResults = [];
    if (!recordId) {
      errors.push(`no_record:${menu.model}`);
    }
    const recordUrl = `${FRONTEND_URL}/r/${encodeURIComponent(menu.model)}/${recordId}?action_id=${menu.actionId}&menu_id=${menu.menuId}`;
    for (const [buttonIndex, label] of buttons.entries()) {
      if (!recordId) break;
      responseRows.length = 0;
      intentErrorRows.length = 0;
      consoleRows.length = 0;
      pageErrors.length = 0;
      await page.goto(recordUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForFunction(() => {
        const text = String(document.body?.textContent || '');
        return !text.includes('正在加载页面') && !text.includes('Loading');
      }, null, { timeout: 60000 }).catch(() => {});
      await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(800);
      const beforeText = normalize(await page.locator('body').textContent().catch(() => ''));
      for (const hint of FAIL_HINTS) {
        if (beforeText.includes(hint)) errors.push(`record_page_contains:${hint}`);
      }
      const button = page.getByRole('button', { name: label }).first();
      if (!(await button.isVisible().catch(() => false))) {
        errors.push(`missing_button:${label}`);
        buttonResults.push({ label, status: 'FAIL', errors: [`missing_button:${label}`] });
        continue;
      }
      const expectedActionId = Number(EXPECTED_DRILLDOWN_ACTION_BY_LABEL[label] || 0);
      await button.click({ timeout: 10000 });
      if (expectedActionId) {
        await page.waitForURL((url) => url.pathname === `/a/${expectedActionId}`, { timeout: 30000 }).catch(() => {});
      }
      await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(500);
      const afterText = normalize(await page.locator('body').textContent().catch(() => ''));
      const buttonErrors = [];
      for (const hint of FAIL_HINTS) {
        if (afterText.includes(hint)) buttonErrors.push(`after_click_contains:${hint}`);
      }
      for (const row of responseRows) {
        buttonErrors.push(`http_${row.status}:${row.url}`);
      }
      for (const row of intentErrorRows) {
        buttonErrors.push(`intent_error_${row.status}:${row.body}`);
      }
      for (const row of consoleRows) {
        if (row.text.includes('intent=execute_button') && row.text.includes('status=error')) {
          buttonErrors.push(`console_error:${row.text}`);
        }
      }
      for (const err of pageErrors) {
        buttonErrors.push(`pageerror:${err.message}`);
      }
      const currentPath = new URL(page.url()).pathname;
      if (expectedActionId && currentPath !== `/a/${expectedActionId}`) {
        buttonErrors.push(`unexpected_route:${currentPath}:expected=/a/${expectedActionId}`);
      }
      if (buttonErrors.length) {
        errors.push(...buttonErrors.map((item) => `${label}:${item}`));
      }
      const screenshot = path.join(outDir, `drilldown_${index + 1}_${buttonIndex + 1}_${menu.menuXmlid.split('.').pop()}.png`);
      await page.screenshot({ path: screenshot, fullPage: true }).catch(() => {});
      buttonResults.push({
        label,
        status: buttonErrors.length ? 'FAIL' : 'PASS',
        errors: buttonErrors,
        bodyExcerpt: afterText.slice(0, 1000),
        screenshot,
      });
    }
    return {
      ...menu,
      recordId,
      status: errors.length ? 'FAIL' : 'PASS',
      errors,
      buttons: buttonResults,
      console: consoleRows,
      responses: responseRows,
      pageErrors,
    };
  } finally {
    page.off('console', onConsole);
    page.off('response', onResponse);
    page.off('pageerror', onPageError);
    await context.close().catch(() => {});
  }
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH || process.env.CHROMIUM_PATH || '';
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const results = [];
  const drilldownResults = [];
  try {
    await login(page);
    const menus = await runtimeProductMenus(page);
    if (menus.length !== TARGET_MENU_XMLIDS.length) {
      throw new Error(`runtime product menu count mismatch expected=${TARGET_MENU_XMLIDS.length} actual=${menus.length}`);
    }
    const storageState = await context.storageState();
    const token = await authToken(page);
    for (const [index, menu] of menus.entries()) {
      const result = await verifyMenu(browser, menu, index, storageState, token);
      results.push(result);
      console.log(`${result.status} ${result.group}/${result.label} action=${result.actionId} menu=${result.menuId}${result.errors.length ? ` errors=${result.errors.join('|')}` : ''}`);
      const drilldown = await verifyRecordDrilldown(browser, menu, index, storageState, token);
      drilldownResults.push(drilldown);
      console.log(`${drilldown.status} drilldown ${drilldown.label} model=${drilldown.model} record=${drilldown.recordId || '-'}${drilldown.errors.length ? ` errors=${drilldown.errors.join('|')}` : ''}`);
    }
  } finally {
    await context.close().catch(() => {});
    await browser.close();
  }
  const payload = {
    status: [...results, ...drilldownResults].every((row) => row.status === 'PASS') ? 'PASS' : 'FAIL',
    frontend_url: FRONTEND_URL,
    db: DB_NAME,
    login: LOGIN,
    product_key: PRODUCT_KEY,
    artifact_dir: outDir,
    results,
    drilldown_results: drilldownResults,
  };
  writeJson('summary.json', payload);
  if (payload.status !== 'PASS') {
    console.error(`[finance_interfund_product_menu_browser_acceptance] FAIL artifacts=${outDir}`);
    process.exit(1);
  }
  console.log(`[finance_interfund_product_menu_browser_acceptance] PASS artifacts=${outDir}`);
}

main().catch((err) => {
  writeJson('browser_error.json', { message: err.message, stack: err.stack });
  console.error(`[finance_interfund_product_menu_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
