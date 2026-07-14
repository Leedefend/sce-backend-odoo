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
const inventoryPath = process.env.FRONTEND_PAGE_IDENTITY_INVENTORY_PATH || '';
const roles = (process.env.AUDIT_ROLES || 'demo_role_finance,demo_role_project_a_member,demo_role_pm,demo_role_owner').split(',').map((v) => v.trim()).filter(Boolean);
const viewports = [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 390, height: 844 }];
const maxSurfacesPerRole = Number(process.env.AUDIT_MAX_SURFACES || 0);
const actionXmlids = JSON.parse(process.env.FRONTEND_PAGE_IDENTITY_ACTION_XMLIDS_JSON || '{}');
const writeAction = /新建|创建|保存|提交|审批|删除|撤销|登记|确认|导入|发布|重置|编辑/i;

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

function navigationFromPayload(payload) {
  const candidates = [payload, payload?.result, payload?.data, payload?.result?.data];
  for (const value of candidates) {
    for (const key of ['release_navigation_v1', 'delivery_engine_v1']) {
      const projection = value?.[key];
      if (Array.isArray(projection?.nav)) return projection.nav;
      if (Array.isArray(projection)) return projection;
    }
  }
  return null;
}

async function login(page, loginName) {
  let navigation = [];
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent')) return;
    try {
      const payload = await response.json();
      const candidate = navigationFromPayload(payload);
      if (candidate) navigation = candidate;
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
  if (!navigation.length) throw new Error(`NAVIGATION_MISSING:${loginName}`);
  return navigation;
}

function resolveNodeRoute(node) {
  const meta = node?.meta && typeof node.meta === 'object' ? node.meta : {};
  const route = node?.route || meta.route;
  if (route) return String(route);
  const scene = node?.scene_key || node?.sceneKey || meta.scene_key || meta.sceneKey;
  if (scene) return `/s/${encodeURIComponent(String(scene))}`;
  const actionId = Number(node?.action_id || node?.actionId || node?.action || meta.action_id || meta.actionId || 0);
  const menuId = Number(node?.menu_id || node?.menuId || meta.menu_id || meta.menuId || 0);
  if (actionId > 0) return `/a/${actionId}${menuId > 0 ? `?menu_id=${menuId}&action_id=${actionId}` : ''}`;
  if (menuId > 0) return `/m/${menuId}`;
  return '';
}

function flattenNavigation(nodes, parent = []) {
  const rows = [];
  const journeyRows = [];
  const responsiveRows = [];
  for (const node of Array.isArray(nodes) ? nodes : []) {
    const label = String(node?.title || node?.label || node?.name || '').trim();
    const meta = node?.meta && typeof node.meta === 'object' ? node.meta : {};
    const target = resolveNodeRoute(node);
    if (label) rows.push({
      label,
      route: target,
      parent_path: [...parent, label].join(' / '),
      category: node?.children?.length ? 'container' : target ? 'navigable_leaf' : 'unresolved_leaf',
      write_capable: writeAction.test(label) && Boolean(node?.action || meta.action_id),
      menu_id: Number(node?.menu_id || node?.menuId || meta.menu_id || 0) || null,
      action_id: Number(node?.action_id || node?.actionId || meta.action_id || 0) || null,
      menu_xmlid: String(node?.xml_id || node?.xmlid || meta.menu_xmlid || ''),
      action_xmlid: String(meta.action_xmlid || actionXmlids[String(Number(node?.action_id || node?.actionId || meta.action_id || 0))] || ''),
      model: String(meta.model || ''),
    });
    if (Array.isArray(node?.children)) rows.push(...flattenNavigation(node.children, [...parent, label].filter(Boolean)));
  }
  return rows;
}

async function inspectPage(page, role, route, screenshotPath) {
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  const onConsole = (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); };
  const onPageError = (error) => pageErrors.push(error.message);
  const onResponse = (response) => { if (response.status() >= 400) httpErrors.push({ url: response.url(), status: response.status() }); };
  page.on('console', onConsole);
  page.on('pageerror', onPageError);
  page.on('response', onResponse);
  const started = Date.now();
  try {
    await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    const shell = page.locator('.layout-shell');
    await shell.waitFor({ timeout: 15000 });
    await page.waitForFunction(() => {
      const root = document.querySelector('.layout-shell');
      const title = root?.getAttribute('data-page-identity-title') || '';
      return Boolean(title && !title.includes('加载中'));
    }, undefined, { timeout: 15000 }).catch(() => {});
    const body = await page.locator('body').innerText();
    const mode = await page.locator('[data-product-page-mode]').first().getAttribute('data-product-page-mode').catch(() => '');
    const mainTitle = String(await shell.getAttribute('data-page-identity-title') || '').trim();
    const identitySource = String(await shell.getAttribute('data-page-identity-source') || '').trim();
    const documentTitle = await page.title();
    const breadcrumbs = await page.locator('.breadcrumb .crumb').allTextContents();
    const technicalPattern = /(?:[a-z_][a-z0-9_]*\.)+[a-z_][a-z0-9_]*|\s#\d+|undefined|null|\b(?:action|menu|record)_?id\b/i;
    const genericTitle = mainTitle === '业务动作' || documentTitle === `业务动作 - 智能施工企业管理平台`;
    const technicalFallback = technicalPattern.test(mainTitle) || technicalPattern.test(documentTitle) || breadcrumbs.some((item) => technicalPattern.test(item));
    await page.screenshot({ path: screenshotPath, fullPage: true });
    return {
      role,
      route,
      final_url: page.url(),
      title: mainTitle,
      document_title: documentTitle,
      breadcrumbs,
      identity_source: identitySource,
      page_type: pageType(page.url(), mode, body),
      load_ms: Date.now() - started,
      load_result: httpErrors.some((item) => item.status === 403) ? 'permission' : httpErrors.length ? 'error' : body.includes('暂无') ? 'empty' : 'ok',
      console_errors: consoleErrors,
      page_errors: pageErrors,
      http_errors: httpErrors,
      technical_leak: technicalFallback,
      generic_title: genericTitle,
      identity_result: mainTitle && documentTitle === `${mainTitle} - 智能施工企业管理平台` && identitySource && !genericTitle && !technicalFallback && !consoleErrors.length && !pageErrors.length && !httpErrors.length ? 'PASS' : 'FAIL',
      screenshot: screenshotPath,
    };
  } finally {
    page.off('console', onConsole);
    page.off('pageerror', onPageError);
    page.off('response', onResponse);
  }
}

