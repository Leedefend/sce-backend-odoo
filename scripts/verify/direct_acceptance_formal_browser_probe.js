#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const { requestJson } = require(path.join(process.cwd(), 'scripts/verify/http_smoke_utils.js'));

const requireFromRoot = createRequire(path.join(process.cwd(), 'frontend/apps/web/package.json'));
const { chromium } = requireFromRoot('playwright');

const BASE = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const OUT_DIR = path.join(
  process.env.ARTIFACTS_DIR || 'artifacts',
  'browser',
  'direct-acceptance-formal-menu',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);
const HEADLESS = String(process.env.HEADLESS || '1') !== '0';

const SPECS = [
  ['材料计划', 'smart_construction_core.menu_project_material_plan', 'project.material.plan', 686],
  ['报价单', 'smart_construction_core.menu_sc_material_quote_acceptance', 'sc.material.rfq', 126],
  ['入库', 'smart_construction_core.menu_sc_material_inbound', 'sc.material.inbound', 13184],
  ['方单', 'smart_construction_core.menu_sc_labor_usage_acceptance', 'sc.labor.usage', 252],
  ['零星用工', 'smart_construction_core.menu_sc_labor_casual_acceptance', 'sc.labor.usage', 8794],
  ['分包方单', 'smart_construction_core.menu_sc_subcontract_request_acceptance', 'sc.subcontract.request', 721],
  ['机械台班记录', 'smart_construction_core.menu_sc_equipment_shift_acceptance', 'sc.equipment.usage', 17502],
  ['租入', 'smart_construction_core.menu_sc_material_rental_in_acceptance', 'sc.material.rental.order', 166],
  ['还租', 'smart_construction_core.menu_sc_material_rental_return_acceptance', 'sc.material.rental.order', 37],
  ['管理人员工资表', 'smart_construction_core.menu_sc_salary_registration', 'sc.hr.payroll.document', 233],
  ['油卡登记', 'smart_construction_core.menu_sc_legacy_fuel_card_fact_acceptance', 'sc.fund.account.operation', 8],
  ['充值登记', 'smart_construction_core.menu_sc_legacy_fuel_card_recharge_fact_acceptance', 'sc.fund.account.operation', 32],
  ['施工日志（新）', 'smart_construction_core.menu_sc_construction_diary', 'sc.construction.diary', 3233],
];

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function intent(token, intentName, params = {}, anonymous = false) {
  const headers = { 'X-Odoo-DB': DB, 'X-Trace-Id': `formal-browser-${Date.now()}` };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (anonymous) headers['X-Anonymous-Intent'] = 'true';
  const resp = await requestJson(
    `${BASE.replace(/\/$/, '')}/api/v1/intent?db=${encodeURIComponent(DB)}&t=${Date.now()}`,
    { intent: intentName, params },
    headers,
  );
  if (resp.status < 200 || resp.status >= 300 || !resp.body || resp.body.ok === false) {
    throw new Error(`${intentName} failed: ${JSON.stringify(resp.body && (resp.body.error || resp.body))}`);
  }
  return resp.body.data || {};
}

function flattenNav(nodes, ancestors = [], out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== 'object') continue;
    const label = normalize(node.label || node.title || node.name);
    const pathLabels = [...ancestors, label].filter(Boolean);
    const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
    const actionId = Number(meta.action_id || node.action_id || 0);
    const model = normalize(meta.model || node.model);
    const menuXmlid = normalize(meta.menu_xmlid || node.menu_xmlid || node.xmlid);
    const menuId = Number(meta.menu_id || node.menu_id || 0);
    const route = normalize(meta.route || node.route || (actionId ? `/a/${actionId}?menu_id=${menuId}` : ''));
    if (menuXmlid || actionId || model) {
      out.push({ label, path: pathLabels.join(' / '), actionId, model, menuXmlid, menuId, route });
    }
    flattenNav(node.children, pathLabels, out);
  }
  return out;
}

