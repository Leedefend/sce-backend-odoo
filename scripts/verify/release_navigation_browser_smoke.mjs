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
const API_BASE_URL = String(process.env.API_BASE_URL || 'http://127.0.0.1:18069').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_prod_sim').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'demo_pm').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'release-navigation-browser-smoke', ts);
const EXPECTED_LABELS = [
  'FR-1 项目立项',
  'FR-2 项目推进',
  'FR-3 成本记录',
  'FR-4 付款记录',
  'FR-5 结算结果',
  '我的工作',
];

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  expected_labels: EXPECTED_LABELS,
  console_errors: [],
  page_errors: [],
  cases: [],
};

function log(message) {
  console.log(`[release_navigation_browser_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function recoverFromTransientFailure(page) {
  const retryButton = page.getByRole('button', { name: /Retry|重试/ });
  if (await retryButton.count()) {
    await retryButton.first().click().catch(() => {});
  } else {
    await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
  }
  await page.waitForTimeout(1500);
}

async function waitForSidebar(page) {
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.locator('.sidebar').waitFor({ timeout: 20000 });
      return;
    } catch (error) {
      lastError = error;
      await recoverFromTransientFailure(page);
    }
  }
  throw lastError;
}

async function expandSidebarTree(page) {
  for (let round = 0; round < 3; round += 1) {
    const toggles = page.locator('.sidebar .toggle');
    const count = await toggles.count();
    if (!count) return;
    for (let index = 0; index < count; index += 1) {
      const toggle = toggles.nth(index);
      const marker = String((await toggle.textContent().catch(() => '')) || '').trim();
      if (marker.includes('▸')) {
        await toggle.click().catch(() => {});
      }
    }
    await page.waitForTimeout(400);
  }
}

async function waitForReleaseNavigation(page) {
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      await expandSidebarTree(page);
      await page.waitForFunction((labels) => {
        const textNodes = Array.from(
          document.querySelectorAll('.sidebar .label, .sidebar .role-menu-item, .sidebar .title, .sidebar .role-label')
        )
          .map((el) => (el.textContent || '').trim())
          .filter(Boolean);
        return labels.every((label) => textNodes.includes(label));
      }, EXPECTED_LABELS, { timeout: 12000 });
      return;
    } catch (error) {
      lastError = error;
      await recoverFromTransientFailure(page);
    }
  }
  throw lastError;
}

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function fetchLoginToken() {
  let payload = null;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const response = await fetch(`${API_BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Anonymous-Intent': 'true',
      },
      body: JSON.stringify({
        intent: 'login',
        params: {
          login: LOGIN,
          password: PASSWORD,
          contract_mode: 'default',
          db: DB_NAME,
        },
      }),
    });
    payload = {
      status: response.status,
      text: await response.text(),
    };
    if (Number(payload?.status || 0) === 200) {
      const parsed = JSON.parse(String(payload?.text || '{}'));
      const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
      const token = String(data?.session?.token || data?.token || '').trim();
      assert(token, 'login response missing token');
      return token;
    }
    await page.waitForTimeout(1500);
  }
  assert(Number(payload?.status || 0) === 200, `login http status drift: ${payload?.status}`);
  return '';
}

async function bootstrapLogin(page) {
  const token = await fetchLoginToken();
  await page.addInitScript(({ token, dbName }) => {
    sessionStorage.setItem(`sc_auth_token:${dbName}`, token);
    sessionStorage.setItem('sc_auth_token:default', token);
    sessionStorage.setItem('sc_auth_token:test', token);
    sessionStorage.setItem('sc_auth_token', token);
    sessionStorage.setItem('sc_active_db:default', dbName);
    sessionStorage.setItem('sc_active_db:test', dbName);
    localStorage.setItem('sc_active_db:default', dbName);
    localStorage.setItem('sc_active_db:test', dbName);
  }, { token, dbName: DB_NAME });
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

  log('login demo_pm');
  await bootstrapLogin(page);
  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await waitForSidebar(page);
  await waitForReleaseNavigation(page);

  const snapshot = await page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    const sidebarText = Array.from(
      document.querySelectorAll('.sidebar .label, .sidebar .role-menu-item, .sidebar .title, .sidebar .role-label')
    )
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    return {
      href: window.location.href,
      pathname: window.location.pathname,
      search: window.location.search,
      title: document.title,
      sidebar_text: sidebarText,
      cache_release_labels: ((cache?.releaseNavigationTree || []).flatMap((root) =>
        (root.children || []).flatMap((group) =>
          (group.children || []).map((child) => child.label || child.title || child.name || '')
        )
      )).filter(Boolean),
    };
  });
  snapshot.release_labels = snapshot.cache_release_labels.length ? snapshot.cache_release_labels : snapshot.sidebar_text;

  for (const label of EXPECTED_LABELS) {
    assert(snapshot.release_labels.includes(label), `release navigation missing label: ${label}`);
    assert(snapshot.sidebar_text.includes(label), `sidebar missing label: ${label}`);
  }
  writeJson('sidebar_snapshot.json', snapshot);
  await page.screenshot({ path: path.join(outDir, 'sidebar.png'), fullPage: true });

  summary.cases.push({
    case_id: 'release_navigation_visible_for_demo_pm',
    status: 'PASS',
    route: `${snapshot.pathname}${snapshot.search}`,
  });
  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Release Navigation Browser Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      '',
      '## Expected Labels',
      ...EXPECTED_LABELS.map((item) => `- ${item}`),
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
