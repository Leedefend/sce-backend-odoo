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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'second-slice-browser-smoke', ts);

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
  console.log(`[second_slice_browser_smoke] ${message}`);
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
  const cardText = await firstCard.innerText();
  assert(cardText.includes('下一步：'), `unexpected execution action card: ${cardText}`);
  const button = firstCard.locator('button.primary-button');
  const disabled = await button.isDisabled();
  assert(!disabled, `execution advance disabled: ${cardText}`);
  await button.click();
  return cardText;
}

async function waitForFeedback(page) {
  const banner = page.locator('.feedback-banner').first();
  await banner.waitFor({ timeout: 20000 });
  return banner.innerText();
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

  log('open quick create');
  await page.goto(`${BASE_URL}/f/project.project/new?scene_key=projects.intake&intake_mode=quick`, { waitUntil: 'networkidle' });
  await page.locator('.form-flow-guide-main').filter({ hasText: '只需完成核心信息即可创建项目' }).waitFor({ timeout: 20000 });
  await page.getByRole('button', { name: '创建项目' }).waitFor({ timeout: 20000 });

  const projectName = `FR2-BROWSER-${Date.now()}`;
  await fillPrimaryName(page, projectName);
  const selects = page.locator('select.input');
  const selectCount = await selects.count();
  assert(selectCount >= 1, 'quick create page missing selectable fields');
  await selectFirstValidOption(selects.first());
  await page.getByRole('button', { name: '创建项目' }).click();

  log('wait dashboard');
  await waitForScene(page, '项目驾驶舱', ['项目进度', '风险提醒', '下一步动作']);
  const dashboard = await snapshot(page);
  writeJson('dashboard_snapshot.json', dashboard);
  assert(!dashboard.search.includes('project_id='), 'dashboard route should not depend on project_id query');

  log('enter execution');
  await clickActionCard(page, '下一步：进入执行推进');
  await waitForScene(page, '执行推进', ['执行任务', '试点前检查', '执行下一步']);
  const execution = await snapshot(page);
  writeJson('execution_snapshot.json', execution);
  assert(execution.text.includes('执行推进'), 'execution scene label missing');
  assert(execution.text.includes('执行任务'), 'execution missing tasks block');
  assert(execution.text.includes('试点前检查'), 'execution missing pilot precheck block');
  assert(execution.text.includes('执行下一步'), 'execution missing next_actions block');

  log('advance execution');
  const executionAdvanceLabel = await clickExecutionAdvance(page);
  const feedback = await waitForFeedback(page);
  const afterAdvance = await snapshot(page);
  writeJson('after_advance_snapshot.json', afterAdvance);
  assert(feedback.includes('动作执行完成'), `unexpected feedback: ${feedback}`);
  assert(feedback.includes('状态变化：'), `missing state transition feedback: ${feedback}`);
  assert(!afterAdvance.text.includes('动作执行失败'), 'execution shows action failure');

  summary.cases.push({
    case_id: 'second_slice_quick_create_to_execution_advance',
    status: 'PASS',
    route: `${afterAdvance.pathname}${afterAdvance.search}`,
    project_name: projectName,
    execution_advance_label: executionAdvanceLabel,
    feedback,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Second Slice Browser Smoke',
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
