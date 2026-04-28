import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(path.join(process.cwd(), 'package.json'));
const { chromium } = require('playwright');

const frontendUrl = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const dbName = process.env.DB_NAME || 'sc_prod_sim';
const closureAction = String(process.env.BROWSER_CLOSURE_ACTION || 'approve').trim().toLowerCase();
const artifactDir = process.env.BUSINESS_BROWSER_ARTIFACT_DIR
  || path.resolve('artifacts/browser-real-user-business-closure/current');
const setupPath = path.join(artifactDir, 'setup.json');
const actionButtonLabel = closureAction === 'reject' ? '审批驳回' : '审批通过';
const browserStatus = closureAction === 'reject' ? 'rejected_and_removed_from_todo' : 'approved_and_removed_from_todo';

function writeJson(name, data) {
  fs.mkdirSync(artifactDir, { recursive: true });
  fs.writeFileSync(path.join(artifactDir, name), JSON.stringify(data, null, 2), 'utf8');
}

async function login(page, user) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(user.login);
  await inputs.nth(1).fill(user.password);
  await inputs.nth(2).fill(dbName);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function runCase(browser, row, index) {
  const context = await browser.newContext({ locale: 'zh-CN' });
  const page = await context.newPage();
  const user = { login: row.reviewer_login, password: row.reviewer_password };
  const title = String(row.title || '');
  const screenshotBase = `case_${index + 1}_${row.model.replaceAll('.', '_')}`;
  try {
    await login(page, user);
    await page.goto(`${frontendUrl}/my-work?section=todo&search=${encodeURIComponent(title)}`, {
      waitUntil: 'networkidle',
    });
    await page.getByRole('heading', { name: /我的工作/ }).waitFor({ timeout: 20000 });
    const todoEntry = page.getByText(title, { exact: false }).first();
    await todoEntry.waitFor({ timeout: 20000 });
    await page.screenshot({ path: path.join(artifactDir, `${screenshotBase}_todo.png`), fullPage: true });
    await todoEntry.click();
    await page.waitForURL((url) => url.pathname.includes(`/r/${row.model}/${row.record_id}`), { timeout: 20000 });
    await page.getByRole('button', { name: actionButtonLabel }).waitFor({ timeout: 20000 });
    await page.screenshot({ path: path.join(artifactDir, `${screenshotBase}_record_before.png`), fullPage: true });
    await page.getByRole('button', { name: actionButtonLabel }).click();
    await page.getByText(/操作成功|审批通过|审批驳回|执行成功|validated|rejected|已完成/, { exact: false }).first().waitFor({ timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(artifactDir, `${screenshotBase}_record_after.png`), fullPage: true });
    await page.goto(`${frontendUrl}/my-work?section=todo&search=${encodeURIComponent(title)}`, {
      waitUntil: 'networkidle',
    });
    await page.waitForTimeout(1000);
    const stillVisible = await page.getByText(title, { exact: false }).count();
    await page.screenshot({ path: path.join(artifactDir, `${screenshotBase}_todo_after.png`), fullPage: true });
    if (stillVisible > 0) {
      throw new Error(`${row.model}/${row.record_id} still visible in todo after approval`);
    }
    return {
      model: row.model,
      record_id: row.record_id,
      reviewer_login: row.reviewer_login,
      title,
      browser_status: browserStatus,
    };
  } finally {
    await context.close();
  }
}

async function main() {
  const setup = JSON.parse(fs.readFileSync(setupPath, 'utf8'));
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const [index, row] of setup.cases.entries()) {
      results.push(await runCase(browser, row, index));
    }
  } finally {
    await browser.close();
  }
  writeJson('browser_summary.json', {
    frontend_url: frontendUrl,
    db_name: dbName,
    action: closureAction,
    results,
  });
  console.log('[business_real_user_browser_closure] PASS');
  console.log(JSON.stringify(results, null, 2));
}

main().catch((err) => {
  writeJson('browser_error.json', {
    message: err.message,
    stack: err.stack,
  });
  console.error(`[business_real_user_browser_closure] FAIL: ${err.message}`);
  process.exit(1);
});
