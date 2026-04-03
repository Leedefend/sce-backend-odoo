import fs from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

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

function buildLoginUrlCandidates(baseUrl, dbName) {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const encodedDb = encodeURIComponent(dbName);
  const out = new Set();
  const push = (url) => {
    if (url && typeof url === 'string') out.add(url);
  };

  push(`${base}/login?db=${encodedDb}`);
  if (base.startsWith('http://127.0.0.1')) {
    push(`${base.replace('http://127.0.0.1', 'http://localhost')}/login?db=${encodedDb}`);
  }
  if (base.startsWith('http://localhost')) {
    push(`${base.replace('http://localhost', 'http://127.0.0.1')}/login?db=${encodedDb}`);
  }
  if (/^http:\/\/(127\.0\.0\.1|localhost)$/.test(base)) {
    push(`http://127.0.0.1:8070/login?db=${encodedDb}`);
    push(`http://localhost:8070/login?db=${encodedDb}`);
  }
  return Array.from(out);
}

function isRetriableNavigationError(error) {
  const message = String(error?.message || error || '');
  return (
    message.includes('ERR_NETWORK_CHANGED') ||
    message.includes('ERR_CONNECTION_RESET') ||
    message.includes('ERR_CONNECTION_REFUSED') ||
    message.includes('ERR_CONNECTION_CLOSED') ||
    message.includes('net::ERR_ABORTED') ||
    message.includes('Timeout')
  );
}

async function gotoLoginWithRecovery(page) {
  const candidates = buildLoginUrlCandidates(BASE_URL, DB_NAME);
  const errors = [];
  for (const candidate of candidates) {
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await page.goto(candidate, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForLoadState('domcontentloaded');
        return candidate;
      } catch (error) {
        errors.push({
          url: candidate,
          attempt,
          message: String(error?.message || error),
        });
        if (!isRetriableNavigationError(error) || attempt >= 3) break;
        await sleep(1000 * attempt);
      }
    }
  }
  writeJson('login_navigation_errors.json', errors);
  throw new Error(`login navigation failed after recovery attempts (${errors.length} tries)`);
}

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').waitFor({ timeout: 20000 });
  await page.locator('input[autocomplete="current-password"]').waitFor({ timeout: 20000 });
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
  await page.locator('h1').first().waitFor({ timeout: 40000 });
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

async function clickPrimaryRecommendedAction(page) {
  const primaryCard = page.locator('.action-card-primary').first();
  await primaryCard.waitFor({ timeout: 20000 });
  await primaryCard.locator('button.primary-button').click();
}

async function waitForScene(page, sceneLabel) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.locator('.eyebrow').filter({ hasText: sceneLabel }).first().waitFor({ timeout: 20000 });
}

async function waitForAnyMainlineScene(page) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  const allowed = ['执行推进', '成本记录', '付款记录', '结算结果'];
  await page.waitForFunction((labels) => {
    const text = Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    return labels.some((label) => text.includes(label));
  }, allowed, { timeout: 20000 });
}

async function waitForPrimaryActionResult(page) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  const result = await page.waitForFunction(() => {
    const eyebrowTexts = Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    const inMainline = ['执行推进', '成本记录', '付款记录', '结算结果'].some((label) => eyebrowTexts.includes(label));
    const feedback = document.querySelector('.feedback-banner');
    const onDashboard = eyebrowTexts.includes('项目驾驶舱');
    if (inMainline) return { mode: 'scene', eyebrowTexts };
    if (feedback && onDashboard) {
      return {
        mode: 'dashboard_feedback',
        eyebrowTexts,
        feedbackText: (feedback.textContent || '').trim(),
      };
    }
    return null;
  }, { timeout: 20000 });
  return await result.jsonValue();
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

  const loginUrlUsed = await gotoLoginWithRecovery(page);
  summary.login_url_used = loginUrlUsed;
  await fillLoginForm(page);
  await submitLogin(page);
  await waitForDashboard(page);

  const dashboardText = await page.locator('body').innerText();
  assert(dashboardText.includes('阶段说明'), 'dashboard missing stage explain');
  assert(dashboardText.includes('里程碑说明'), 'dashboard missing milestone explain');
  assert(dashboardText.includes('当前状态说明'), 'dashboard missing status explain');
  assert(dashboardText.includes('流程地图'), 'dashboard missing flow map');
  await page.locator('.project-switcher').first().waitFor({ timeout: 20000 });
  const projectOptionCount = await page.locator('.project-switcher option').count();
  const optionTexts = await page.locator('.project-switcher option').evaluateAll((nodes) =>
    nodes.map((node) => (node.textContent || '').trim()),
  );
  assert(projectOptionCount >= 2, `project switcher should expose at least 2 projects, got ${projectOptionCount}`);
  assert(
    optionTexts.some((text) => text.includes('展厅-')),
    `project switcher should include showroom demo projects, got: ${optionTexts.join(' | ')}`,
  );
  await page.locator('.recommended-badge').first().waitFor({ timeout: 20000 });

  await clickActionCard(page, '下一步：进入执行推进');
  await waitForScene(page, '执行推进');
  const execButton = page.locator('.action-list .action-card button.primary-button').first();
  await execButton.waitFor({ timeout: 20000 });
  await execButton.click();
  await waitForDashboard(page);

  await clickPrimaryRecommendedAction(page);
  const primaryResult = await waitForPrimaryActionResult(page);

  const sceneSnapshot = await page.evaluate(() => ({
    eyebrow: Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean),
    hasCostForm: Boolean(document.querySelector('.cost-form-card')),
    hasPaymentForm: Boolean(document.querySelector('.payment-form-card')),
    hasSettlementSummary: Boolean(document.querySelector('.metric-list')),
  }));

  const finalSnapshot = await page.evaluate(() => ({
    href: window.location.href,
    pathname: window.location.pathname,
    text: document.body.innerText,
  }));
  assert(finalSnapshot.pathname === '/s/project.management', 'final route drifted away from dashboard');
  assert(!finalSnapshot.href.includes('project_id='), 'dashboard route should not depend on project_id query');
  assert(
    primaryResult && (primaryResult.mode === 'scene' || primaryResult.mode === 'dashboard_feedback'),
    'primary action did not produce a valid mainline result',
  );
  if (primaryResult.mode === 'dashboard_feedback') {
    assert(finalSnapshot.text.includes('流程地图'), 'dashboard feedback state missing flow map');
    assert(finalSnapshot.text.includes('下一目标'), 'dashboard feedback state missing completion target');
  }

  writeJson('primary_action_result.json', primaryResult);
  writeJson('scene_snapshot.json', sceneSnapshot);
  writeJson('dashboard_snapshot.json', finalSnapshot);
  await page.screenshot({ path: path.join(outDir, 'project_dashboard_primary_entry.png'), fullPage: true });

  summary.cases.push({
    case_id: 'project_dashboard_primary_entry',
    status: 'PASS',
    route: '/s/project.management',
    project_option_count: projectOptionCount,
    project_option_samples: optionTexts.slice(0, 6),
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
