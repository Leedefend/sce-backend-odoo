import fs from 'node:fs';
import path from 'node:path';
import { bootstrapPortalBrowserAuth, launchPortalChromium, resolvePortalSmokeConfig, waitForPortalBootstrapReady } from './playwright_portal_bootstrap.mjs';

const { baseUrl: BASE_URL, apiBaseUrl: API_BASE_URL, dbName: DB_NAME, login: LOGIN, password: PASSWORD, artifactsDir: ARTIFACTS_DIR } = resolvePortalSmokeConfig();
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
      if (key && key.startsWith('sc_frontend_session_v0_5')) cacheKeys.push(key);
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
  browser = await launchPortalChromium();
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      summary.console_errors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  log('case 1: bootstrap auth');
  await bootstrapPortalBrowserAuth(page, {
    apiBaseUrl: API_BASE_URL || BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    password: PASSWORD,
  });
  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForPortalBootstrapReady(page);

  const loginState = await readSessionSnapshot(page);
  writeJson('case_login_success.json', loginState);
  assert(loginState.pathname !== '/login', 'bootstrap auth stayed on /login');
  assert(loginState.token_keys.length > 0, 'fresh login missing scoped token');
  assert(loginState.token_values.some((value) => value && value !== 'invalid.browser.smoke.token'), 'fresh login token empty');
  assert(loginState.href.includes(`db=${encodeURIComponent(DB_NAME)}`) || loginState.search.includes(`db=${encodeURIComponent(DB_NAME)}`), 'bootstrap auth missing db binding');
  summary.cases.push({
    case_id: 'bootstrap_auth',
    status: 'PASS',
    route: `${loginState.pathname}${loginState.search}`,
  });

  const protectedPath = `${loginState.pathname}${loginState.search}` || '/';
  log(`case 2: bootstrap recovery via ${protectedPath}`);
  await poisonTokens(page);
  const poisonedState = await readSessionSnapshot(page);
  writeJson('case_poisoned_token_snapshot.json', poisonedState);
  assert(poisonedState.token_values.some((value) => value === 'invalid.browser.smoke.token'), 'poisoned token state not applied');

  await bootstrapPortalBrowserAuth(page, {
    apiBaseUrl: API_BASE_URL || BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    password: PASSWORD,
  });
  await page.goto(`${BASE_URL}${protectedPath}`, { waitUntil: 'domcontentloaded' });
  await waitForPortalBootstrapReady(page);

  const reloginState = await readSessionSnapshot(page);
  writeJson('case_relogin_success.json', reloginState);
  assert(reloginState.pathname !== '/login', 'bootstrap recovery stayed on /login');
  assert(reloginState.token_values.some((value) => value && value !== 'invalid.browser.smoke.token'), 'relogin token not refreshed');
  summary.cases.push({
    case_id: 'bootstrap_recover_from_poisoned_token',
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
