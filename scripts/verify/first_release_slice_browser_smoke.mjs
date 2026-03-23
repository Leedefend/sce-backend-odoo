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
const LOGIN = String(process.env.E2E_LOGIN || 'svc_e2e_smoke').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'first-release-slice-browser-smoke', ts);

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
  console.log(`[first_release_slice_browser_smoke] ${message}`);
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

async function fillPrimaryName(page, value) {
  const input = page.locator('.field input.input').first();
  await input.fill(value);
}

async function selectFirstValidOption(select) {
  const optionValue = await select.evaluate((node) => {
    const options = Array.from(node.querySelectorAll('option'));
    const candidate = options.find((option) => {
      const value = String(option.getAttribute('value') || '').trim();
      return value && value !== '__create__';
    });
    return candidate ? String(candidate.getAttribute('value') || '') : '';
  });
  assert(optionValue, 'no selectable option found');
  await select.selectOption(optionValue);
}

async function waitForDashboard(page) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.locator('h1').filter({ hasText: '项目驾驶舱' }).first().waitFor({ timeout: 20000 });
}

async function snapshot(page) {
  return page.evaluate(() => ({
    href: window.location.href,
    pathname: window.location.pathname,
    search: window.location.search,
    title: document.title,
    text: document.body.innerText,
  }));
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

  log('login');
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  await fillLoginForm(page);
  await submitLogin(page);
  await page.waitForLoadState('networkidle');

  log('open first release quick create');
  await page.goto(`${BASE_URL}/f/project.project/new?scene_key=projects.intake&intake_mode=quick`, { waitUntil: 'networkidle' });
  await page.locator('.form-flow-guide-main').filter({ hasText: '只需完成核心信息即可创建项目' }).waitFor({ timeout: 20000 });
  await page.getByRole('button', { name: '创建项目' }).waitFor({ timeout: 20000 });

  const projectName = `P2R-BROWSER-${Date.now()}`;
  await fillPrimaryName(page, projectName);
  const selects = page.locator('select.input');
  const selectCount = await selects.count();
  assert(selectCount >= 1, 'quick create page missing selectable fields');
  await selectFirstValidOption(selects.first());
  await page.getByRole('button', { name: '创建项目' }).click();

  await waitForDashboard(page);
  const dash = await snapshot(page);
  writeJson('dashboard_snapshot.json', dash);

  assert(dash.pathname === '/s/project.management', `unexpected dashboard path: ${dash.pathname}`);
  assert(dash.search.includes('project_id='), 'dashboard route missing project_id');
  assert(dash.text.includes('项目进度'), 'dashboard missing progress block');
  assert(dash.text.includes('风险提醒'), 'dashboard missing risks block');
  assert(dash.text.includes('下一步动作'), 'dashboard missing next_actions block');
  assert(!dash.text.includes('fallback'), 'dashboard contains fallback text');
  assert(!dash.text.includes('unknown'), 'dashboard contains unknown text');

  summary.cases.push({
    case_id: 'first_release_quick_create_to_dashboard',
    status: 'PASS',
    route: `${dash.pathname}${dash.search}`,
    project_name: projectName,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# First Release Slice Browser Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
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
    // ignore
  }
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) await browser.close();
}
