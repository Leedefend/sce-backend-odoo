import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);
const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');

function primeLocalRuntimeLibraries() {
  const candidateDirs = [
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib'),
  ].filter((dir) => fs.existsSync(dir));
  if (!candidateDirs.length) return;
  const existing = String(process.env.LD_LIBRARY_PATH || '').trim();
  const segments = existing ? existing.split(':').filter(Boolean) : [];
  process.env.LD_LIBRARY_PATH = [...candidateDirs, ...segments].join(':');
}

primeLocalRuntimeLibraries();

const BASE_URL = String(process.env.BASE_URL || 'http://127.0.0.1').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_demo').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'admin').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'admin').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'enterprise-enablement-frontend-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  status: 'PASS',
  system_init_calls: [],
  console_errors: [],
  page_errors: [],
};

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function log(message) {
  console.log(`[enterprise_enablement_frontend_smoke] ${message}`);
}

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 20000, waitUntil: 'commit' });
}

async function readSessionSnapshot(page) {
  return page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    return {
      href: window.location.href,
      pathname: window.location.pathname,
      search: window.location.search,
      cache_key: cacheKey || '',
      enterprise_enablement: cache?.enterpriseEnablement || null,
      user_groups: Array.isArray(cache?.user?.groups_xmlids) ? cache.user.groups_xmlids : [],
      workspace_home_ref: cache?.workspaceHomeRef || null,
      workspace_home_loaded: !!cache?.workspaceHome,
    };
  });
}

async function waitForEnterpriseCard(page) {
  const card = page.locator('.enterprise-enablement-card');
  await card.waitFor({ state: 'visible', timeout: 20000 });
  await page.locator('.enterprise-enablement-primary').waitFor({ state: 'visible', timeout: 10000 });
  return card;
}

async function openCompanyCreateForm(page) {
  await page.locator('.router-host').waitFor({ state: 'visible', timeout: 30000 });
  await page.getByText('正在初始化工作台...').waitFor({ state: 'hidden', timeout: 30000 }).catch(() => {});
  const createButton = page.getByRole('button', { name: '新建公司' });
  await createButton.waitFor({ state: 'visible', timeout: 20000 });
  await createButton.click();
  await page.waitForFunction(() => window.location.pathname === '/f/res.company/new', undefined, { timeout: 20000 });
  await page.waitForLoadState('domcontentloaded');
}

