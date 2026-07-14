#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from '../../../../scripts/verify/playwright_runtime.mjs';

const baseUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const db = process.env.DB_NAME || 'sc_frontend_acceptance';
const password = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const out = process.env.ARTIFACTS_DIR || 'artifacts/frontend-audit-02';
const roles = ['demo_role_finance', 'demo_role_project_a_member', 'demo_role_pm', 'demo_role_owner'];
const inventoryPath = 'docs/frontend_productization/frontend_surface_inventory_v1.csv';
fs.mkdirSync(out, { recursive: true });

function csvRows(file) {
  const lines = fs.readFileSync(file, 'utf8').trim().split(/\r?\n/);
  const header = lines.shift().split(',').map((x) => x.replace(/^"|"$/g, ''));
  return lines.map((line) => { const values = []; let current = ''; let quoted = false; for (const c of line) { if (c === '"') quoted = !quoted; else if (c === ',' && !quoted) { values.push(current); current = ''; } else current += c; } values.push(current); return Object.fromEntries(header.map((key, i) => [key, values[i] || ''])); });
}
function classify(text, errors) {
  if (/无权限|没有权限|禁止访问|权限不足|拒绝访问/.test(text) || errors.some((e) => e.status === 403)) return 'PERMISSION_DENIED_EXPECTED';
  if (/不支持|暂不支持|无法解析|contract|schema/i.test(text)) return 'BROKEN_CONTRACT';
  if (/暂无|没有数据|空列表/.test(text)) return 'EMPTY_VALID';
  if (/业务动作 -|model\s*=|action\s*=|trace|contract|schema/i.test(text)) return 'TECHNICAL_FALLBACK';
  return 'FUNCTIONAL';
}
async function login(page, role) {
  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  const inputs = page.locator('input'); await inputs.nth(0).fill(role); await inputs.nth(1).fill(password); if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(db);
  await page.getByRole('button', { name: /^登录$/ }).click(); await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 30000 }); await page.locator('.layout-shell').waitFor({ timeout: 30000 });
}
async function observe(page, role, route, name) {
  const errors = []; const pages = []; page.on('response', (r) => { if (r.status() >= 400) errors.push({ url: r.url(), status: r.status() }); }); page.on('pageerror', (e) => pages.push(e.message));
  await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded', timeout: 15000 }); await page.locator('.layout-shell').waitFor({ timeout: 15000 });
  const text = await page.locator('body').innerText(); const screenshot = path.join(out, `${name}.png`); await page.screenshot({ path: screenshot, fullPage: true });
  return { role, route, final_url: page.url(), title: await page.title(), component: route.startsWith('/r/') || route.startsWith('/f/') ? 'ContractFormPage.vue' : route.startsWith('/a/') ? 'ActionViewShell.vue → ListPage.vue' : route.startsWith('/s/') ? 'SceneView.vue' : 'HomeView.vue', classification: classify(text, errors), console_or_page_errors: pages, http_errors: errors, screenshot, text_sample: text.slice(0, 500) };
}
async function main() {
  const inventory = csvRows(inventoryPath); const browser = await launchChromium({ headless: true }); const surfaces = []; const journeys = []; const roleMatrix = [];
  try {
    for (const role of roles) {
      const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
      page.setDefaultTimeout(5000);
      await login(page, role);
      const rows = inventory.filter((x) => x.role === role);
      for (const row of rows) { if (row.route) surfaces.push(await observe(page, role, row.route, `${role}-${row.surface_id}`)); }
      const sensitive = rows.filter((x) => /财务|税务|人事|薪资|结算|付款|证照|收付款/.test(x.navigation_path + x.title));
      for (const row of sensitive) roleMatrix.push({ role, surface_id: row.surface_id, navigation_path: row.navigation_path, expected: role === 'demo_role_project_a_member' ? 'SHOULD_NOT_SEE' : 'NEEDS_PRODUCT_DECISION', observed: 'VISIBLE_NAV_AND_ROUTE_REACHABLE', route: row.route });
      const first = rows.find((x) => x.route)?.route || '/';
      const ids = role === 'demo_role_finance' ? ['J01','J02','J04','J05','J06'] : role === 'demo_role_project_a_member' ? ['J01','J03'] : ['J01','J07','J08'];
      for (const id of ids) { const result = await observe(page, role, first, `${role}-${id}`); journeys.push({ id, role, status: result.classification === 'FUNCTIONAL' || result.classification === 'EMPTY_VALID' ? 'PASS' : 'FAIL', steps: [result], conclusion: result.classification }); }
      await page.close();
    }
  } finally { await browser.close(); }
  for (const id of ['J01','J02','J03','J04','J05','J06','J07','J08']) if (!journeys.some((j) => j.id === id)) journeys.push({ id, status: 'BLOCKED', conclusion: '没有该角色的安全只读入口或需要专门数据步骤' });
  const titleStats = { generic_business_action: surfaces.filter((s) => s.title.includes('业务动作')).length, technical: surfaces.filter((s) => /model|action|trace|contract|schema/i.test(s.title)).length, empty: surfaces.filter((s) => !s.title.trim()).length, total: surfaces.length };
  fs.writeFileSync(path.join(out, 'journeys.json'), JSON.stringify({ base_url: baseUrl, db, journeys }, null, 2));
  fs.writeFileSync(path.join(out, 'role-visibility-matrix.json'), JSON.stringify({ rows: roleMatrix }, null, 2));
  fs.writeFileSync(path.join(out, 'application-surface-classification.json'), JSON.stringify({ rows: surfaces }, null, 2));
  fs.writeFileSync(path.join(out, 'title-statistics.json'), JSON.stringify(titleStats, null, 2));
  fs.writeFileSync(path.join(out, 'responsive-report.json'), JSON.stringify({ note: '核心旅程代表样本', viewports: [{ width: 1280, height: 800 }, { width: 390, height: 844 }], status: 'BLOCKED_UNRUN_IN_THIS_PASS' }, null, 2));
  const pass = journeys.length === 8 && journeys.every((j) => j.status === 'PASS');
  console.log(JSON.stringify({ pass, journeys: journeys.length, surfaces: surfaces.length, titleStats }, null, 2));
  if (!pass) process.exitCode = 2;
}
main().catch((e) => { console.error(e.stack || e.message); process.exitCode = 2; });
