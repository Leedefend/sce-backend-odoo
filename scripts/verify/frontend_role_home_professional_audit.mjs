#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { launchChromium } from './playwright_runtime.mjs';

const require = createRequire(import.meta.url);
const axeModule = require(require.resolve('@axe-core/playwright', {
  paths: [path.resolve('frontend/apps/web/node_modules')],
}));
const AxeBuilder = axeModule.default || axeModule;

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const PHASE = process.env.FE_PRO_01_PHASE === 'final' ? 'final' : 'baseline';
const ROOT = process.env.FE_PRO_01_ARTIFACT_ROOT || 'artifacts/frontend-professional/fe-pro-01';
const OUT = path.join(ROOT, PHASE);
const REPORT = path.join(ROOT, `${PHASE}-report.json`);
const COMPARISON_REPORT = path.join(ROOT, 'comparison-report.json');
const ROLES = [
  { login: 'demo_role_finance', key: 'finance', label: '财务主管' },
  { login: 'demo_role_project_a_member', key: 'project_member', label: '项目成员' },
  { login: 'demo_role_pm', key: 'pm', label: '项目经理' },
  { login: 'demo_role_owner', key: 'owner', label: '业主' },
];
const VIEWPORTS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  { width: 390, height: 844 },
];
const TECHNICAL_TERMS = [
  'payload', 'bundle', 'fallback', 'HUD', 'trace', 'JSON', 'registry',
  'projection', 'provider', 'debug', 'capability map', '配置缺口', '契约未命中',
];
const ROLE_FORBIDDEN_TEXT = {
  project_member: ['付款', '结算', 'FE-JOURNEY-PAYMENT', '¥'],
  owner: ['投标报名'],
};

fs.mkdirSync(OUT, { recursive: true });

function check(value, message) {
  if (!value) throw new Error(message);
}

function technicalHits(text) {
  const source = String(text || '');
  return TECHNICAL_TERMS.filter((term) => new RegExp(`(^|[^a-z])${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}([^a-z]|$)`, 'i').test(source));
}

function captureRuntime(page) {
  const state = { console: [], pageerror: [], http: [] };
  page.on('console', (message) => {
    if (message.type() === 'error' && !/favicon|ResizeObserver/i.test(message.text())) state.console.push(message.text());
  });
  page.on('pageerror', (error) => state.pageerror.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400) state.http.push({ status: response.status(), url: response.url() });
  });
  return state;
}

async function login(page, user) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('#login-username, input[autocomplete="username"]').first().fill(user);
  const password = page.locator('#login-password, input[autocomplete="current-password"]').first();
  await password.fill(PASSWORD);
  const dbInput = page.locator('input').nth(2);
  if (await dbInput.isEnabled().catch(() => false)) await dbInput.fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  return new URL(page.url()).pathname;
}

async function visibleCount(locator) {
  return locator.evaluateAll((nodes) => nodes.filter((node) => {
    const rect = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  }).length);
}

