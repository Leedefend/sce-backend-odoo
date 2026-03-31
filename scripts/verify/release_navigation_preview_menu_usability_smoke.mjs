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

const BASE_URL = String(process.env.BASE_URL || 'http://127.0.0.1:5174').replace(/\/+$/, '');
const API_BASE_URL = String(process.env.API_BASE_URL || '').replace(/\/+$/, '');
const API_BASE_CANDIDATES = [
  API_BASE_URL,
  'http://127.0.0.1:18069',
  'http://127.0.0.1:8070',
  'http://127.0.0.1:18081',
].map((item) => String(item || '').replace(/\/+$/, '')).filter(Boolean);
const DB_NAME = String(process.env.DB_NAME || 'sc_demo').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'demo_pm').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'release-navigation-preview-usability-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  status: 'PASS',
  base_url: BASE_URL,
  api_base_url: API_BASE_URL,
  api_base_candidates: API_BASE_CANDIDATES,
  db_name: DB_NAME,
  login: LOGIN,
  preview_menu_count: 0,
  preview_menus: [],
  cases: [],
  console_errors: [],
  page_errors: [],
};

function log(message) {
  console.log(`[release_navigation_preview_menu_usability_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function fetchLoginToken() {
  let payload = null;
  let lastError = null;
  for (const apiBase of API_BASE_CANDIDATES) {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        const response = await fetch(`${apiBase}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Anonymous-Intent': 'true',
          },
          body: JSON.stringify({
            intent: 'login',
            params: {
              login: LOGIN,
              password: PASSWORD,
              contract_mode: 'default',
              db: DB_NAME,
            },
          }),
        });
        payload = {
          status: response.status,
          text: await response.text(),
        };
        if (Number(payload?.status || 0) === 200) {
          const parsed = JSON.parse(String(payload?.text || '{}'));
          const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
          const token = String(data?.session?.token || data?.token || '').trim();
          assert(token, 'login response missing token');
          summary.api_base_url = apiBase;
          return token;
        }
      } catch (error) {
        lastError = error;
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
  }
  if (lastError) {
    throw lastError;
  }
  assert(Number(payload?.status || 0) === 200, `login http status drift: ${payload?.status}`);
  return '';
}

async function bootstrapLogin(page) {
  const token = await fetchLoginToken();
  await page.addInitScript(({ token, dbName }) => {
    sessionStorage.setItem(`sc_auth_token:${dbName}`, token);
    sessionStorage.setItem('sc_auth_token:default', token);
    sessionStorage.setItem('sc_auth_token:test', token);
    sessionStorage.setItem('sc_auth_token', token);
    sessionStorage.setItem('sc_active_db:default', dbName);
    sessionStorage.setItem('sc_active_db:test', dbName);
    localStorage.setItem('sc_active_db:default', dbName);
    localStorage.setItem('sc_active_db:test', dbName);
  }, { token, dbName: DB_NAME });
}

async function waitForSidebar(page) {
  await page.locator('.sidebar').waitFor({ timeout: 20000 });
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1200);
}

function flattenPreviewLeaves(nodes) {
  const out = [];
  const walk = (items) => {
    for (const node of items || []) {
      if (!node || typeof node !== 'object') continue;
      const children = Array.isArray(node.children) ? node.children : [];
      if (children.length) {
        walk(children);
        continue;
      }
      const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
      if (String(meta.release_state || '').trim() !== 'preview') continue;
      const menuId = Number(node.menu_id || node.id || meta.menu_id || 0) || 0;
      if (!menuId) continue;
      out.push({
        key: String(node.key || ''),
        label: String(node.label || node.title || node.name || '').trim(),
        menu_id: menuId,
        scene_key: String(meta.scene_key || '').trim(),
        action_id: Number(meta.action_id || 0) || 0,
        model: String(meta.model || '').trim(),
      });
    }
  };
  walk(nodes);
  return out;
}

async function readPreviewMenus(page) {
  return page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    const roots = Array.isArray(cache?.releaseNavigationTree) ? cache.releaseNavigationTree : [];
    const flatten = [];
    const walk = (items) => {
      for (const node of items || []) {
        if (!node || typeof node !== 'object') continue;
        const children = Array.isArray(node.children) ? node.children : [];
        if (children.length) {
          walk(children);
          continue;
        }
        const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
        if (String(meta.release_state || '').trim() !== 'preview') continue;
        const menuId = Number(node.menu_id || node.id || meta.menu_id || 0) || 0;
        if (!menuId) continue;
        flatten.push({
          key: String(node.key || ''),
          label: String(node.label || node.title || node.name || '').trim(),
          menu_id: menuId,
          scene_key: String(meta.scene_key || '').trim(),
          action_id: Number(meta.action_id || 0) || 0,
          model: String(meta.model || '').trim(),
        });
      }
    };
    walk(roots);
    return flatten;
  });
}

