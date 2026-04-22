import fs from 'node:fs';
import path from 'node:path';
import { bootstrapPortalBrowserAuth, launchPortalChromium, resolvePortalSmokeConfig, waitForPortalBootstrapReady } from './playwright_portal_bootstrap.mjs';

const { baseUrl: BASE_URL, apiBaseUrl: API_BASE_URL, dbName: DB_NAME, login: LOGIN, password: PASSWORD, artifactsDir: ARTIFACTS_DIR } = resolvePortalSmokeConfig();
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'cost-slice-browser-smoke', ts);

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
  console.log(`[cost_slice_browser_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
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

async function ensureCostEntryReady(page) {
  const form = page.locator('.cost-form-card').first();
  try {
    await form.waitFor({ timeout: 8000 });
    return form;
  } catch {
    const entryCard = page.locator('.block-card').filter({ hasText: '成本录入' }).first();
    await entryCard.getByRole('button', { name: '刷新' }).click();
    try {
      await form.waitFor({ timeout: 20000 });
    } catch (error) {
      const debug = await page.evaluate(async () => {
        const response = await fetch('/api/v1/intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            intent: 'cost.tracking.block.fetch',
            params: { block_key: 'cost_entry' },
          }),
        });
        return response.json();
      }).catch((err) => ({ fetch_error: String(err?.message || err) }));
      throw new Error(`cost_entry block not ready: ${JSON.stringify(debug)}`);
    }
    return form;
  }
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
  browser = await launchPortalChromium();
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  log('login');
  await bootstrapPortalBrowserAuth(page, {
    apiBaseUrl: API_BASE_URL || BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    password: PASSWORD,
  });
  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForPortalBootstrapReady(page);

  log('quick create project');
  await page.goto(`${BASE_URL}/f/project.project/new?scene_key=projects.intake&intake_mode=quick`, { waitUntil: 'networkidle' });
  await page.locator('.form-flow-guide-main').filter({ hasText: '只需完成核心信息即可创建项目' }).waitFor({ timeout: 20000 });
  const projectName = `FR3-COST-${Date.now()}`;
  await fillPrimaryName(page, projectName);
  const selects = page.locator('select.input');
  const selectCount = await selects.count();
  assert(selectCount >= 1, 'quick create page missing selectable fields');
  await selectFirstValidOption(selects.first());
  await page.getByRole('button', { name: '创建项目' }).click();

  log('dashboard');
  await waitForScene(page, '项目驾驶舱', ['项目进度', '风险提醒', '下一步动作']);
  const dashboard = await snapshot(page);
  writeJson('dashboard_snapshot.json', dashboard);
  assert(!dashboard.search.includes('project_id='), 'dashboard route should not depend on project_id query');

  log('execution');
  await clickActionCard(page, '下一步：进入执行推进');
  await waitForScene(page, '执行推进', ['执行任务', '试点前检查', '执行下一步']);
  const execution = await snapshot(page);
  writeJson('execution_snapshot.json', execution);

  log('execution advance');
  await clickExecutionAdvance(page);
  const executionFeedback = await waitForFeedback(page, '动作执行完成');
  assert(executionFeedback.includes('状态变化：'), `missing state transition feedback: ${executionFeedback}`);

  log('enter cost');
  await clickActionCard(page, '下一步：进入成本记录');
  await waitForScene(page, '成本记录', ['成本录入', '成本记录', '成本汇总']);
  const costScene = await snapshot(page);
  writeJson('cost_scene_snapshot.json', costScene);

  log('fill cost form');
  const costForm = await ensureCostEntryReady(page);
  await costForm.locator('input[type="date"]').fill('2026-03-23');
  await costForm.locator('input[type="number"]').fill('678.90');
  await costForm.locator('input[type="text"]').fill('FR-3 browser smoke cost');
  const categorySelect = costForm.locator('select').first();
  const categoryCount = await categorySelect.locator('option').count();
  if (categoryCount > 1) {
    await categorySelect.selectOption({ index: 1 });
  }
  await costForm.getByRole('button', { name: '记录成本' }).click();
  const costFeedback = await waitForFeedback(page, '成本记录已创建');
  assert(costFeedback.includes('已创建') || costFeedback.includes('draft account.move'), `unexpected cost feedback: ${costFeedback}`);

  log('assert cost list and summary');
  await refreshBlockCard(page, '成本记录');
  await refreshBlockCard(page, '成本汇总');
  await page.waitForTimeout(1500);
  const bodyText = await page.locator('body').innerText();
  assert(bodyText.includes('FR-3 browser smoke cost'), 'cost list missing created record');
  assert(bodyText.includes('项目成本合计'), 'cost summary missing total label');
  assert(bodyText.includes('678.9') || bodyText.includes('678.90'), 'cost summary missing amount');

  const finalSnapshot = await snapshot(page);
  writeJson('final_snapshot.json', finalSnapshot);

  summary.cases.push({
    case_id: 'fr3_cost_slice_prepared_browser_smoke',
    status: 'PASS',
    route: `${finalSnapshot.pathname}${finalSnapshot.search}`,
    project_name: projectName,
    feedback: costFeedback,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Cost Slice Browser Smoke',
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