async function inspectHome(page, role, viewport, landingPath, screenshot) {
  await page.setViewportSize(viewport);
  await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  await page.locator('.page-renderer--role-home, .minimum-workspace-fallback, .capability-home, [data-role-home]').first().waitFor({ timeout: 45000 });
  await page.waitForTimeout(300);

  const bodyText = await page.locator('body').innerText();
  const shellText = await page.locator('.layout-shell').innerText();
  const renderingPath = await page.evaluate(() => {
    if (document.querySelector('[data-role-home-renderer]')) return document.querySelector('[data-role-home-renderer]')?.getAttribute('data-role-home-renderer');
    if (document.querySelector('.page-renderer--role-home')) return 'page_renderer';
    if (document.querySelector('.minimum-workspace-fallback')) return 'minimum_workspace';
    if (document.querySelector('.capability-home')) return 'legacy_capability_home';
    return 'unknown';
  });
  const headings = await page.locator('main h1, main h2, main h3').allTextContents();
  const h1Count = await visibleCount(page.locator('h1'));
  const mainCount = await visibleCount(page.locator('main'));
  const firstViewportActions = await page.locator('main button:visible, main a:visible').evaluateAll((nodes) => nodes.filter((node) => {
    const rect = node.getBoundingClientRect();
    return rect.top >= 0 && rect.top < window.innerHeight && rect.left >= 0 && rect.left < window.innerWidth;
  }).length);
  const topNavigationGroups = await visibleCount(page.locator('.tree--root > li'));
  const homePanels = await visibleCount(page.locator('main section, main article, main details'));
  const firstAction = await page.locator('main button:visible, main a:visible').first().innerText().catch(() => '');
  const horizontal = await page.evaluate(() => ({
    scroll_width: document.documentElement.scrollWidth,
    client_width: document.documentElement.clientWidth,
  }));
  const roleOccurrences = role.label ? shellText.split(role.label).length - 1 : 0;
  const contextTexts = await page.locator('.topbar-context, .role-surface, [data-product-context]').allTextContents();
  const axeResult = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  const axeBlocking = axeResult.violations.filter((row) => ['critical', 'serious'].includes(row.impact));
  await page.screenshot({ path: screenshot, fullPage: true });
  return {
    role: role.key,
    login: role.login,
    viewport: `${viewport.width}x${viewport.height}`,
    landing_path: landingPath,
    home_path: new URL(page.url()).pathname,
    rendering_path: renderingPath,
    heading_count: headings.length,
    headings,
    h1_count: h1Count,
    main_landmark_count: mainCount,
    first_viewport_action_count: firstViewportActions,
    top_navigation_group_count: topNavigationGroups,
    home_panel_count: homePanels,
    technical_term_hits: technicalHits(bodyText),
    sensitive_exposure_hits: (ROLE_FORBIDDEN_TEXT[role.key] || []).filter((term) => bodyText.includes(term)),
    role_occurrences: roleOccurrences,
    context_surfaces: contextTexts,
    first_actionable_element: firstAction.trim(),
    clicks_from_login_to_first_role_task: landingPath === '/' || landingPath === '/s/workspace.home' ? 0 : 1,
    horizontal_overflow: Math.max(0, horizontal.scroll_width - horizontal.client_width),
    axe_critical_serious: axeBlocking.map((row) => ({ id: row.id, impact: row.impact, nodes: row.nodes.length })),
    screenshot,
  };
}