async function loginBrowser(page) {
  await page.goto(`${BASE.replace(/\/$/, '')}/login?db=${encodeURIComponent(DB)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const dbInput = page.locator('input[autocomplete="off"]');
  if (await dbInput.isEditable().catch(() => false)) await dbInput.fill(DB);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 45000 });
  await page.waitForSelector('[data-component="SidebarNav"] .menu', { timeout: 45000 });
}

async function expandAll(page) {
  for (let round = 0; round < 50; round += 1) {
    const clicked = await page.evaluate(() => {
      function visible(element) {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
      }
      const buttons = Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.toggle'))
        .filter((button) => visible(button) && String(button.textContent || '').includes('▸'));
      buttons.forEach((button) => button.click());
      return buttons.length;
    });
    if (!clicked) break;
    await page.waitForTimeout(80);
  }
}

async function apiTotal(token, nav) {
  const contract = await intent(token, 'ui.contract', { op: 'action_open', action_id: nav.actionId });
  const head = contract.head && typeof contract.head === 'object' ? contract.head : {};
  const data = await intent(token, 'api.data', {
    op: 'list',
    model: normalize(head.model || nav.model),
    domain: Array.isArray(head.domain) ? head.domain : [],
    domain_raw: normalize(head.domain_raw),
    context_raw: normalize(head.context_raw),
    fields: ['id', 'display_name'],
    limit: 1,
    need_total: true,
  });
  return Number(data.total || 0);
}

function screenshotName(index, label) {
  return `${String(index + 1).padStart(2, '0')}-${label.replace(/[\\/:*?"<>|（）()]/g, '_')}.png`;
}

(async function main() {
  ensureDir(OUT_DIR);
  const loginData = await intent('', 'login', { db: DB, login: LOGIN, password: PASSWORD }, true);
  const token = loginData.token || (loginData.session || {}).token;
  if (!token) throw new Error('login missing token');
  const init = await intent(token, 'system.init', {});
  const nav = flattenNav(init.nav || []);
  const byXmlid = new Map(nav.map((row) => [row.menuXmlid, row]));

  const browser = await chromium.launch({ headless: HEADLESS });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, locale: 'zh-CN' });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(normalize(message.text()));
  });
  page.on('pageerror', (error) => pageErrors.push(normalize(error.message)));

  const rows = [];
  try {
    await loginBrowser(page);
    await expandAll(page);
    const sidebarText = normalize(await page.locator('[data-component="SidebarNav"]').innerText().catch(() => ''));
    await page.screenshot({ path: path.join(OUT_DIR, '00-formal-menu-expanded.png'), fullPage: true });

    for (const [index, spec] of SPECS.entries()) {
      const [label, xmlid, expectedModel, expectedTotal] = spec;
      const item = byXmlid.get(xmlid);
      const row = {
        label,
        xmlid,
        expectedModel,
        expectedTotal,
        visibleInNav: Boolean(item),
        path: item ? item.path : '',
        route: item ? item.route : '',
        navModel: item ? item.model : '',
        apiTotal: null,
        pageOk: false,
        paginationText: '',
        error: '',
      };
      try {
        if (!item) throw new Error('formal menu missing from system.init nav');
        if (item.model !== expectedModel) throw new Error(`nav model mismatch: ${item.model}`);
        row.apiTotal = await apiTotal(token, item);
        if (row.apiTotal !== expectedTotal) throw new Error(`api total mismatch: ${row.apiTotal} != ${expectedTotal}`);
        await page.goto(`${BASE.replace(/\/$/, '')}${item.route}&t=${Date.now()}`, { waitUntil: 'networkidle', timeout: 60000 });
        await page.waitForSelector('.page', { timeout: 30000 });
        await page.waitForTimeout(500);
        const body = normalize(await page.locator('body').innerText().catch(() => ''));
        const errorVisible = await page.locator('text=页面渲染失败').count().catch(() => 0);
        row.paginationText = normalize(await page.locator('.pagination-total').first().innerText({ timeout: 5000 }).catch(() => ''));
        row.pageOk = !errorVisible && (body.includes(item.label) || body.includes(label));
        await page.screenshot({ path: path.join(OUT_DIR, screenshotName(index, label)), fullPage: true });
        if (!row.pageOk) throw new Error('page did not render expected title/label');
      } catch (error) {
        row.error = error && error.message ? error.message : String(error);
      }
      rows.push(row);
    }

    const failures = rows.filter((row) => row.error || !row.pageOk || row.apiTotal !== row.expectedTotal);
    const report = {
      ok: failures.length === 0 && sidebarText.includes('正式业务菜单'),
      base_url: BASE,
      db_name: DB,
      login: LOGIN,
      out_dir: OUT_DIR,
      formal_group_visible: sidebarText.includes('正式业务菜单'),
      summary: {
        expected_count: SPECS.length,
        nav_visible_count: rows.filter((row) => row.visibleInNav).length,
        page_ok_count: rows.filter((row) => row.pageOk).length,
        failure_count: failures.length,
      },
      rows,
      console_errors: consoleErrors,
      page_errors: pageErrors,
    };
    fs.writeFileSync(path.join(OUT_DIR, 'report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
    fs.writeFileSync(path.join(OUT_DIR, 'report.md'), [
      '# Direct Acceptance Formal Menu Browser Probe',
      '',
      `- ok: ${report.ok}`,
      `- formal_group_visible: ${report.formal_group_visible}`,
      `- nav_visible_count: ${report.summary.nav_visible_count}`,
      `- page_ok_count: ${report.summary.page_ok_count}`,
      `- failure_count: ${report.summary.failure_count}`,
      '',
      '| label | model | total | page | path | error |',
      '| --- | --- | ---: | --- | --- | --- |',
      ...rows.map((row) => `| ${row.label} | ${row.navModel} | ${row.apiTotal ?? ''} | ${row.pageOk ? 'PASS' : 'FAIL'} | ${row.path} | ${row.error || ''} |`),
    ].join('\n') + '\n', 'utf8');
    console.log(JSON.stringify(report.summary, null, 2));
    console.log(`DIRECT_ACCEPTANCE_FORMAL_BROWSER=${report.ok ? 'PASS' : 'FAIL'}`);
    console.log(`ARTIFACTS=${OUT_DIR}`);
    if (!report.ok) process.exitCode = 1;
  } finally {
    await browser.close().catch(() => {});
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
