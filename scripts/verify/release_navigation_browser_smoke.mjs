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

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 20000, waitUntil: 'commit' });
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
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  await fillLoginForm(page);
  await submitLogin(page);
  await page.waitForLoadState('networkidle');
  await page.locator('.sidebar').waitFor({ timeout: 20000 });

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
      release_labels: ((cache?.releaseNavigationTree || []).flatMap((root) =>
        (root.children || []).flatMap((group) =>
          (group.children || []).map((child) => child.label || child.title || child.name || '')
        )
      )).filter(Boolean),
    };
  });

  for (const label of EXPECTED_LABELS) {
    assert(snapshot.release_labels.includes(label), `releaseNavigationTree missing label: ${label}`);
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