async function verifyMenu(page, menu) {
  const targetUrl = `${BASE_URL}/m/${menu.menu_id}?menu_id=${menu.menu_id}`;
  const caseResult = {
    menu_id: menu.menu_id,
    label: menu.label,
    scene_key: menu.scene_key,
    action_id: menu.action_id,
    model: menu.model,
    target_url: targetUrl,
    status: 'PASS',
    final_url: '',
    error_text: '',
  };
  try {
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1200);
    const errorText = await page.evaluate(() => {
      const selectors = [
        '[data-component="StatusPanel"]',
        '.status-panel',
        '.router-host',
        'body',
      ];
      const text = selectors
        .map((selector) => Array.from(document.querySelectorAll(selector)).map((el) => el.textContent || '').join('\n'))
        .join('\n');
      return text;
    });
    caseResult.final_url = page.url();
    caseResult.error_text = String(errorText || '').slice(0, 1000);
    const normalizedErrorText = caseResult.error_text.toLowerCase();
    const hardFailure = [
      '初始化失败',
      'invalid menu id',
      '菜单无动作',
      'root menu not found',
      'menu resolve failed',
      'menu not found',
      'contract_context_missing',
      'scene_registry_missing',
      'resolve menu failed',
      'contract failed',
      'error:',
      'unhandled',
    ].some((token) => normalizedErrorText.includes(String(token).toLowerCase()));
    if (caseResult.final_url.includes('reason=CONTRACT_CONTEXT_MISSING')
      || caseResult.final_url.includes('diag=scene_registry_missing')) {
      caseResult.status = 'FAIL';
    }
    if (hardFailure) {
      caseResult.status = 'FAIL';
      await page.screenshot({ path: path.join(outDir, `fail-menu-${menu.menu_id}.png`), fullPage: true }).catch(() => {});
    }
  } catch (error) {
    caseResult.status = 'FAIL';
    caseResult.error_text = String(error?.message || error);
    caseResult.final_url = page.url();
    await page.screenshot({ path: path.join(outDir, `fail-menu-${menu.menu_id}.png`), fullPage: true }).catch(() => {});
  }
  return caseResult;
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

  log('bootstrap demo_pm session');
  await bootstrapLogin(page);
  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForSidebar(page);

  const previewMenus = await readPreviewMenus(page);
  summary.preview_menu_count = previewMenus.length;
  summary.preview_menus = previewMenus;
  assert(previewMenus.length > 0, 'preview menu list empty');

  for (const menu of previewMenus) {
    log(`check menu_id=${menu.menu_id} label=${menu.label}`);
    const result = await verifyMenu(page, menu);
    summary.cases.push(result);
  }

  if (summary.cases.some((item) => item.status !== 'PASS')) {
    summary.status = 'FAIL';
    throw new Error(`preview usability failures=${summary.cases.filter((item) => item.status !== 'PASS').length}`);
  }

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Release Navigation Preview Menu Usability Smoke',
      '',
      `- base_url: \`${BASE_URL}\``,
      `- db_name: \`${DB_NAME}\``,
      `- login: \`${LOGIN}\``,
      `- preview_menu_count: \`${summary.preview_menu_count}\``,
      '',
      '## Cases',
      ...summary.cases.map((item) => `- ${item.status} menu_id=${item.menu_id} ${item.label} -> ${item.final_url}`),
    ].join('\n'),
    'utf8',
  );
  log(`PASS artifacts=${outDir}`);
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Release Navigation Preview Menu Usability Smoke',
      '',
      `- status: \`FAIL\``,
      `- error: \`${summary.error}\``,
      `- preview_menu_count: \`${summary.preview_menu_count}\``,
      '',
      '## Cases',
      ...summary.cases.map((item) => `- ${item.status} menu_id=${item.menu_id} ${item.label} -> ${item.final_url}`),
    ].join('\n'),
    'utf8',
  );
  log(`FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) {
    await browser.close();
  }
}
