import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

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
const API_BASE_URL = String(process.env.API_BASE_URL || '').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_prod_sim').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'svc_e2e_smoke').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';

const API_BASE_CANDIDATES = [
  API_BASE_URL,
  'http://127.0.0.1:18069',
  'http://localhost:18069',
  'http://127.0.0.1:8069',
  'http://localhost:8069',
].map((item) => String(item || '').replace(/\/+$/, '')).filter(Boolean);

const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'unified-system-menu-click-usability-smoke', ts);
fs.mkdirSync(outDir, { recursive: true });

function log(message) {
  console.log(`[unified_system_menu_click_usability_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function fetchLoginToken() {
  let lastError = null;
  for (const apiBase of API_BASE_CANDIDATES) {
    for (let attempt = 0; attempt < 5; attempt += 1) {
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
        if (response.status !== 200) {
          await new Promise((resolve) => setTimeout(resolve, 1200));
          continue;
        }
        const parsed = await response.json();
        const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
        const token = String(data?.session?.token || data?.token || '').trim();
        if (token) {
          return { token, apiBase };
        }
      } catch (error) {
        lastError = error;
      }
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
  }
  throw new Error(`login token fetch failed: ${String(lastError?.message || lastError || 'unknown')}`);
}

function flattenLeafMenus(nodes) {
  const out = [];
  const walk = (items, ancestors = []) => {
    for (const node of items || []) {
      if (!node || typeof node !== 'object') continue;
      const children = Array.isArray(node.children) ? node.children : [];
      if (children.length) {
        walk(children, [...ancestors, String(node.label || node.title || node.name || node.key || '')]);
        continue;
      }
      const menuId = Number(node.menu_id || node.id || 0) || 0;
      if (!menuId) continue;
      const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
      out.push({
        menu_id: menuId,
        label: String(node.label || node.title || node.name || node.key || `menu_${menuId}`),
        path: [...ancestors, String(node.label || node.title || node.name || node.key || '')].filter(Boolean).join('/'),
        scene_key: String(meta.scene_key || '').trim(),
        route: String(meta.route || '').trim(),
        action_id: Number(meta.action_id || 0) || 0,
        menu_xmlid: String(meta.menu_xmlid || '').trim(),
      });
    }
  };
  walk(nodes, []);
  return out;
}

async function readMenusFromStorage(page) {
  return page.evaluate(() => {
    const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
    const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
    const releaseTree = Array.isArray(cache?.releaseNavigationTree) ? cache.releaseNavigationTree : [];
    const menuTree = Array.isArray(cache?.menuTree) ? cache.menuTree : [];
    return {
      cache_key: cacheKey || '',
      release_tree: releaseTree,
      menu_tree: menuTree,
    };
  });
}

function isFailureText(text) {
  const normalized = String(text || '').toLowerCase();
  const tokens = [
    '页面缺少契约必需上下文',
    'contract context',
    'contract_context_missing',
    'menu resolve failed',
    'resolve menu failed',
    'invalid menu id',
  ];
  return tokens.some((token) => normalized.includes(token.toLowerCase()));
}

async function waitForPageSettled(page, { allowNetworkIdleTimeout = false } = {}) {
  let networkIdleTimedOut = false;
  await page.waitForLoadState('domcontentloaded');
  try {
    await page.waitForLoadState('networkidle', { timeout: 10000 });
  } catch (error) {
    const message = String(error?.message || error || '');
    const isNetworkIdleTimeout =
      (message.includes('waitForLoadState') || message.includes('page.waitForLoadState'))
      && message.includes('Timeout');
    if (!allowNetworkIdleTimeout || !isNetworkIdleTimeout) {
      throw error;
    }
    networkIdleTimedOut = true;
  }
  await page.waitForTimeout(networkIdleTimedOut ? 1200 : 500);
  return { networkIdleTimedOut };
}

async function verifyLeaf(page, leaf) {
  const targetUrl = `${BASE_URL}/m/${leaf.menu_id}?menu_id=${leaf.menu_id}`;
  const result = {
    ...leaf,
    target_url: targetUrl,
    final_url: '',
    status: 'PASS',
    error_text: '',
    networkidle_timeout: false,
  };
  try {
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    const settle = await waitForPageSettled(page, { allowNetworkIdleTimeout: true });
    result.networkidle_timeout = settle.networkIdleTimedOut;
    result.final_url = page.url();
    result.error_text = await page.evaluate(() => {
      const text = Array.from(document.querySelectorAll('body, .status-panel, [data-component="StatusPanel"]'))
        .map((node) => node.textContent || '')
        .join('\n');
      return String(text || '').slice(0, 1200);
    });
    if (
      result.final_url.includes('reason=CONTRACT_CONTEXT_MISSING')
      || result.final_url.includes('diag=legacy_route_missing_action_id')
      || result.final_url.includes('diag=scene_registry_missing')
      || isFailureText(result.error_text)
    ) {
      result.status = 'FAIL';
    }
  } catch (error) {
    result.status = 'FAIL';
    result.error_text = String(error?.message || error);
    result.final_url = page.url();
  }
  return result;
}

const summary = {
  status: 'PASS',
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  api_base_candidates: API_BASE_CANDIDATES,
  used_api_base: '',
  leaf_count: 0,
  fail_count: 0,
  failed_menu_ids: [],
  non_blocking_networkidle_timeouts: 0,
};

let browser;
try {
  log('fetch login token');
  const { token, apiBase } = await fetchLoginToken();
  summary.used_api_base = apiBase;

  browser = await chromium.launch({
    headless: true,
    timeout: 20000,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-seccomp-filter-sandbox', '--disable-namespace-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.addInitScript(({ token, dbName }) => {
    sessionStorage.setItem(`sc_auth_token:${dbName}`, token);
    sessionStorage.setItem('sc_auth_token:default', token);
    sessionStorage.setItem('sc_auth_token:test', token);
    sessionStorage.setItem('sc_auth_token', token);
    sessionStorage.setItem('sc_active_db:default', dbName);
    localStorage.setItem('sc_active_db:default', dbName);
  }, { token, dbName: DB_NAME });

  await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForPageSettled(page, { allowNetworkIdleTimeout: true });
  await page.waitForTimeout(1500);

  const runtime = await readMenusFromStorage(page);
  const sourceTree = runtime.release_tree.length ? runtime.release_tree : runtime.menu_tree;
  const leaves = flattenLeafMenus(sourceTree);
  summary.leaf_count = leaves.length;
  assert(leaves.length > 0, 'no menu leaves discovered from runtime storage');

  const cases = [];
  for (const leaf of leaves) {
    const item = await verifyLeaf(page, leaf);
    cases.push(item);
  }
  writeJson('cases.json', cases);

  const failed = cases.filter((item) => item.status !== 'PASS');
  summary.non_blocking_networkidle_timeouts = cases.filter((item) => item.networkidle_timeout).length;
  summary.fail_count = failed.length;
  summary.failed_menu_ids = failed.map((item) => item.menu_id);
  if (failed.length) {
    summary.status = 'FAIL';
    writeJson('failed_cases.json', failed);
  }
  writeJson('summary.json', summary);

  if (failed.length) {
    throw new Error(`menu click usability failures=${failed.length}`);
  }

  log(`PASS leaf_count=${summary.leaf_count}`);
  log(`artifacts: ${outDir}`);
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  writeJson('summary.json', summary);
  log(`FAIL ${summary.error}`);
  log(`artifacts: ${outDir}`);
  process.exitCode = 1;
} finally {
  if (browser) {
    await browser.close().catch(() => {});
  }
}
