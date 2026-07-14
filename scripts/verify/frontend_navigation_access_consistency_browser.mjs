#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { launchChromium } from './playwright_runtime.mjs';

const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5175';
const DB_NAME = process.env.DB_NAME || 'sc_frontend_acceptance';
const PASSWORD = process.env.ROLE_SMOKE_PASSWORD || 'demo';
const OUTPUT_DIR = process.env.ARTIFACTS_DIR || 'artifacts/playwright/frontend-navigation-access';
const INITIAL_LEAF_COUNT = 74;
const ROLE_CASES = [
  { login: 'demo_role_finance', role: 'finance' },
  { login: 'demo_role_project_a_member', role: 'project_member' },
  { login: 'demo_role_pm', role: 'pm' },
  { login: 'demo_role_owner', role: 'owner' },
];
const id = (name) => Number(process.env[`FRONTEND_NAV_ACCESS_${name}_ID`] || 0);
const REMOVED_TARGETS = [
  { role: 'finance', label: '计划管理', actionId: id('PLAN_ACTION'), menuId: id('PLAN_MENU') },
  { role: 'finance', label: '计划汇报', actionId: id('PLAN_REPORT_ACTION'), menuId: id('PLAN_REPORT_MENU') },
  { role: 'project_member', label: '投标报名管理', actionId: id('TENDER_ACTION'), menuId: id('TENDER_MENU') },
  { role: 'owner', label: '投标报名管理', actionId: id('TENDER_ACTION'), menuId: id('TENDER_MENU') },
];
const FAILURE_TEXT = /无权访问|权限不足|访问被拒绝|初始化失败|加载失败|暂无导航数据|Retry|重试初始化/i;

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

function requireCheck(condition, message) {
  if (!condition) throw new Error(message);
}

function payloadData(payload) {
  return payload?.result?.data || payload?.result || payload?.data || payload;
}

function navigationFromPayload(payload) {
  const data = payloadData(payload);
  const release = data?.release_navigation_v1?.nav;
  const delivery = data?.delivery_engine_v1?.nav;
  if (Array.isArray(release)) return release;
  if (Array.isArray(delivery)) return delivery;
  return null;
}

function nodeMeta(node) {
  return node?.meta && typeof node.meta === 'object' ? node.meta : {};
}

function resolveNodeRoute(node) {
  const meta = nodeMeta(node);
  const route = node?.route || meta.route;
  if (route) return String(route);
  const scene = node?.scene_key || node?.sceneKey || meta.scene_key || meta.sceneKey;
  if (scene) return `/s/${encodeURIComponent(String(scene))}`;
  const actionId = Number(node?.action_id || node?.actionId || node?.action || meta.action_id || meta.actionId || 0);
  const menuId = Number(node?.menu_id || node?.menuId || meta.menu_id || meta.menuId || 0);
  if (actionId > 0) return `/a/${actionId}${menuId > 0 ? `?menu_id=${menuId}` : ''}`;
  if (menuId > 0) return `/m/${menuId}`;
  return '';
}

function flattenLeaves(nodes, ancestors = []) {
  const rows = [];
  for (const node of Array.isArray(nodes) ? nodes : []) {
    const meta = nodeMeta(node);
    const label = String(node?.title || node?.label || node?.name || '').trim();
    const pathLabels = [...ancestors, label].filter(Boolean);
    const children = Array.isArray(node?.children) ? node.children : [];
    if (children.length) {
      rows.push(...flattenLeaves(children, pathLabels));
      continue;
    }
    rows.push({
      label,
      navigation_path: pathLabels.join(' / '),
      route: resolveNodeRoute(node),
      menu_id: Number(node?.menu_id || node?.menuId || meta.menu_id || meta.menuId || 0),
      action_id: Number(node?.action_id || node?.actionId || node?.action || meta.action_id || meta.actionId || 0),
      menu_xmlid: String(node?.xmlid || node?.menu_xmlid || meta.menu_xmlid || ''),
      action_xmlid: String(node?.action_xmlid || meta.action_xmlid || ''),
      model: String(node?.model || meta.model || meta.res_model || ''),
    });
  }
  return rows;
}