async function main() {
  const browser = await launchChromium({ headless: true });
  const rows = [];
  const runtimeRows = [];
  try {
    for (const role of ROLES) {
      const context = await browser.newContext({ viewport: VIEWPORTS[0], locale: 'zh-CN' });
      const page = await context.newPage();
      const runtime = captureRuntime(page);
      const landingPath = await login(page, role.login);
      for (const viewport of VIEWPORTS) {
        const fileName = `${role.key}-${viewport.width}x${viewport.height}.png`;
        rows.push(await inspectHome(page, role, viewport, landingPath, path.join(OUT, fileName)));
      }
      runtimeRows.push({ role: role.key, ...runtime });
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const totals = {
    screenshots: rows.length,
    technical_term_hits: rows.reduce((sum, row) => sum + row.technical_term_hits.length, 0),
    sensitive_exposure_hits: rows.reduce((sum, row) => sum + row.sensitive_exposure_hits.length, 0),
    horizontal_overflow_pages: rows.filter((row) => row.horizontal_overflow > 1).length,
    axe_critical_serious: rows.reduce((sum, row) => sum + row.axe_critical_serious.length, 0),
    console_errors: runtimeRows.reduce((sum, row) => sum + row.console.length, 0),
    page_errors: runtimeRows.reduce((sum, row) => sum + row.pageerror.length, 0),
    unexpected_http_errors: runtimeRows.reduce((sum, row) => sum + row.http.length, 0),
  };
  const report = {
    schema_version: 'frontend_role_home_professional_audit.v1',
    phase: PHASE,
    git_sha: process.env.GIT_SHA || '',
    database: DB_NAME,
    base_url: BASE_URL,
    roles: ROLES.map(({ key }) => key),
    viewports: VIEWPORTS,
    totals,
    rows,
    runtime: runtimeRows,
  };
  fs.writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`);
  if (PHASE === 'final') {
    const baselinePath = path.join(ROOT, 'baseline-report.json');
    const baseline = fs.existsSync(baselinePath) ? JSON.parse(fs.readFileSync(baselinePath, 'utf8')) : null;
    const lineCount = (file) => fs.readFileSync(file, 'utf8').split('\n').length;
    const comparison = {
      schema_version: 'frontend_role_home_professional_comparison.v1',
      baseline_sha: baseline?.git_sha || '',
      final_sha: report.git_sha,
      baseline: baseline?.totals || null,
      final: totals,
      change: baseline ? {
        technical_term_hits: totals.technical_term_hits - Number(baseline.totals?.technical_term_hits || 0),
        horizontal_overflow_pages: totals.horizontal_overflow_pages - Number(baseline.totals?.horizontal_overflow_pages || 0),
        axe_critical_serious: totals.axe_critical_serious - Number(baseline.totals?.axe_critical_serious || 0),
      } : null,
      source_size: {
        before: { app_shell: 2316, home_view: 3525, combined: 5841 },
        after: {
          app_shell: lineCount('frontend/apps/web/src/layouts/AppShell.vue'),
          home_view: lineCount('frontend/apps/web/src/views/HomeView.vue'),
        },
      },
      rows: rows.map((row) => ({
        role: row.role,
        viewport: row.viewport,
        top_navigation_group_count: row.top_navigation_group_count,
        home_panel_count: row.home_panel_count,
        first_viewport_action_count: row.first_viewport_action_count,
        technical_term_hits: row.technical_term_hits,
        sensitive_exposure_hits: row.sensitive_exposure_hits,
        horizontal_overflow: row.horizontal_overflow,
        axe_critical_serious: row.axe_critical_serious,
      })),
    };
    comparison.source_size.after.combined = comparison.source_size.after.app_shell + comparison.source_size.after.home_view;
    comparison.source_size.reduction_ratio = 1 - (comparison.source_size.after.combined / comparison.source_size.before.combined);
    fs.writeFileSync(COMPARISON_REPORT, `${JSON.stringify(comparison, null, 2)}\n`);
  }
  check(rows.length === 12, `expected 12 screenshots, got ${rows.length}`);
  if (PHASE === 'final') {
    check(totals.technical_term_hits === 0, `technical terms=${totals.technical_term_hits}`);
    check(totals.sensitive_exposure_hits === 0, `sensitive exposure hits=${totals.sensitive_exposure_hits}`);
    check(totals.horizontal_overflow_pages === 0, `overflow pages=${totals.horizontal_overflow_pages}`);
    check(totals.axe_critical_serious === 0, `axe blocking=${totals.axe_critical_serious}`);
    check(totals.console_errors === 0 && totals.page_errors === 0 && totals.unexpected_http_errors === 0, `runtime errors=${JSON.stringify(totals)}`);
    check(rows.every((row) => row.h1_count === 1 && row.main_landmark_count === 1), 'heading or landmark contract failed');
    check(rows.every((row) => row.rendering_path === 'contract'), 'formal role did not use the contract renderer');
    check(rows.every((row) => row.top_navigation_group_count <= 7), 'top navigation exceeds seven business domains');
  }
  console.log(JSON.stringify({ phase: PHASE, report: REPORT, totals }, null, 2));
}

main().catch((error) => {
  console.error(`[frontend_role_home_professional_audit] ${error.message}`);
  process.exitCode = 2;
});