async function main() {
  const browser = await launchChromium({ headless: true });
  const rows = [];
  const journeyRows = [];
  const responsiveRows = [];
  try {
    for (const role of roles) {
      const page = await browser.newPage({ viewport: viewports[0], locale: 'zh-CN' });
      page.setDefaultTimeout(8000);
      const navigation = await login(page, role);
      const contractRows = flattenNavigation(navigation).filter((item) => item.category !== 'container');
      const selectedRows = maxSurfacesPerRole > 0 ? contractRows.slice(0, maxSurfacesPerRole) : contractRows;
      for (const [index, link] of selectedRows.entries()) {
        const safeRoute = link.route;
        const screenshot = path.join(outputDir, `${role}-${String(index + 1).padStart(3, '0')}.png`);
        try {
          if (!safeRoute) throw new Error('UNRESOLVED_NAVIGATION_TARGET');
          const inspected = await inspectPage(page, role, safeRoute, screenshot);
          rows.push({ surface_id: `FE-AUD-${role}-${index + 1}`, navigation_path: link.parent_path, navigation_label: link.label, route: safeRoute, category: link.category, write_capable: link.write_capable, menu_id: link.menu_id, action_id: link.action_id, menu_xmlid: link.menu_xmlid, action_xmlid: link.action_xmlid, model: link.model, ...inspected });
        } catch (error) {
          rows.push({ surface_id: `FE-AUD-${role}-${index + 1}`, role, navigation_path: link.parent_path, navigation_label: link.label, route: safeRoute, category: link.category, write_capable: link.write_capable, menu_id: link.menu_id, action_id: link.action_id, menu_xmlid: link.menu_xmlid, action_xmlid: link.action_xmlid, model: link.model, reachable: false, identity_result: 'FAIL', load_result: 'error', notes: error.message });
        }
      }
      journeyRows.push(...['J01','J02','J03','J04','J05','J06','J07','J08'].map((id) => ({ id, role, status: 'NOT_ASSESSED', evidence: 'surface巡检不执行写操作，需专门旅程脚本复核' })));
      responsiveRows.push({ role, viewport: 1440, attempted: true, surfaces: selectedRows.length });
      for (const viewport of viewports.slice(1)) {
        const sample = selectedRows[0];
        if (sample?.route) {
          await page.setViewportSize(viewport);
          const screenshot = path.join(outputDir, `${role}-${viewport.width}x${viewport.height}.png`);
          try {
            const inspected = await inspectPage(page, role, sample.route, screenshot);
            responsiveRows.push({ role, viewport: viewport.width, attempted: true, route: sample.route, load_result: inspected.load_result, screenshot });
          } catch (error) {
            responsiveRows.push({ role, viewport: viewport.width, attempted: true, route: sample.route, status: 'error', error: error.message, screenshot });
          }
        } else responsiveRows.push({ role, viewport: viewport.width, attempted: false, status: 'N/A', reason: '无可导航样本' });
      }
      await page.close();
    }
  } finally {
    await browser.close();
  }
  const fields = ['surface_id', 'role', 'navigation_path', 'navigation_label', 'route', 'menu_id', 'action_id', 'menu_xmlid', 'action_xmlid', 'model', 'page_type', 'actual_component', 'title', 'document_title', 'breadcrumbs', 'identity_source', 'identity_result', 'reachable', 'load_result', 'write_capable', 'screenshot', 'load_ms', 'technical_leak', 'generic_title', 'notes'];
  const normalized = rows.map((row) => ({ actual_component: row.route.startsWith('/r/') || row.route.startsWith('/f/') ? 'ContractFormPage.vue' : row.route.startsWith('/a/') ? 'ActionViewShell.vue → ListPage.vue' : row.route.startsWith('/s/') ? 'SceneView.vue' : row.route.startsWith('/m/') ? 'MenuView.vue' : row.route === '/' ? 'HomeView.vue' : 'UNRESOLVED', reachable: row.reachable !== false, ...row }));
  const leafCounts = Object.fromEntries(roles.map((role) => [role, normalized.filter((row) => row.role === role).length]));
  const failed = normalized.filter((row) => row.reachable === false || row.identity_result !== 'PASS');
  const coverage = Object.fromEntries(roles.map((role) => { const all = normalized.filter((row) => row.role === role); return [role, { denominator: all.length, reachable: all.filter((row) => row.reachable).length, rate: all.length ? all.filter((row) => row.reachable).length / all.length : 0, failures: all.filter((row) => !row.reachable).map((row) => row.notes || row.title) }]; }));
  const genericBusinessActionTitle = normalized.filter((row) => row.generic_title).length;
  const technicalModelTitle = normalized.filter((row) => /(?:[a-z_][a-z0-9_]*\.)+[a-z_][a-z0-9_]*/i.test(`${row.title || ''} ${row.document_title || ''}`)).length;
  const rawIdTitle = normalized.filter((row) => /\s#\d+|^\d+$/i.test(String(row.title || ''))).length;
  const undefinedTitle = normalized.filter((row) => /undefined|null/i.test(`${row.title || ''} ${row.document_title || ''}`)).length;
  const missingMenuXmlid = normalized.filter((row) => !row.menu_xmlid).length;
  const missingActionXmlid = normalized.filter((row) => !row.action_xmlid).length;
  const forbidden = normalized.filter((row) => row.load_result === 'permission' || (row.http_errors || []).some((item) => item.status === 403)).length;
  const unresolved = normalized.filter((row) => row.reachable === false || !row.route).length;
  const summary = {
    authoritative_leaf_count: normalized.length,
    scanned: normalized.length,
    reachable: normalized.filter((row) => row.reachable).length,
    identity_pass: normalized.filter((row) => row.identity_result === 'PASS').length,
    generic_business_action_title: genericBusinessActionTitle,
    technical_model_title: technicalModelTitle,
    raw_id_title: rawIdTitle,
    undefined_title: undefinedTitle,
    missing_menu_xmlid: missingMenuXmlid,
    missing_action_xmlid: missingActionXmlid,
    forbidden,
    unresolved,
  };
  fs.writeFileSync(path.join(outputDir, 'full-surface-report.json'), `${JSON.stringify({ base_url: baseUrl, db: dbName, roles, viewports, leaf_counts: leafCounts, summary, coverage, rows: normalized }, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'journeys.json'), `${JSON.stringify({ journeys: journeyRows }, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'responsive-report.json'), `${JSON.stringify({ viewports, rows: responsiveRows }, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'accessibility-report.json'), `${JSON.stringify({ status: 'N/A', reason: '本轮脚本未引入新依赖，需按代表页面补充人工/工具证据' }, null, 2)}\n`);
  fs.writeFileSync(path.join(outputDir, 'performance-report.json'), `${JSON.stringify({ status: 'observed', samples: normalized.map(({ role, route, load_ms }) => ({ role, route, load_ms })) }, null, 2)}\n`);
  const inventoryCsv = `${fields.join(',')}\n${normalized.map((row) => fields.map((field) => csvCell(row[field])).join(',')).join('\n')}\n`;
  fs.writeFileSync(path.join(outputDir, 'full-surface-report.csv'), inventoryCsv);
  if (inventoryPath) {
    fs.mkdirSync(path.dirname(inventoryPath), { recursive: true });
    fs.writeFileSync(inventoryPath, inventoryCsv);
  }
  const expectedLeafCounts = { demo_role_finance: 42, demo_role_project_a_member: 9, demo_role_pm: 14, demo_role_owner: 5 };
  const pass = roles.every((role) => leafCounts[role] === expectedLeafCounts[role])
    && normalized.length === 70
    && summary.reachable === 70
    && summary.identity_pass === 70
    && summary.generic_business_action_title === 0
    && summary.technical_model_title === 0
    && summary.raw_id_title === 0
    && summary.undefined_title === 0
    && summary.missing_menu_xmlid === 0
    && summary.missing_action_xmlid === 0
    && summary.forbidden === 0
    && summary.unresolved === 0
    && failed.length === 0
    && journeyRows.length === roles.length * 8;
  console.log(JSON.stringify({ pass, surfaces: normalized.length, failed: failed.length, outputDir }, null, 2));
  if (!pass) process.exitCode = 2;
}

main().catch((error) => { console.error(error.stack || error.message); process.exitCode = 2; });