function actionableConsoleErrors(lines) {
  return lines.filter((line) => !/favicon|ResizeObserver/i.test(line));
}

function isStructuredErrorPayload(body) {
  try {
    const payload = JSON.parse(body);
    if (payload?.ok === false || payload?.success === false) return true;
    if (payload?.error) return true;
    if (payload?.result?.ok === false || payload?.result?.success === false) return true;
    if (payload?.result?.error) return true;
    return false;
  } catch {
    return false;
  }
}

async function login(page, loginName, capture) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.locator('.layout-shell').waitFor({ timeout: 45000 });
  await page.waitForFunction(() => !(document.body.innerText || '').includes('正在初始化'), null, { timeout: 45000 });
  requireCheck(Array.isArray(capture.navigation), `missing authoritative navigation for ${loginName}`);
}

async function inspectLeaf(page, role, leaf, capture, index) {
  requireCheck(leaf.route, `${role}/${leaf.navigation_path}: unresolved navigation target`);
  capture.reset();
  const started = Date.now();
  let thrown = null;
  try {
    await page.goto(`${BASE_URL}${leaf.route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.locator('.layout-shell').waitFor({ timeout: 45000 });
    await page.waitForFunction(() => {
      const text = document.body.innerText || '';
      return !/正在加载页面|正在加载场景|正在加载列表|正在初始化/.test(text);
    }, null, { timeout: 45000 });
    await page.waitForTimeout(150);
  } catch (error) {
    thrown = error;
  }
  const body = await page.locator('body').innerText().catch(() => '');
  const expectedPath = new URL(`${BASE_URL}${leaf.route}`).pathname;
  const actualPath = new URL(page.url()).pathname;
  const httpErrors = capture.responses.filter((row) => row.status >= 400);
  const payloadErrors = capture.responses.filter((row) => row.status === 200 && isStructuredErrorPayload(row.body));
  const consoleErrors = actionableConsoleErrors(capture.consoleErrors);
  const failures = [];
  if (thrown) failures.push(thrown.message);
  if (actualPath !== expectedPath) failures.push(`route mismatch: ${actualPath}`);
  if (httpErrors.length) failures.push(`HTTP ${httpErrors.map((row) => row.status).join(',')}`);
  if (payloadErrors.length) failures.push('HTTP 200 permission/error payload');
  if (capture.pageErrors.length) failures.push(`pageerror: ${capture.pageErrors.join(' | ')}`);
  if (consoleErrors.length) failures.push(`console: ${consoleErrors.join(' | ')}`);
  if (FAILURE_TEXT.test(body)) failures.push('permission/initialization error surface');
  if (!body.trim()) failures.push('empty page body');
  const result = {
    role,
    ...leaf,
    final_url: page.url(),
    http_statuses: capture.responses.map((row) => row.status),
    intent_count: capture.responses.length,
    console_errors: consoleErrors,
    page_errors: capture.pageErrors,
    result: failures.length ? 'FAIL' : 'PASS',
    failure: failures.join('; '),
    load_ms: Date.now() - started,
  };
  if (failures.length) {
    const screenshot = path.join(OUTPUT_DIR, `${role}-${String(index + 1).padStart(3, '0')}-failure.png`);
    await page.screenshot({ path: screenshot, fullPage: true }).catch(() => {});
    result.screenshot = screenshot;
  }
  return result;
}

async function verifyRemovedRouteDenied(page, target, capture) {
  const probes = [];
  for (const route of [`/a/${target.actionId}?menu_id=${target.menuId}`, `/m/${target.menuId}`]) {
    capture.reset();
    await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('heading', { name: '无权访问', exact: true }).waitFor({ timeout: 30000 });
    const body = await page.locator('body').innerText();
    requireCheck(body.includes('返回已授权的工作区'), `${target.role}/${target.label}: denial lacks safe return`);
    requireCheck(!/records\s*=\s*0|可读降级渲染/.test(body), `${target.role}/${target.label}: denial became empty/read-only page`);
    requireCheck(
      !capture.responses.some((row) => row.intent !== 'system.init' && /"records"\s*:\s*\[|FE-[ABC]-(?:PR|PLAN|TENDER)|"amount"\s*:\s*[1-9]/.test(row.body)),
      `${target.role}/${target.label}: denial response leaked record payload`,
    );
    probes.push({
      route,
      responses: capture.responses.map((row) => ({ intent: row.intent, status: row.status })),
      result: 'PERMISSION_DENIED',
    });
  }
  return { ...target, result: 'PASS', probes };
}

function attachCapture(page) {
  const capture = {
    navigation: null,
    responses: [],
    consoleErrors: [],
    pageErrors: [],
    reset() {
      this.responses = [];
      this.consoleErrors = [];
      this.pageErrors = [];
    },
  };
  page.on('console', (message) => { if (message.type() === 'error') capture.consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => capture.pageErrors.push(error.message));
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    let intent = '';
    try { intent = JSON.parse(response.request().postData() || '{}')?.intent || ''; } catch {}
    let responseBody = '';
    try { responseBody = await response.text(); } catch {}
    capture.responses.push({ status: response.status(), url: response.url(), intent, body: responseBody });
    try {
      const nav = navigationFromPayload(JSON.parse(responseBody));
      if (nav) capture.navigation = nav;
    } catch {}
  });
  return capture;
}

async function main() {
  requireCheck(REMOVED_TARGETS.every((row) => row.actionId > 0 && row.menuId > 0), 'FE-B02R runtime IDs are incomplete');
  const browser = await launchChromium({ headless: true });
  const rows = [];
  const directDenials = [];
  const leafCounts = {};
  try {
    for (const roleCase of ROLE_CASES) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' });
      const page = await context.newPage();
      const capture = attachCapture(page);
      await login(page, roleCase.login, capture);
      const leaves = flattenLeaves(capture.navigation);
      leafCounts[roleCase.role] = leaves.length;
      for (const [index, leaf] of leaves.entries()) rows.push(await inspectLeaf(page, roleCase.role, leaf, capture, index));
      for (const target of REMOVED_TARGETS.filter((row) => row.role === roleCase.role)) {
        directDenials.push(await verifyRemovedRouteDenied(page, target, capture));
      }
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const removedCount = REMOVED_TARGETS.length;
  const finalCount = Object.values(leafCounts).reduce((sum, count) => sum + count, 0);
  const forbidden = rows.filter((row) => row.http_statuses.includes(403) || /permission|无权/.test(row.failure)).length;
  const unresolved = rows.filter((row) => row.result !== 'PASS' && !row.http_statuses.includes(403)).length;
  const reachable = rows.filter((row) => row.result === 'PASS').length;
  const report = {
    contract: 'authoritative_navigation_leaf_reachability_v1',
    initial_authoritative_leaf_count: INITIAL_LEAF_COUNT,
    removed_as_unauthorized: removedCount,
    retained_after_authorized_fix: 0,
    final_authoritative_leaf_count: finalCount,
    reachable,
    forbidden,
    unresolved,
    role_leaf_counts: leafCounts,
    direct_removed_route_denials: directDenials,
    rows,
  };
  fs.writeFileSync(path.join(OUTPUT_DIR, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  requireCheck(finalCount === INITIAL_LEAF_COUNT - removedCount, `unexpected authoritative denominator: initial=${INITIAL_LEAF_COUNT} removed=${removedCount} final=${finalCount}`);
  requireCheck(reachable === finalCount && forbidden === 0 && unresolved === 0, `navigation reachability failed: reachable=${reachable} forbidden=${forbidden} unresolved=${unresolved}`);
  requireCheck(directDenials.length === removedCount, 'removed-route denial coverage is incomplete');
  console.log(`[verify.frontend.navigation.access] PASS final=${finalCount} reachable=${reachable}`);
  console.log(JSON.stringify({ leaf_counts: leafCounts, removed: removedCount, final: finalCount }, null, 2));
}

main().catch((error) => {
  console.error(`[verify.frontend.navigation.access] FAIL ${error.stack || error.message}`);
  process.exitCode = 2;
});
