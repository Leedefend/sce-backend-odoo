const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.BASE_URL || 'http://127.0.0.1:18081';
const rootDir = path.resolve(__dirname, '..', '..', '..', '..');
const artifactRoot = process.env.ARTIFACT_ROOT || path.join(rootDir, 'artifacts', 'playwright', 'user-visible-surface-visual-coverage');
const outPath = process.env.OUT || path.join(artifactRoot, 'report.json');
const maxActions = Number(process.env.MAX_ACTIONS || 0);
const maxForms = Number(process.env.MAX_FORMS || 0);
const skipForms = process.env.SKIP_FORMS === '1';
const skipActions = process.env.SKIP_ACTIONS === '1';
const startIndex = Number(process.env.START_INDEX || 0);
const limit = Number(process.env.LIMIT || 0);
const takeScreenshots = process.env.TAKE_SCREENSHOTS !== '0';

function flattenNav(nodes, path = []) {
  const out = [];
  for (const node of nodes || []) {
    const label = String(node?.label || node?.title || '').trim();
    const nextPath = label ? [...path, label] : path;
    const meta = node?.meta || {};
    const target = meta.entry_target || {};
    const refs = target.compatibility_refs || {};
    const actionId = Number(meta.action_id || refs.action_id || 0);
    const menuId = Number(meta.menu_id || node?.menu_id || refs.menu_id || 0);
    const model = String(meta.model || refs.model || '').trim();
    const sceneKey = String(meta.scene_key || target.scene_key || '').trim();
    if (actionId || sceneKey) {
      out.push({ label, path: nextPath.join(' / '), actionId, menuId, model, sceneKey });
    }
    out.push(...flattenNav(node?.children || [], nextPath));
  }
  return out;
}