async function readActionPageDebug(page, actionId) {
  return page.evaluate(async ({ actionId, dbName }) => {
    const isVisible = (el) => {
      if (!(el instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };
    const toRow = (el) => ({
      text: String(el.textContent || '').trim(),
      class_name: String(el.className || ''),
      disabled: !!el.disabled,
    });
    const buttonRows = Array.from(document.querySelectorAll('button')).map(toRow);
    const headingRows = Array.from(document.querySelectorAll('h1,h2,h3')).map((el) => String(el.textContent || '').trim()).filter(Boolean);
    const routerHost = document.querySelector('.router-host');
    const hostVisibleButtons = routerHost
      ? Array.from(routerHost.querySelectorAll('button')).filter(isVisible).map(toRow)
      : [];
    const hostVisibleHeadings = routerHost
      ? Array.from(routerHost.querySelectorAll('h1,h2,h3')).filter(isVisible).map((el) => String(el.textContent || '').trim()).filter(Boolean)
      : [];
    const hostPages = routerHost ? Array.from(routerHost.querySelectorAll('.page')) : [];
    const hostAdvancedViews = routerHost ? Array.from(routerHost.querySelectorAll('.advanced-view')) : [];
    const hostTables = routerHost ? Array.from(routerHost.querySelectorAll('.table')) : [];
    const hostHeaders = routerHost ? Array.from(routerHost.querySelectorAll('.header')) : [];
    const headerPrimaryButton = document.querySelector('.router-host .header .primary');
    const headerTitle = document.querySelector('.router-host .header .title');
    const sessionKeys = Object.keys(sessionStorage);
    const tokenKey = sessionKeys.find((key) => key.startsWith('sc_auth_token'));
    const token = tokenKey ? String(sessionStorage.getItem(tokenKey) || '').trim() : '';
    let contractSummary = null;
    try {
      const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Trace-Id': 'enterprise-enablement-smoke-debug',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({
          intent: 'ui.contract',
          params: { op: 'action_open', action_id: actionId },
        }),
      });
      const payload = await response.json();
      const data = payload?.data || {};
      const nested = data?.ui_contract || data;
      contractSummary = {
        status: response.status,
        root_model: data?.model || '',
        root_head_model: data?.head?.model || '',
        nested_model: nested?.model || '',
        nested_head_model: nested?.head?.model || '',
        root_view_type: data?.view_type || '',
        nested_view_type: nested?.view_type || '',
        root_head_view_type: data?.head?.view_type || '',
        nested_head_view_type: nested?.head?.view_type || '',
        create_right: nested?.permissions?.effective?.rights?.create,
        head_create: nested?.head?.permissions?.create,
        recommended_runtime: nested?.semantic_page?.capability_profile?.recommended_runtime || '',
        takeover_class: nested?.semantic_page?.capability_profile?.takeover_class || '',
      };
    } catch (error) {
      contractSummary = {
        error: String(error?.message || error),
      };
    }
    return {
      href: window.location.href,
      buttons: buttonRows,
      headings: headingRows,
      host_visible_buttons: hostVisibleButtons,
      host_visible_headings: hostVisibleHeadings,
      host_page_count: hostPages.length,
      host_visible_page_count: hostPages.filter(isVisible).length,
      host_advanced_view_count: hostAdvancedViews.length,
      host_visible_advanced_view_count: hostAdvancedViews.filter(isVisible).length,
      host_table_count: hostTables.length,
      host_visible_table_count: hostTables.filter(isVisible).length,
      host_header_count: hostHeaders.length,
      host_visible_header_count: hostHeaders.filter(isVisible).length,
      header_title: headerTitle ? String(headerTitle.textContent || '').trim() : '',
      header_primary_button: headerPrimaryButton ? toRow(headerPrimaryButton) : null,
      router_host_html_excerpt: routerHost ? String(routerHost.innerHTML || '').replace(/\s+/g, ' ').trim().slice(0, 1200) : '',
      token_present: !!token,
      token_key: tokenKey || '',
      action_debug: (window.__scActionDebug && typeof window.__scActionDebug === 'object') ? window.__scActionDebug : null,
      contract_summary: contractSummary,
    };
  }, { actionId, dbName: DB_NAME });
}

async function readCompanyFormDebug(page) {
  return page.evaluate(async ({ dbName }) => {
    const isVisible = (el) => {
      if (!(el instanceof HTMLElement)) return false;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };
    const sessionKeys = Object.keys(sessionStorage);
    const tokenKey = sessionKeys.find((key) => key.startsWith('sc_auth_token'));
    const token = tokenKey ? String(sessionStorage.getItem(tokenKey) || '').trim() : '';
    const textRows = Array.from(document.querySelectorAll('h1,h2,h3,label,.contract-label,.subtitle,p,button,span'))
      .filter(isVisible)
      .map((el) => String(el.textContent || '').trim())
      .filter(Boolean);
    const fieldLabels = textRows.filter((item) => ['公司简称', '统一社会信用代码', '联系电话', '地址', '启用', '组织架构'].some((token) => item.includes(token)));
    const forbiddenTokens = textRows.filter((item) => item.includes('partner_id') || item.includes('child_ids') || item.includes('sequence'));
    const routerHost = document.querySelector('.router-host');
    async function fetchIntent(params) {
      try {
        const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Trace-Id': 'enterprise-enable-form-debug',
            'Authorization': token ? `Bearer ${token}` : '',
          },
          body: JSON.stringify({ intent: 'ui.contract', params }),
        });
        const payload = await response.json();
        const data = payload?.data || {};
        return {
          status: response.status,
          head_title: data?.head?.title || '',
          model: data?.head?.model || data?.model || '',
          view_type: data?.head?.view_type || data?.view_type || '',
          field_count: Object.keys(data?.fields || {}).length,
        };
      } catch (error) {
        return {
          error: String(error?.message || error),
        };
      }
    }
    return {
      href: window.location.href,
      visible_texts_sample: textRows.slice(0, 80),
      field_labels: fieldLabels,
      forbidden_tokens: forbiddenTokens,
      form_debug: (window.__scFormDebug && typeof window.__scFormDebug === 'object') ? window.__scFormDebug : null,
      contract_fetch_action_open: await fetchIntent({ op: 'action_open', action_id: 567, render_profile: 'create', contract_surface: 'user', source_mode: 'governance_pipeline' }),
      contract_fetch_model: await fetchIntent({ op: 'model', model: 'res.company', view_type: 'form', render_profile: 'create', contract_surface: 'user', source_mode: 'governance_pipeline' }),
      router_host_html_excerpt: routerHost ? String(routerHost.innerHTML || '').replace(/\s+/g, ' ').trim().slice(0, 1600) : '',
    };
  }, { dbName: DB_NAME });
}

