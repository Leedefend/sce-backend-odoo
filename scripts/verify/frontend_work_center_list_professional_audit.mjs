#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { launchChromium } from './playwright_runtime.mjs';

const require = createRequire(import.meta.url);
const axeModule = require(require.resolve('@axe-core/playwright', { paths: [path.resolve('frontend/apps/web/node_modules')] }));
const AxeBuilder = axeModule.default || axeModule;

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const PHASE = process.env.FE_PRO_02_PHASE === 'final' ? 'final' : 'baseline';
const ROOT = process.env.FE_PRO_02_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-02';
const OUTPUT = path.join(ROOT, PHASE);
const REPORT = path.join(ROOT, `${PHASE}-report.json`);
const ROLES = [
  { key: 'finance', login: 'demo_role_finance' },
  { key: 'project_member', login: 'demo_role_project_a_member' },
  { key: 'pm', login: 'demo_role_pm' },
  { key: 'owner', login: 'demo_role_owner' },
];
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  ...(PHASE === 'final' ? [{ width: 768, height: 1024 }] : []),
  { width: 390, height: 844 },
];
const TECHNICAL_TERMS = ['Trace', 'request JSON', 'response JSON', 'payload', 'intent name', 'registry', 'provider', 'raw exception', 'HTTP stack', '复制请求', '重放请求'];

fs.mkdirSync(OUTPUT, { recursive: true });

function runtimeCapture(page) {
  const state = { console: [], pageerror: [], http: [], requests: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) state.console.push(message.text());
  });
  page.on('pageerror', (error) => state.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400) state.http.push({ status: response.status(), url: response.url() });
  });
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().includes('/api/')) state.requests.push(request.url());
  });
  return state;
}

async function login(page, login) {
  const started = Date.now();
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('#login-username, input[autocomplete="username"]').first().fill(login);
  await page.locator('#login-password, input[autocomplete="current-password"]').first().fill(PASSWORD);
  const db = page.locator('input').nth(2);
  if (await db.isEnabled().catch(() => false)) await db.fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  return { landing_route: new URL(page.url()).pathname, elapsed_ms: Date.now() - started };
}

async function pageFacts(page) {
  await page.waitForTimeout(300);
  const text = await page.locator('body').innerText();
  const horizontal = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  return {
    path: new URL(page.url()).pathname,
    visible_actions: await page.locator('main button:visible, main a:visible').count(),
    toolbar_buttons: await page.locator('main .sc-product-page-toolbar button:visible, main .list-toolbar button:visible').count(),
    filter_controls: await page.locator('main input[type="search"]:visible, main select:visible, main [data-filter-key]:visible').count(),
    technical_term_hits: TECHNICAL_TERMS.filter((term) => text.toLowerCase().includes(term.toLowerCase())),
    horizontal_overflow: Math.max(0, horizontal),
    axe_critical_serious: axe.violations.filter((row) => ['critical', 'serious'].includes(row.impact)).map((row) => ({ id: row.id, impact: row.impact, nodes: row.nodes.length, targets: row.nodes.slice(0, 20).map((node) => node.target) })),
  };
}