function uniqEntries(rows) {
  const seen = new Set();
  const out = [];
  for (const row of rows) {
    const key = row.actionId ? `a:${row.actionId}:${row.menuId || 0}` : `s:${row.sceneKey}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }
  return out;
}

function slug(value) {
  return String(value || '')
    .replace(/[^a-zA-Z0-9._-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 100) || 'surface';
}

async function main() {
  fs.rmSync(artifactRoot, { recursive: true, force: true });
  fs.mkdirSync(path.join(artifactRoot, 'actions'), { recursive: true });
  fs.mkdirSync(path.join(artifactRoot, 'forms'), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  let currentProbe = '';
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push({ probe: currentProbe, text: msg.text().slice(0, 500) });
  });
  page.on('pageerror', (err) => consoleErrors.push({ probe: currentProbe, text: err.message.slice(0, 500) }));

  await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.locator('input').nth(0).fill(process.env.LOGIN || 'wutao');
  await page.locator('input[type="password"]').fill(process.env.PASSWORD || '123456');
  if (await page.locator('input').count() >= 3) {
    const db = page.locator('input').nth(2);
    if (await db.isEnabled().catch(() => false)) await db.fill(process.env.DB || 'sc_demo');
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1000);

  const token = await page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith('sc_auth_token')) || '';
    return key ? sessionStorage.getItem(key) : '';
  });
  if (!token) throw new Error('login token missing');

  async function intent(intentName, params) {
    return await page.evaluate(async ({ intentName, params, token, dbName }) => {
      const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Odoo-DB': dbName, Authorization: `Bearer ${token}` },
        body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true } }),
      });
      const body = await res.json();
      if (!res.ok || body.ok === false) throw new Error(JSON.stringify(body.error || body).slice(0, 700));
      return body.data || body;
    }, { intentName, params, token, dbName: process.env.DB || 'sc_demo' });
  }

  async function waitForSettledUserSurface(targetPage) {
    await targetPage.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    await targetPage.waitForFunction(() => {
      const text = document.body?.innerText || '';
      return !/正在加载列表|正在加载|Loading/i.test(text);
    }, null, { timeout: 15000 }).catch(() => {});
    await targetPage.waitForTimeout(300);
  }

  const init = await intent('system.init', {
    with_preload: false,
    with: ['workspace_home'],
    root_xmlid: 'smart_construction_core.menu_sc_root',
  });
  let entries = uniqEntries(flattenNav(init.nav || []));
  const totalDiscovered = entries.length;
  if (maxActions > 0) entries = entries.slice(0, maxActions);
  if (startIndex > 0 || limit > 0) {
    entries = entries.slice(Math.max(0, startIndex), limit > 0 ? Math.max(0, startIndex) + limit : undefined);
  }

  const actionResults = [];
  const formResults = [];
  let formOpened = 0;
  let lastLoggedIndex = -1;

  function logProgress(index) {
    if (lastLoggedIndex === index) return;
    lastLoggedIndex = index;
    const progress = writeProgress();
    console.log(`[user-page-coverage] ${index + 1}/${entries.length} action_failed=${progress.actionFailed} form_failed=${progress.formFailed}`);
  }

  function writeProgress() {
    const summary = {
      artifactRoot,
      totalDiscovered,
      startIndex,
      limit,
      totalScanned: entries.length,
      actionOk: actionResults.filter((row) => row.ok).length,
      actionFailed: actionResults.filter((row) => !row.ok).length,
      formsScanned: formResults.filter((row) => !row.skipped).length,
      formsSkipped: formResults.filter((row) => row.skipped).length,
      formOk: formResults.filter((row) => !row.skipped && row.ok).length,
      formFailed: formResults.filter((row) => !row.skipped && !row.ok).length,
      consoleErrorCount: consoleErrors.length,
    };
    fs.writeFileSync(outPath, JSON.stringify({
      summary,
      actionFailures: actionResults.filter((row) => !row.ok).slice(0, 100),
      formFailures: formResults.filter((row) => !row.skipped && !row.ok).slice(0, 100),
      formSkipped: formResults.filter((row) => row.skipped).slice(0, 200),
      consoleErrors: consoleErrors.slice(0, 100),
      actionResults,
      formResults,
    }, null, 2));
    return summary;
  }

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const route = entry.actionId
      ? `/a/${entry.actionId}?db=${process.env.DB || 'sc_demo'}${entry.menuId ? `&menu_id=${entry.menuId}` : ''}`
      : `/s/${encodeURIComponent(entry.sceneKey)}?db=${process.env.DB || 'sc_demo'}`;
    if (!skipActions) {
      currentProbe = `list:${entry.path}`;
      const started = Date.now();
      let actionRow = {
        index,
        ...entry,
        route,
        ok: false,
        elapsedMs: 0,
        titleVisible: false,
        hasErrorText: false,
        hasHorizontalOverflow: false,
        screenshotPath: '',
        headers: [],
        issue: '',
      };
      try {
        await page.goto(`${base}${route}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await waitForSettledUserSurface(page);
        const text = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
        const headers = await page.locator('th').evaluateAll((nodes) => (
          nodes.map((node) => node.textContent?.trim()).filter(Boolean).slice(0, 30)
        )).catch(() => []);
        const hasErrorText = /render error|contract not renderable|missing required nav|页面加载失败|页面异常|系统异常|Traceback|Cannot read/i.test(text);
        const hasLoadingText = /正在加载列表|正在加载|Loading/i.test(text);
        const lastLabel = String(entry.path || '').split(' / ').pop() || '';
        const titleVisible = entry.label ? text.includes(entry.label) || text.includes(lastLabel) : true;
        const hasHorizontalOverflow = await page.evaluate(() => (
          document.documentElement.scrollWidth > window.innerWidth + 1 || document.body.scrollWidth > window.innerWidth + 1
        )).catch(() => false);
        let screenshotPath = '';
        if (takeScreenshots) {
          screenshotPath = path.join(artifactRoot, 'actions', `${String(index + 1).padStart(3, '0')}_${slug(entry.path || entry.label)}.png`);
          await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
        }
        actionRow = {
          ...actionRow,
          ok: !hasErrorText && !hasLoadingText && !hasHorizontalOverflow,
          elapsedMs: Date.now() - started,
          titleVisible,
          hasErrorText,
          hasLoadingText,
          hasHorizontalOverflow,
          screenshotPath,
          headers,
        };
      } catch (err) {
        actionRow = { ...actionRow, elapsedMs: Date.now() - started, issue: err instanceof Error ? err.message : String(err), ok: false };
      }
      actionResults.push(actionRow);
    }
    if ((index + 1) % 10 === 0) {
      logProgress(index);
    }

    if (skipForms || !entry.actionId || !entry.model || (maxForms > 0 && formOpened >= maxForms)) continue;
    let recordId = 0;
    try {
      const list = await intent('api.data', {
        op: 'list',
        model: entry.model,
        fields: ['id', 'name'],
        limit: 1,
        order: 'id desc',
        context: {},
      });
      const first = (list.rows || list.records || list.data || [])[0] || {};
      recordId = Number(first.id || 0);
    } catch (err) {
      formResults.push({ ...entry, ok: false, skipped: false, issue: `sample record failed: ${err instanceof Error ? err.message : String(err)}` });
      continue;
    }
    if (!recordId) {
      formResults.push({ ...entry, ok: true, skipped: true, reason: 'no records' });
      continue;
    }
    formOpened += 1;
    currentProbe = `form:${entry.path}`;
    const formRoute = `/r/${encodeURIComponent(entry.model)}/${recordId}?db=${process.env.DB || 'sc_demo'}&action_id=${entry.actionId}${entry.menuId ? `&menu_id=${entry.menuId}` : ''}`;
    let formRow = {
      ...entry,
      recordId,
      route: formRoute,
      ok: false,
      outline: [],
      inputCount: 0,
      issue: '',
      hasErrorText: false,
      hasHorizontalOverflow: false,
      screenshotPath: '',
    };
    try {
      await page.goto(`${base}${formRoute}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await waitForSettledUserSurface(page);
      const text = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
      const outline = await page.locator('.native-business-outline-item').evaluateAll((nodes) => (
        nodes.map((node) => node.textContent?.trim()).filter(Boolean)
      )).catch(() => []);
      const inputCount = await page.locator('input, textarea, select').count().catch(() => 0);
      const hasErrorText = /render error|contract not renderable|页面加载失败|页面异常|系统异常|Traceback|Cannot read/i.test(text);
      const hasLoadingText = /正在加载列表|正在加载|Loading/i.test(text);
      const hasHorizontalOverflow = await page.evaluate(() => (
        document.documentElement.scrollWidth > window.innerWidth + 1 || document.body.scrollWidth > window.innerWidth + 1
      )).catch(() => false);
      let screenshotPath = '';
      if (takeScreenshots) {
        screenshotPath = path.join(artifactRoot, 'forms', `${String(formOpened).padStart(3, '0')}_${slug(entry.path || entry.label)}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
      }
      formRow = { ...formRow, ok: !hasErrorText && !hasLoadingText && !hasHorizontalOverflow, outline, inputCount, hasErrorText, hasLoadingText, hasHorizontalOverflow, screenshotPath };
    } catch (err) {
      formRow = { ...formRow, issue: err instanceof Error ? err.message : String(err), ok: false };
    }
    formResults.push(formRow);
    if ((index + 1) % 10 === 0 || index === entries.length - 1) {
      logProgress(index);
    }
  }

  const summary = writeProgress();
  const report = JSON.parse(fs.readFileSync(outPath, 'utf8'));
  console.log(JSON.stringify({
    summary,
    outPath,
    actionFailures: report.actionFailures.slice(0, 12),
    formFailures: report.formFailures.slice(0, 12),
    formSkipped: report.formSkipped.slice(0, 12),
    consoleErrors: report.consoleErrors.slice(0, 12),
  }, null, 2));
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