async function followPrimaryAction(page, sessionSnapshot) {
  const primaryAction = sessionSnapshot?.enterprise_enablement?.primary_action || null;
  const route = String(primaryAction?.route || '').trim();
  if (!route) throw new Error('enterprise primary action route is missing');
  log(`navigate to primary action route ${route}`);
  const primaryButton = page.locator('.enterprise-enablement-primary');
  await primaryButton.waitFor({ state: 'visible', timeout: 20000 });
  await primaryButton.click();
}

let browser;
let page;
try {
  browser = await chromium.launch({ headless: true, timeout: 20000 });
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });
  page.on('response', async (response) => {
    if (!response.url().includes('/api/v1/intent') || response.request().method() !== 'POST') return;
    try {
      const body = response.request().postDataJSON();
      if (String(body?.intent || '') !== 'system.init') return;
      const payload = await response.json();
      const data = payload?.data || {};
      const mainline = data?.ext_facts?.enterprise_enablement?.mainline || null;
      summary.system_init_calls.push({
        status: response.status(),
        pathname: page.url(),
        has_mainline: !!mainline,
        step_count: Array.isArray(mainline?.steps) ? mainline.steps.length : 0,
        primary_action_id: Number(mainline?.primary_action?.action_id || 0),
      });
    } catch {
      // ignore parse failure
    }
  });

  log(`login with ${LOGIN}`);
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await fillLoginForm(page);
  await submitLogin(page);

  log('open home page');
  await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
  const card = await waitForEnterpriseCard(page);

  const cardTexts = {
    eyebrow: String(await page.locator('.enterprise-enablement-eyebrow').textContent() || '').trim(),
    heading: String(await page.locator('.enterprise-enablement-header h3').textContent() || '').trim(),
    lead: String(await page.locator('.enterprise-enablement-lead').textContent() || '').trim(),
    step_labels: await page.locator('.enterprise-step strong').allTextContents(),
  };
  writeJson('home_card_texts.json', cardTexts);

  const sessionSnapshot = await readSessionSnapshot(page);
  writeJson('session_snapshot.json', sessionSnapshot);
  await page.screenshot({ path: path.join(outDir, 'enterprise_enablement_home.png'), fullPage: true });

  assert(cardTexts.eyebrow === '企业启用', 'home should show enterprise enablement card');
  assert(cardTexts.step_labels.length >= 3, 'enterprise enablement steps should be visible');
  assert(Array.isArray(sessionSnapshot.enterprise_enablement?.steps), 'session cache missing enterprise enablement steps');
  assert(sessionSnapshot.enterprise_enablement.steps.length >= 3, 'enterprise enablement steps should be cached');
  assert(Number(sessionSnapshot.enterprise_enablement?.primary_action?.action_id || 0) > 0, 'primary action should resolve to action id');
  assert(sessionSnapshot.user_groups.includes('base.group_system'), 'Sprint 0 frontend user should carry base.group_system');

  log('follow primary action');
  await followPrimaryAction(page, sessionSnapshot);
  await page.waitForURL((url) => url.pathname.startsWith('/a/'), { timeout: 20000, waitUntil: 'commit' });
  await page.waitForLoadState('domcontentloaded');

  const actionUrl = new URL(page.url());
  const actionSnapshot = {
    href: page.url(),
    pathname: actionUrl.pathname,
    action_id: Number((actionUrl.pathname.match(/\/a\/(\d+)/) || [])[1] || 0),
    menu_id: Number(actionUrl.searchParams.get('menu_id') || 0),
  };
  writeJson('primary_action_navigation.json', actionSnapshot);
  await page.screenshot({ path: path.join(outDir, 'enterprise_enablement_action.png'), fullPage: true });
  writeJson('action_page_debug.json', await readActionPageDebug(page, actionSnapshot.action_id));

  assert(actionSnapshot.action_id > 0, 'primary action route should contain action id');
  assert(actionSnapshot.menu_id > 0, 'primary action route should contain menu_id');
  assert(summary.system_init_calls.some((item) => item.has_mainline && item.step_count >= 3 && item.primary_action_id > 0), 'system.init should expose enterprise enablement mainline');

  log('open company create form');
  await openCompanyCreateForm(page);
  writeJson('company_form_debug.json', await readCompanyFormDebug(page));
  await page.getByText('这里只维护企业启用所需的基础信息').waitFor({ state: 'visible', timeout: 20000 });
  const companyFormSnapshot = {
    href: page.url(),
    has_enterprise_hint: await page.getByText('这里只维护企业启用所需的基础信息').isVisible(),
    has_short_name: await page.getByText('公司简称').isVisible(),
    has_credit_code: await page.getByText('统一社会信用代码').isVisible(),
    has_forbidden_rel_field: await page.getByText('partner_id').count(),
    has_relation_forbidden: await page.getByText('RELATION_READ_FORBIDDEN').count(),
  };
  writeJson('company_create_form_snapshot.json', companyFormSnapshot);
  await page.screenshot({ path: path.join(outDir, 'enterprise_enablement_company_create.png'), fullPage: true });

  assert(companyFormSnapshot.has_enterprise_hint, 'company create form should show enterprise bootstrap hint');
  assert(companyFormSnapshot.has_short_name, 'company create form should expose short name field');
  assert(companyFormSnapshot.has_credit_code, 'company create form should expose credit code field');
  assert(companyFormSnapshot.has_forbidden_rel_field === 0, 'company create form should not leak partner_id');
  assert(companyFormSnapshot.has_relation_forbidden === 0, 'company create form should not leak RELATION_READ_FORBIDDEN');

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Enterprise Enablement Frontend Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      `- home_card: \`${cardTexts.heading}\``,
      `- step_count: \`${cardTexts.step_labels.length}\``,
      `- primary_route: \`${actionSnapshot.href}\``,
      `- console_error_count: \`${summary.console_errors.length}\``,
      `- page_error_count: \`${summary.page_errors.length}\``,
      '',
      '## Checks',
      '- `system.init` returns `ext_facts.enterprise_enablement.mainline`',
      '- Home page renders enterprise enablement card for admin user',
      '- Card exposes at least three visible steps',
      '- Primary CTA navigates to the unique company action route',
      '- Company list exposes explicit `新建公司` primary action',
      '- Company create form uses enterprise bootstrap form instead of native company settings form',
    ].join('\n'),
    'utf8',
  );
  log(`PASS artifacts=${outDir}`);
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  try {
    if (page) {
      await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
    }
  } catch {
    // ignore screenshot failure
  }
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) await browser.close();
}