async function roleSnapshots(browser, role) {
  const context = await browser.newContext({ viewport: VIEWPORTS[0], locale: 'zh-CN' });
  const page = await context.newPage();
  const runtime = runtimeCapture(page);
  const landing = await login(page, role.login);
  const roleLabel = await page.locator('.topbar-context span').first().innerText().catch(() => '');
  await page.goto(`${BASE_URL}/my-work`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('main').waitFor({ timeout: 45000 });
  const rows = [];
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize(viewport);
    const facts = await pageFacts(page);
    const screenshot = path.join(OUTPUT, `${role.key}-${viewport.width}x${viewport.height}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    rows.push({ role: role.key, viewport: `${viewport.width}x${viewport.height}`, role_surface_label: roleLabel.trim(), ...landing, ...facts, screenshot });
  }
  await context.close();
  return rows.map((row) => ({ ...row, runtime }));
}

async function taskSnapshot(browser, task) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const runtime = runtimeCapture(page);
  await login(page, task.login);
  const started = Date.now();
  let clicks = 0;
  const quickLink = task.quickLinkLabel ? page.locator('main').getByRole('button', { name: new RegExp(task.quickLinkLabel) }).first() : null;
  if (quickLink) await quickLink.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
  if (quickLink && await quickLink.isVisible().catch(() => false)) {
    await quickLink.click();
    clicks += 1;
  } else if (task.menuPath?.length) {
    for (const [index, label] of task.menuPath.entries()) {
      const button = index === task.menuPath.length - 1
        ? page.getByRole('button', { name: label, exact: true })
        : page.getByRole('button', { name: new RegExp(label) });
      await button.first().click();
      clicks += 1;
      await page.waitForTimeout(150);
    }
  } else {
    await page.goto(`${BASE_URL}${task.path}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  }
  await page.locator('main').waitFor({ timeout: 45000 });
  await page.locator('.product-work, [data-product-page-mode="list"], .sc-state-panel').first().waitFor({ timeout: 45000 }).catch(() => {});
  await page.waitForFunction(() => {
    const text = document.querySelector('main')?.textContent || '';
    return !/正在加载(?:列表|工作事项)/.test(text);
  }, { timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(350);
  const before = await pageFacts(page);
  const firstRecord = page.locator(task.recordSelector).first();
  const hasRecord = await firstRecord.isVisible().catch(() => false);
  let returnStatePreserved = null;
  if (hasRecord) {
    const search = page.locator('main input[type="search"]:visible').first();
    if (task.search && await search.isVisible().catch(() => false)) {
      await search.fill(task.search);
      await search.press('Enter');
      await page.waitForTimeout(450);
    }
    const routeBefore = page.url();
    await firstRecord.click();
    clicks += 1;
    await page.waitForTimeout(450);
    if (page.url() !== routeBefore) {
      await page.goBack({ waitUntil: 'domcontentloaded' });
      clicks += 1;
      await page.waitForTimeout(350);
      returnStatePreserved = task.search ? (await search.inputValue().catch(() => '')) === task.search : true;
    }
  }
  const result = {
    task: task.key,
    requested_path: task.path || task.menuPath.join(' / '),
    success: hasRecord,
    clicks,
    page_transitions: clicks,
    elapsed_ms: Date.now() - started,
    return_state_preserved: returnStatePreserved,
    record_candidates: await page.locator(task.recordSelector).count(),
    state_text: (await page.locator('main').innerText()).slice(0, 500),
    ...before,
    runtime,
  };
  await context.close();
  return result;
}

async function main() {
  const browser = await launchChromium({ headless: true });
  try {
    const existing = process.env.FE_PRO_02_TASKS_ONLY === '1' && fs.existsSync(REPORT)
      ? JSON.parse(fs.readFileSync(REPORT, 'utf8'))
      : null;
    const roles = existing?.roles || [];
    if (!existing) for (const role of ROLES) roles.push(...await roleSnapshots(browser, role));
    const tasks = [];
    for (const task of [
      { key: 'T01', login: 'demo_role_finance', path: '/my-work', recordSelector: '.work-card, [data-work-item-key]' },
      { key: 'T02', login: 'demo_role_executive', path: '/my-work', recordSelector: '.work-card, [data-work-item-key]' },
      { key: 'T03', login: 'demo_role_finance', quickLinkLabel: '付款申请', menuPath: ['财务中心', '付款管理', '支付申请'], recordSelector: 'tbody tr', search: 'FE-A-PR-001' },
      { key: 'T04', login: 'demo_role_pm', menuPath: ['合同中心', '合同管理', '施工合同'], recordSelector: 'tbody tr', search: 'CONOUT2600001' },
    ]) tasks.push(await taskSnapshot(browser, task));
    const report = {
      schema_version: 'frontend_work_center_list_professional_audit.v1',
      phase: PHASE,
      git_sha: process.env.GIT_SHA || '',
      database: DB_NAME,
      base_url: BASE_URL,
      roles,
      tasks,
      source_size: {
        app_shell: fs.readFileSync('frontend/apps/web/src/layouts/AppShell.vue', 'utf8').split('\n').length - 1,
        my_work_view: fs.readFileSync('frontend/apps/web/src/views/MyWorkView.vue', 'utf8').split('\n').length - 1,
        list_page: fs.readFileSync('frontend/apps/web/src/pages/ListPage.vue', 'utf8').split('\n').length - 1,
        action_view: fs.readFileSync('frontend/apps/web/src/views/ActionView.vue', 'utf8').split('\n').length - 1,
      },
    };
    fs.writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);
    if (PHASE === 'final') {
      const baselinePath = path.join(ROOT, 'baseline-report.json');
      const baseline = fs.existsSync(baselinePath) ? JSON.parse(fs.readFileSync(baselinePath, 'utf8')) : null;
      const comparison = {
        schema_version: 'frontend_work_center_list_professional_comparison.v1',
        baseline_sha: baseline?.git_sha || '',
        final_sha: report.git_sha,
        source_size: { before: baseline?.source_size || null, after: report.source_size },
        tasks: tasks.map((task) => {
          const before = baseline?.tasks?.find((row) => row.task === task.task) || null;
          return { task: task.task, before, after: task };
        }),
        role_surfaces: roles.map((row) => ({ role: row.role, viewport: row.viewport, role_surface_label: row.role_surface_label, landing_route: row.landing_route, horizontal_overflow: row.horizontal_overflow, technical_term_hits: row.technical_term_hits, axe_critical_serious: row.axe_critical_serious })),
      };
      fs.writeFileSync(path.join(ROOT, 'comparison-report.json'), `${JSON.stringify(comparison, null, 2)}\n`);
      const expectedLabels = { finance: '财务主管', project_member: '项目成员', pm: '项目经理', owner: '企业负责人' };
      if (roles.length !== 16) throw new Error(`expected 16 role/viewport rows, got ${roles.length}`);
      if (roles.some((row) => row.role_surface_label !== expectedLabels[row.role] || row.landing_route !== '/')) throw new Error('role label or landing contract failed');
      if (roles.some((row) => row.technical_term_hits.length || row.horizontal_overflow > 1 || row.axe_critical_serious.length)) throw new Error('role surface product/a11y guard failed');
      if (roles.some((row) => row.runtime.console.length || row.runtime.pageerror.length || row.runtime.http.length)) throw new Error('role surface runtime errors detected');
      if (tasks.some((task) => !task.success || task.technical_term_hits.length || task.horizontal_overflow > 1 || task.axe_critical_serious.length)) throw new Error('T01-T04 product task guard failed');
      if (tasks.filter((task) => ['T03', 'T04'].includes(task.task)).some((task) => task.return_state_preserved !== true)) throw new Error('list return state was not preserved');
    }
    console.log(JSON.stringify({ report: REPORT, role_rows: roles.length, tasks: tasks.map(({ task, success }) => ({ task, success })) }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(`[frontend_work_center_list_professional_audit] ${error.message}`);
  process.exitCode = 2;
});
