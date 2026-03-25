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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'project-dashboard-primary-entry-browser-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  cases: [],
  console_errors: [],
  page_errors: [],
};

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

async function waitForDashboard(page) {
  await page.waitForFunction(() => window.location.pathname === '/s/project.management', { timeout: 40000 });
  await page.locator('h1').filter({ hasText: '项目驾驶舱' }).first().waitFor({ timeout: 40000 });
  await page.locator('.state-explain-card').waitFor({ timeout: 40000 });
  await page.locator('h2').filter({ hasText: '下一步动作' }).first().waitFor({ timeout: 40000 });
  await page.locator('.action-card').first().waitFor({ timeout: 40000 });
}

async function clickActionCard(page, labelText) {
  const patterns = Array.isArray(labelText) ? labelText : [labelText];
  let card = null;
  for (const pattern of patterns) {
    const candidate = page.locator('.action-card').filter({ hasText: pattern }).first();
    try {
      await candidate.waitFor({ timeout: 10000 });
      card = candidate;
      break;
    } catch {}
  }
  if (!card) {
    throw new Error(`action not found: ${patterns.join(' | ')}`);
  }
  await card.waitFor({ timeout: 20000 });
  await card.locator('button.primary-button').click();
}

async function waitForScene(page, sceneLabel) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.locator('.eyebrow').filter({ hasText: sceneLabel }).first().waitFor({ timeout: 20000 });
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

  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  await fillLoginForm(page);
  await submitLogin(page);
  await waitForDashboard(page);

  const dashboardText = await page.locator('body').innerText();
  assert(dashboardText.includes('阶段说明'), 'dashboard missing stage explain');
  assert(dashboardText.includes('里程碑说明'), 'dashboard missing milestone explain');
  assert(dashboardText.includes('当前状态说明'), 'dashboard missing status explain');
  await page.locator('.recommended-badge').first().waitFor({ timeout: 20000 });

  await clickActionCard(page, '下一步：进入执行推进');
  await waitForScene(page, '执行推进');
  const execButton = page.locator('.action-list .action-card button.primary-button').first();
  await execButton.waitFor({ timeout: 20000 });
  await execButton.click();
  await waitForDashboard(page);

  await clickActionCard(page, ['继续：进入成本记录', '下一步：进入成本记录']);
  await waitForScene(page, '成本记录');
  const costForm = page.locator('.cost-form-card').first();
  await costForm.locator('input[type="date"]').fill('2026-03-26');
  await costForm.locator('input[type="number"]').fill('88.50');
  await costForm.locator('input[type="text"]').fill('main-entry-browser-smoke');
  const categorySelect = costForm.locator('select').first();
  if (await categorySelect.count()) {
    const optionCount = await categorySelect.locator('option').count();
    if (optionCount > 1) {
      await categorySelect.selectOption({ index: 1 });
    }
  }
  await costForm.getByRole('button', { name: /记录成本/ }).click();
  await waitForDashboard(page);

  const finalSnapshot = await page.evaluate(() => ({
    href: window.location.href,
    pathname: window.location.pathname,
    text: document.body.innerText,
  }));
  assert(finalSnapshot.pathname === '/s/project.management', 'final route drifted away from dashboard');
  assert(!finalSnapshot.href.includes('project_id='), 'dashboard route should not depend on project_id query');

  writeJson('dashboard_snapshot.json', finalSnapshot);
  await page.screenshot({ path: path.join(outDir, 'project_dashboard_primary_entry.png'), fullPage: true });

  summary.cases.push({
    case_id: 'project_dashboard_primary_entry',
    status: 'PASS',
    route: '/s/project.management',
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Project Dashboard Primary Entry Browser Smoke',
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
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  try {
    if (page) {
      await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
    }
  } catch {}
  writeJson('summary.json', summary);
  throw error;
} finally {
  if (browser) await browser.close();
}
