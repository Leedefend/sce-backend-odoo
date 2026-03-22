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

const BASE_URL = String(process.env.BASE_URL || 'http://localhost:8070').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_demo').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'svc_e2e_smoke').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'login-browser-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  cases: [],
  console_errors: [],
  page_errors: [],
};

function log(message) {
  console.log(`[fe_login_browser_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  try {
    await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 20000, waitUntil: 'commit' });
  } catch (error) {
    const loginError = await page.locator('.error').textContent().catch(() => '');
    throw new Error(
      `login navigation timeout: url=${page.url()} error=${String(loginError || '').trim() || 'none'} cause=${String(error?.message || error)}`,
    );
  }
}

async function readSessionSnapshot(page) {
  return page.evaluate(() => {
    const tokenKeys = [];
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) tokenKeys.push(key);
    }
    const cacheKeys = [];
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (key && key.startsWith('sc_frontend_session_v0_4')) cacheKeys.push(key);
    }
    const cache = cacheKeys.length ? JSON.parse(localStorage.getItem(cacheKeys[0]) || 'null') : null;
    return {
      href: window.location.href,
      pathname: window.location.pathname,
      search: window.location.search,
      token_keys: tokenKeys,
      token_values: tokenKeys.map((key) => sessionStorage.getItem(key) || ''),
      cache_keys: cacheKeys,
      cache,
    };
  });
}

async function poisonTokens(page) {
  await page.evaluate(() => {
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith('sc_auth_token')) {
        sessionStorage.setItem(key, 'invalid.browser.smoke.token');
      }
    }
  });
}

let browser;
let page;
try {
  log('launch browser');
  browser = await chromium.launch({ headless: true, timeout: 20000 });
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      summary.console_errors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  log('case 1: fresh login');
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  await fillLoginForm(page);
  await submitLogin(page);
  await page.waitForLoadState('networkidle');

  const loginState = await readSessionSnapshot(page);
  writeJson('case_login_success.json', loginState);
  assert(loginState.pathname !== '/login', 'fresh login stayed on /login');
  assert(loginState.token_keys.length > 0, 'fresh login missing scoped token');
  assert(loginState.token_values.some((value) => value && value !== 'invalid.browser.smoke.token'), 'fresh login token empty');
  assert(loginState.cache?.menuTree?.length > 0, 'fresh login missing cached menuTree');
  summary.cases.push({
    case_id: 'fresh_login',
    status: 'PASS',
    route: `${loginState.pathname}${loginState.search}`,
  });

  const protectedPath = `${loginState.pathname}${loginState.search}` || '/';
  log(`case 2: 401 redirect recovery via ${protectedPath}`);
  await poisonTokens(page);
  await page.goto(`${BASE_URL}${protectedPath}`, { waitUntil: 'domcontentloaded' });
  await page.waitForURL((url) => url.pathname.startsWith('/login') && url.searchParams.has('redirect'), { timeout: 20000 });

  const redirectState = await readSessionSnapshot(page);
  writeJson('case_401_redirect.json', redirectState);
  assert(redirectState.pathname === '/login', '401 flow did not return to /login');
  assert(redirectState.search.includes('redirect='), '401 flow missing redirect query');
  summary.cases.push({
    case_id: 'auth_401_redirect',
    status: 'PASS',
    route: `${redirectState.pathname}${redirectState.search}`,
  });

  await fillLoginForm(page);
  await submitLogin(page);
  await page.waitForLoadState('networkidle');

  const reloginState = await readSessionSnapshot(page);
  writeJson('case_relogin_success.json', reloginState);
  assert(reloginState.pathname !== '/login', 'relogin stayed on /login');
  assert(reloginState.token_values.some((value) => value && value !== 'invalid.browser.smoke.token'), 'relogin token not refreshed');
  summary.cases.push({
    case_id: 'relogin_after_401',
    status: 'PASS',
    route: `${reloginState.pathname}${reloginState.search}`,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Login Browser Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      `- protected_route: \`${protectedPath}\``,
      `- console_error_count: \`${summary.console_errors.length}\``,
      `- page_error_count: \`${summary.page_errors.length}\``,
      '',
      '## Cases',
      ...summary.cases.map((item) => `- ${item.case_id}: ${item.status} (${item.route})`),
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
  if (browser) {
    await browser.close();
  }
}
