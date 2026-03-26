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

async function followPrimaryAction(page, sessionSnapshot) {
  const primaryAction = sessionSnapshot?.enterprise_enablement?.primary_action || null;
  const route = String(primaryAction?.route || '').trim();
  const menuId = Number(primaryAction?.menu_id || 0);
  const targetUrl = route
    ? `${BASE_URL}${route}${route.includes('?') ? '&' : '?'}menu_id=${encodeURIComponent(String(menuId || 0))}`
    : '';
  if (!targetUrl) throw new Error('enterprise primary action route is missing');
  log(`navigate to primary action route ${route}`);
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
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
  assert(cardTexts.step_labels.length >= 2, 'enterprise enablement steps should be visible');
  assert(Array.isArray(sessionSnapshot.enterprise_enablement?.steps), 'session cache missing enterprise enablement steps');
  assert(sessionSnapshot.enterprise_enablement.steps.length >= 2, 'enterprise enablement steps should be cached');
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

  assert(actionSnapshot.action_id > 0, 'primary action route should contain action id');
  assert(actionSnapshot.menu_id > 0, 'primary action route should contain menu_id');
  assert(summary.system_init_calls.some((item) => item.has_mainline && item.step_count >= 2 && item.primary_action_id > 0), 'system.init should expose enterprise enablement mainline');

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
      '- Card exposes at least two visible steps',
      '- Primary CTA navigates to the unique company action route',
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
