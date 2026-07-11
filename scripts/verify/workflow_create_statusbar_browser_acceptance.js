#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

const repoRoot = path.resolve(__dirname, '..', '..');
const requireFromWeb = createRequire(path.join(repoRoot, 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || process.env.LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || process.env.PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts/workflow-create-statusbar-browser';
const CATEGORY_CATALOG = process.env.CATEGORY_CATALOG || path.join(repoRoot, 'artifacts/playwright/business-form-all-category-direct/category_catalog.json');
const CATEGORY_CODES = (process.env.WORKFLOW_CREATE_STATUSBAR_CATEGORIES || 'finance.deduction.bill,finance.deduction.paid,finance.deduction.refund,finance.receipt.income.project,contract.income')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);
const ALL_CATEGORIES = process.env.WORKFLOW_CREATE_STATUSBAR_ALL !== '0';

function outPath(name) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  return path.join(ARTIFACTS_DIR, name);
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.locator('input').nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator('input').count() >= 3) {
    const dbInput = page.locator('input').nth(2);
    if (await dbInput.isEnabled().catch(() => false)) {
      await dbInput.fill(DB_NAME);
    }
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 60000 });
}

function loadCatalog() {
  if (!fs.existsSync(CATEGORY_CATALOG)) {
    throw new Error(`category catalog missing: ${CATEGORY_CATALOG}`);
  }
  const raw = JSON.parse(fs.readFileSync(CATEGORY_CATALOG, 'utf8'));
  const rows = Array.isArray(raw) ? raw : raw.categories || raw.rows || raw.data || [];
  if (!Array.isArray(rows) || !rows.length) {
    throw new Error(`category catalog has no rows: ${CATEGORY_CATALOG}`);
  }
  return rows
    .map((row) => ({
      code: String(row.code || '').trim(),
      name: String(row.name || row.label || row.code || '').trim(),
      model: String(row.model || '').trim(),
      actionId: Number(row.action_id || row.actionId || 0),
      menuId: Number(row.menu_id || row.menuId || 0),
    }))
    .filter((row) => row.code && row.model && row.actionId);
}

function selectScenarios(catalog) {
  if (ALL_CATEGORIES) return catalog;
  const byCode = new Map(catalog.map((row) => [row.code, row]));
  const missing = CATEGORY_CODES.filter((code) => !byCode.has(code));
  if (missing.length) {
    throw new Error(`category catalog missing required workflow create samples: ${missing.join(', ')}`);
  }
  return CATEGORY_CODES.map((code) => byCode.get(code));
}

function createUrl(scenario) {
  const params = new URLSearchParams({
    db: DB_NAME,
    action_id: String(scenario.actionId),
    current_business_category_code: scenario.code,
    default_business_category_code: scenario.code,
    current_business_category_label: scenario.name,
    default_business_category_label: scenario.name,
    ctx_source: 'workflow_create_statusbar_browser_acceptance',
  });
  if (scenario.menuId) {
    params.set('menu_id', String(scenario.menuId));
  }
  return `${FRONTEND_URL}/f/${encodeURIComponent(scenario.model)}/new?${params.toString()}`;
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 45000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 45000 });
  const text = normalize(await page.locator('.template-layout-shell').textContent({ timeout: 5000 }));
  if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) {
    throw new Error(`form render failed: ${text.slice(0, 500)}`);
  }
  return text;
}

async function visibleStatusbars(page) {
  return page.locator('.native-statusbar--header').evaluateAll((nodes) => nodes
    .map((node) => {
      const style = window.getComputedStyle(node);
      const visible = style.display !== 'none'
        && style.visibility !== 'hidden'
        && style.opacity !== '0'
        && Boolean(node.offsetWidth || node.offsetHeight || node.getClientRects().length);
      return {
        visible,
        text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
      };
    })
    .filter((item) => item.visible));
}

async function visibleWorkflowStateFields(page) {
  return page.locator('.template-form-section .field').evaluateAll((nodes) => {
    const stateFieldNames = new Set([
      'state',
      'status',
      'lifecycle_state',
      'workflow_state',
      'approval_state',
      'tier_validation_state',
      'validation_state',
    ]);
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return nodes
      .map((node) => {
        const style = window.getComputedStyle(node);
        const visible = style.display !== 'none'
          && style.visibility !== 'hidden'
          && style.opacity !== '0'
          && Boolean(node.offsetWidth || node.offsetHeight || node.getClientRects().length);
        const classNames = Array.from(node.classList || []);
        const fieldClass = classNames.find((item) => item.startsWith('field--'));
        const fieldName = fieldClass ? fieldClass.replace(/^field--/, '') : '';
        const label = normalize(node.querySelector('.label')?.textContent || '');
        return {
          visible,
          fieldName,
          label,
          text: normalize(node.textContent || ''),
        };
      })
      .filter((item) => item.visible)
      .filter((item) => stateFieldNames.has(item.fieldName) || item.label === '状态' || item.label.endsWith('状态'));
  });
}

