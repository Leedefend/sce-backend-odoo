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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'settlement-slice-browser-smoke', ts);

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
  console.log(`[settlement_slice_browser_smoke] ${message}`);
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

async function waitForScene(page, sceneLabel, headings = []) {
  await page.waitForURL((url) => url.pathname === '/s/project.management', { timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.locator('.eyebrow').filter({ hasText: sceneLabel }).first().waitFor({ timeout: 20000 });
  for (const heading of headings) {
    await page.locator('h2').filter({ hasText: heading }).first().waitFor({ timeout: 20000 });
  }
}

async function clickActionCard(page, labelText) {
  const card = page.locator('.action-card').filter({ hasText: labelText }).first();
  await card.waitFor({ timeout: 20000 });
  const button = card.locator('button.primary-button');
  await button.waitFor({ timeout: 20000 });
  const disabled = await button.isDisabled();
  assert(!disabled, `action disabled: ${labelText}`);
  await button.click();
}

async function clickExecutionAdvance(page) {
  const firstCard = page.locator('.action-list .action-card').first();
  await firstCard.waitFor({ timeout: 20000 });
  const button = firstCard.locator('button.primary-button');
  const disabled = await button.isDisabled();
  assert(!disabled, 'execution advance disabled');
  await button.click();
}

async function waitForFeedback(page, expectedTitle) {
  const banner = page.locator('.feedback-banner').first();
  await banner.waitFor({ timeout: 20000 });
  const text = await banner.innerText();
  assert(text.includes(expectedTitle), `unexpected feedback: ${text}`);
  return text;
}

async function refreshBlockCard(page, titleText) {
  const card = page.locator('.block-card').filter({ hasText: titleText }).first();
  await card.getByRole('button', { name: '刷新' }).click();
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

  log('quick create project');
  await page.goto(`${BASE_URL}/f/project.project/new?scene_key=projects.intake&intake_mode=quick`, { waitUntil: 'networkidle' });
  await page.locator('.form-flow-guide-main').filter({ hasText: '只需完成核心信息即可创建项目' }).waitFor({ timeout: 20000 });
  const projectName = `FR5-SETTLEMENT-${Date.now()}`;
  await fillPrimaryName(page, projectName);
  const selects = page.locator('select.input');
  const selectCount = await selects.count();
  assert(selectCount >= 1, 'quick create page missing selectable fields');
  await selectFirstValidOption(selects.first());
  await page.getByRole('button', { name: '创建项目' }).click();

  await waitForScene(page, '项目驾驶舱', ['项目进度', '风险提醒', '下一步动作']);
  const dashboard = await snapshot(page);
  writeJson('dashboard_snapshot.json', dashboard);
  assert(!dashboard.search.includes('project_id='), 'dashboard route should not depend on project_id query');
  await clickActionCard(page, '下一步：进入执行推进');
  await waitForScene(page, '执行推进', ['执行任务', '试点前检查', '执行下一步']);
  await clickExecutionAdvance(page);
  await waitForFeedback(page, '动作执行完成');

  await clickActionCard(page, '下一步：进入成本记录');
  await waitForScene(page, '成本记录', ['成本录入', '成本记录', '成本汇总']);
  const costForm = page.locator('.cost-form-card').first();
  await costForm.locator('input[type="date"]').fill('2026-03-23');
  await costForm.locator('input[type="number"]').fill('678.90');
  await costForm.locator('input[type="text"]').fill('FR-5 browser smoke cost');
  const categorySelect = costForm.locator('select').first();
  const categoryCount = await categorySelect.locator('option').count();
  if (categoryCount > 1) {
    await categorySelect.selectOption({ index: 1 });
  }
  await costForm.getByRole('button', { name: '记录成本' }).click();
  await waitForFeedback(page, '成本记录已创建');

  await clickActionCard(page, '下一步：进入付款记录');
  await waitForScene(page, '付款记录', ['付款录入', '付款记录', '付款汇总']);
  const paymentForm = page.locator('.payment-form-card').first();
  await paymentForm.locator('input[type="date"]').fill('2026-03-23');
  await paymentForm.locator('input[type="number"]').fill('345.67');
  await paymentForm.locator('input[type="text"]').fill('FR-5 browser smoke payment');
  await paymentForm.getByRole('button', { name: '记录付款' }).click();
  await waitForFeedback(page, '付款记录已创建');

  await clickActionCard(page, '下一步：查看结算结果');
  await waitForScene(page, '结算结果', ['结算结果']);
  await refreshBlockCard(page, '结算结果');
  await page.waitForTimeout(1500);

  const bodyText = await page.locator('body').innerText();
  assert(bodyText.includes('总成本'), 'settlement summary missing total_cost label');
  assert(bodyText.includes('总付款'), 'settlement summary missing total_payment label');
  assert(bodyText.includes('差额'), 'settlement summary missing delta label');
  assert(bodyText.includes('678.9') || bodyText.includes('678.90'), 'settlement summary missing cost amount');
  assert(bodyText.includes('345.67') || bodyText.includes('345.7'), 'settlement summary missing payment amount');
  writeJson('settlement_snapshot.json', await snapshot(page));

  const finalSnapshot = await snapshot(page);
  summary.cases.push({
    case_id: 'fr5_settlement_slice_prepared_browser_smoke',
    status: 'PASS',
    route: `${finalSnapshot.pathname}${finalSnapshot.search}`,
    project_name: projectName,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Settlement Slice Browser Smoke',
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
  }
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) await browser.close();
}
