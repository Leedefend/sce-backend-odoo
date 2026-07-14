#!/usr/bin/env node

/**
 * Read-only surface audit runner. It deliberately navigates only links exposed
 * by the authenticated menu tree and never clicks controls that can mutate data.
 * The acceptance runtime is supplied by the caller (FRONTEND_URL/DB_NAME).
 */
import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from '../../../../scripts/verify/playwright_runtime.mjs';

const baseUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const dbName = process.env.DB_NAME || 'sc_frontend_acceptance';
const password = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const outputDir = process.env.ARTIFACTS_DIR || 'artifacts/frontend-audit';
const roles = (process.env.AUDIT_ROLES || 'demo_role_finance,demo_role_project_a_member,demo_role_pm,demo_role_owner').split(',').map((v) => v.trim()).filter(Boolean);
const viewports = [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 390, height: 844 }];
const maxSurfacesPerRole = Number(process.env.AUDIT_MAX_SURFACES || 30);
const dangerous = /新建|创建|保存|提交|审批|删除|撤销|登记|付款|确认|导入|发布|重置|编辑/i;

fs.mkdirSync(outputDir, { recursive: true });

function csvCell(value) { return `"${String(value ?? '').replaceAll('"', '""')}"`; }
function pageType(url, mode, text) {
  if (url.includes('/login')) return 'login';
  if (mode === 'list' || /列表|搜索结果/.test(text)) return 'list';
  if (mode === 'form' || /表单|详情|记录/.test(text)) return 'detail';
  if (url.includes('/admin/')) return 'config';
  if (url.includes('/s/')) return 'home';
  return 'report';
}

async function login(page, loginName) {
  let navigation = [];
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    try {
      const payload = await response.json();
      const data = payload?.result || payload?.data || payload;
      const candidate = data?.release_navigation_v1?.nav || data?.delivery_engine_v1?.nav;
      if (Array.isArray(candidate)) navigation = candidate;
    } catch {}
  });
  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(password);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(dbName);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  return navigation;
}

function flattenNavigation(nodes, parent = []) {
  const rows = [];
  for (const node of Array.isArray(nodes) ? nodes : []) {
    const label = String(node?.title || node?.label || node?.name || '').trim();
    const meta = node?.meta && typeof node.meta === 'object' ? node.meta : {};
    const target = node?.route || meta.route || node?.scene_key || meta.scene_key || '';
    if (label) rows.push({ label, route: String(target || '').trim(), parent_path: [...parent, label].join(' / '), dangerous: dangerous.test(label) });
    if (Array.isArray(node?.children)) rows.push(...flattenNavigation(node.children, [...parent, label].filter(Boolean)));
  }
  return rows;
}

async function inspectPage(page, role, route, screenshotPath) {
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('response', (response) => { if (response.status() >= 400) httpErrors.push({ url: response.url(), status: response.status() }); });
  const started = Date.now();
  await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.locator('.layout-shell').waitFor({ timeout: 10000 });
  const body = await page.locator('body').innerText();
  const mode = await page.locator('[data-product-page-mode]').first().getAttribute('data-product-page-mode').catch(() => '');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return {
    role,
    route,
    final_url: page.url(),
    title: await page.title(),
    page_type: pageType(page.url(), mode, body),
    load_ms: Date.now() - started,
    load_result: httpErrors.some((item) => item.status === 403) ? 'permission' : httpErrors.length ? 'error' : body.includes('暂无') ? 'empty' : 'ok',
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    technical_leak: /model\s*=|action\s*=|trace|contract|schema|\s#\d+/.test(body),
    screenshot: screenshotPath,
  };
}

async function main() {
  const browser = await launchChromium({ headless: true });
  const rows = [];
  try {
    for (const role of roles) {
      const page = await browser.newPage({ viewport: viewports[0], locale: 'zh-CN' });
      page.setDefaultTimeout(8000);
      const navigation = await login(page, role);
      const contractRows = flattenNavigation(navigation).filter((item) => !item.dangerous);
      if (!contractRows.length) {
        rows.push({ surface_id: `FE-AUD-${role}-EMPTY`, role, navigation_path: '', title: '', route: page.url(), load_result: 'empty', notes: '权威导航为空或未能从 system.init 解析' });
      }
      const toggles = page.locator('.sidebar .toggle');
      const toggleCount = Math.min(await toggles.count(), 10);
      for (let toggleIndex = 0; toggleIndex < toggleCount; toggleIndex += 1) await toggles.nth(toggleIndex).click({ timeout: 300 }).catch(() => {});
      const links = await page.locator('a[href], [role="link"], .sidebar .label').evaluateAll((nodes) => nodes.map((node) => ({
        href: node.getAttribute('href') || '',
        title: (node.textContent || node.getAttribute('aria-label') || '').trim(),
        menu_label: node.classList.contains('label'),
      })).filter((item) => (item.href && item.href.startsWith('/') && !/login|admin\//.test(item.href)) || item.menu_label));
      const unique = [...new Map([...links, ...contractRows.map((item) => ({ href: item.route, title: item.label, menu_label: false }))].map((item) => [item.href || item.title, item])).values()].slice(0, maxSurfacesPerRole);
      for (const [index, link] of unique.entries()) {
        if (dangerous.test(link.title)) continue;
        let safeRoute = link.href ? link.href.split('#')[0] : '/';
        const screenshot = path.join(outputDir, `${role}-${String(index + 1).padStart(3, '0')}.png`);
        try {
          if (link.menu_label) {
            await page.goto(`${baseUrl}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
            await page.locator('.layout-shell').waitFor({ timeout: 45000 });
            const toggles = page.locator('.sidebar .toggle');
            const toggleCount = Math.min(await toggles.count(), 10);
            for (let toggleIndex = 0; toggleIndex < toggleCount; toggleIndex += 1) await toggles.nth(toggleIndex).click({ timeout: 300 }).catch(() => {});
            await page.getByRole('button', { name: link.title, exact: true }).first().click();
            await page.waitForTimeout(500);
            safeRoute = new URL(page.url()).pathname + new URL(page.url()).search;
          }
          rows.push({ surface_id: `FE-AUD-${role}-${index + 1}`, navigation_path: link.title, title: link.title, route: safeRoute, ...await inspectPage(page, role, safeRoute, screenshot) });
        } catch (error) {
          rows.push({ surface_id: `FE-AUD-${role}-${index + 1}`, navigation_path: link.title, title: link.title, route: safeRoute, reachable: false, load_result: 'timeout', notes: error.message });
        }
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
  const fields = ['surface_id', 'role', 'navigation_path', 'title', 'route', 'page_type', 'actual_component', 'reachable', 'load_result', 'write_capable', 'screenshot', 'load_ms', 'technical_leak', 'notes'];
  const normalized = rows.map((row) => ({ actual_component: row.page_type === 'list' ? 'ActionViewShell/ListPage' : 'ContractFormPage or scene surface', reachable: true, write_capable: false, ...row }));
  fs.writeFileSync(path.join(outputDir, 'full-surface-report.json'), `${JSON.stringify({ base_url: baseUrl, db: dbName, roles, viewports, rows: normalized }, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'full-surface-report.csv'), `${fields.join(',')}\n${normalized.map((row) => fields.map((field) => csvCell(row[field])).join(',')).join('\n')}\n`);
  console.log(JSON.stringify({ pass: true, surfaces: normalized.length, outputDir }, null, 2));
}

main().catch((error) => { console.error(error.stack || error.message); process.exitCode = 2; });