async function nativeCreateHeaderLayout(page) {
  return page.evaluate(() => {
    const rectOf = (node) => {
      if (!node) return null;
      const rect = node.getBoundingClientRect();
      return {
        left: Math.round(rect.left * 100) / 100,
        right: Math.round(rect.right * 100) / 100,
        width: Math.round(rect.width * 100) / 100,
        top: Math.round(rect.top * 100) / 100,
        bottom: Math.round(rect.bottom * 100) / 100,
      };
    };
    const header = document.querySelector('.contract-form-native-shell .template-page-header');
    const actions = document.querySelector('.contract-form-native-shell .template-page-header-actions');
    const status = document.querySelector('.contract-form-native-shell .template-page-header-status');
    const firstAction = actions ? actions.querySelector('button, a, [role="button"]') : null;
    const statusStyle = status ? window.getComputedStyle(status) : null;
    const hasVisibleStatus = Boolean(status)
      && statusStyle.display !== 'none'
      && statusStyle.visibility !== 'hidden'
      && Boolean(status.offsetWidth || status.offsetHeight || status.getClientRects().length)
      && String(status.textContent || '').trim().length > 0;
    const headerStyle = header ? window.getComputedStyle(header) : null;
    const actionsStyle = actions ? window.getComputedStyle(actions) : null;
    return {
      viewportWidth: window.innerWidth,
      hasHeader: Boolean(header),
      hasActions: Boolean(actions),
      hasVisibleStatus,
      headerClass: header ? String(header.getAttribute('class') || '') : '',
      headerJustify: headerStyle ? headerStyle.justifyContent : '',
      actionsJustify: actionsStyle ? actionsStyle.justifyContent : '',
      header: rectOf(header),
      actions: rectOf(actions),
      firstAction: rectOf(firstAction),
      firstActionText: firstAction ? String(firstAction.textContent || '').replace(/\s+/g, ' ').trim() : '',
    };
  });
}

function headerLayoutFailures(layout) {
  if (!layout || !layout.hasHeader || !layout.hasActions) return [];
  if (layout.viewportWidth <= 860 || layout.hasVisibleStatus) return [];
  if (!String(layout.headerClass || '').includes('template-page-header--title-hidden')) return [];
  const failures = [];
  const rightGap = layout.header && layout.actions ? layout.header.right - layout.actions.right : 0;
  if (rightGap > 6) {
    failures.push(`header actions not right aligned: rightGap=${rightGap}`);
  }
  if (layout.headerJustify !== 'flex-end') {
    failures.push(`header justify mismatch: ${layout.headerJustify || '-'}`);
  }
  if (layout.actionsJustify !== 'flex-end') {
    failures.push(`actions justify mismatch: ${layout.actionsJustify || '-'}`);
  }
  return failures;
}

async function launchBrowser() {
  try {
    const runtime = await import(pathToFileUrl(path.join(repoRoot, 'scripts/verify/playwright_runtime.mjs')));
    if (runtime && typeof runtime.launchChromium === 'function') {
      return await runtime.launchChromium({ headless: true });
    }
  } catch (_err) {
    // Fall back to Playwright's default launcher below.
  }
  return chromium.launch({ headless: true });
}

function pathToFileUrl(filePath) {
  const resolved = path.resolve(filePath).replace(/\\/g, '/');
  return `file://${resolved.startsWith('/') ? '' : '/'}${resolved}`;
}

async function main() {
  const scenarios = selectScenarios(loadCatalog());
  const browser = await launchBrowser();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));

  const results = [];
  try {
    await login(page);
    for (const scenario of scenarios) {
      const url = createUrl(scenario);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      const text = await waitForFormReady(page);
      await page.waitForTimeout(500);
      const visible = await visibleStatusbars(page);
      const visibleStateFields = await visibleWorkflowStateFields(page);
      const headerLayout = await nativeCreateHeaderLayout(page);
      const layoutFailures = headerLayoutFailures(headerLayout);
      const screenshot = outPath(`${scenario.code.replace(/[^a-z0-9_.-]+/gi, '_')}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      const result = {
        ok: visible.length === 0 && visibleStateFields.length === 0 && layoutFailures.length === 0,
        code: scenario.code,
        name: scenario.name,
        model: scenario.model,
        actionId: scenario.actionId,
        menuId: scenario.menuId,
        url: page.url(),
        visibleStatusbars: visible,
        visibleStateFields,
        headerLayout,
        layoutFailures,
        textSample: text.slice(0, 300),
        screenshot,
      };
      results.push(result);
      if (!result.ok) {
        throw new Error(`create form rendered invalid create surface: ${scenario.code} ${JSON.stringify({
          visibleStatusbars: visible,
          visibleStateFields,
          layoutFailures,
          headerLayout,
        })}`);
      }
    }
    const payload = {
      ok: true,
      db: DB_NAME,
      checked: results.length,
      categories: results,
      consoleErrors,
    };
    fs.writeFileSync(outPath('workflow-create-statusbar.json'), JSON.stringify(payload, null, 2), 'utf8');
    console.log(JSON.stringify(payload, null, 2));
  } catch (err) {
    const failure = {
      ok: false,
      db: DB_NAME,
      url: page.url(),
      results,
      consoleErrors,
      error: err && err.stack ? err.stack : String(err),
      screenshot: outPath('workflow-create-statusbar-failure.png'),
    };
    await page.screenshot({ path: failure.screenshot, fullPage: true }).catch(() => {});
    fs.writeFileSync(outPath('workflow-create-statusbar-failure.json'), JSON.stringify(failure, null, 2), 'utf8');
    throw err;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
