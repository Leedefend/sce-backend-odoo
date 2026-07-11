const { chromium } = require('playwright');
const fs = require('node:fs');

const base = process.env.BASE_URL || 'http://127.0.0.1:5174';
const dbName = process.env.DB || 'sc_demo';
const loginName = process.env.LOGIN || 'wutao';
const password = process.env.PASSWORD || '123456';
const outPath = process.env.OUT || '/tmp/action_runtime_targeted_acceptance.json';

function defaultTargets() {
  return [
    { action: 973, model: 'sc.finance.project.capital.position', maxDataMs: 2200 },
    { action: 975, model: 'sc.finance.counterparty.position.summary', maxDataMs: 2200 },
    { action: 974, model: 'sc.finance.project.counterparty.position', maxDataMs: 2200 },
    { action: 999, model: 'sc.self.funding.registration', maxDataMs: 700 },
    { action: 998, model: 'sc.self.funding.registration', maxDataMs: 700 },
  ];
}

function parseTargets() {
  const raw = String(process.env.TARGETS || '').trim();
  if (!raw) return defaultTargets();
  return raw.split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      const [actionRaw, modelRaw, maxDataRaw] = item.split(':');
      const action = Number(actionRaw || 0);
      const model = String(modelRaw || '').trim();
      const maxDataMs = Number(maxDataRaw || 0) || 2000;
      if (!action || !model) throw new Error(`invalid target: ${item}`);
      return { action, model, maxDataMs };
    });
}

async function login(page) {
  await page.goto(`${base}/login?db=${encodeURIComponent(dbName)}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('input', { timeout: 60000 });
  await page.locator('input').nth(0).fill(loginName);
  await page.locator('input[type="password"]').fill(password);
  if (await page.locator('input').count() >= 3) {
    const dbInput = page.locator('input').nth(2);
    if (await dbInput.isEnabled().catch(() => false)) await dbInput.fill(dbName);
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForURL((url) => !String(url).includes('/login'), { timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
}

async function navigateInApp(page, action) {
  await page.evaluate(async (path) => {
    const router = window.__SC_ROUTER__;
    if (!router || typeof router.push !== 'function') {
      throw new Error('router hook missing: run dev server or set VITE_E2E_ROUTER_HOOK=1');
    }
    await router.push(path);
  }, `/a/${action}?db=${encodeURIComponent(dbName)}`);
  await page.waitForURL(new RegExp(`/a/${action}(\\\\?|$)`), { timeout: 30000 });
}

async function waitForTargetDataCall(calls, startIndex, target) {
  const deadline = Date.now() + Number(process.env.TARGET_TIMEOUT_MS || 30000);
  while (Date.now() < deadline) {
    const row = calls.slice(startIndex).find((item) => (
      item.intent === 'api.data'
      && String(item.params?.model || '').trim() === target.model
      && String(item.params?.op || '').trim() === 'list'
    ));
    if (row) return row;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return null;
}

async function main() {
  const targets = parseTargets();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' });
  const starts = new Map();
  const calls = [];
  const consoleErrors = [];

  page.on('request', (req) => starts.set(req, Date.now()));
  page.on('response', async (resp) => {
    const req = resp.request();
    if (!resp.url().includes('/api/v1/intent')) return;
    let body = null;
    try {
      body = req.postDataJSON();
    } catch {
      body = null;
    }
    calls.push({
      actionProbe: page.url(),
      intent: body?.intent || '',
      ms: Date.now() - (starts.get(req) || Date.now()),
      params: body?.params || {},
      status: resp.status(),
    });
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text().slice(0, 500));
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message.slice(0, 500)));

  await login(page);
  const results = [];
  for (const target of targets) {
    const before = calls.length;
    await navigateInApp(page, target.action);
    const data = await waitForTargetDataCall(calls, before, target);
    await page.waitForTimeout(300);
    const rows = calls.slice(before);
    const prefs = rows.filter((row) => (
      row.intent === 'user.view.preference.get'
      && Number(row.params?.action_id || 0) === target.action
    ));
    const prefModels = prefs.map((row) => String(row.params?.model || '').trim());
    const emptyPrefs = prefModels.filter((model) => !model);
    const wrongPrefs = prefModels.filter((model) => model && model !== target.model);
    const bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
    const hasErrorText = /render error|页面加载失败|页面异常|系统异常|Traceback|Cannot read/i.test(bodyText);
    results.push({
      action: target.action,
      model: target.model,
      dataMs: data?.ms ?? null,
      maxDataMs: target.maxDataMs,
      prefModels,
      ok: Boolean(data)
        && data.ms <= target.maxDataMs
        && emptyPrefs.length === 0
        && wrongPrefs.length === 0
        && !hasErrorText,
      hasErrorText,
    });
  }
  await browser.close();

  const summary = {
    total: results.length,
    ok: results.filter((row) => row.ok).length,
    failed: results.filter((row) => !row.ok).length,
    consoleErrorCount: consoleErrors.length,
  };
  const report = { summary, results, consoleErrors };
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (summary.failed || summary.consoleErrorCount) process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
