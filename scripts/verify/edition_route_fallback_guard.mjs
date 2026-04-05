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
const API_BASE_URL = String(process.env.API_BASE_URL || 'http://127.0.0.1:18069').replace(/\/+$/, '');
const DB_NAME = String(process.env.DB_NAME || 'sc_prod_sim').trim();
const LOGIN = String(process.env.E2E_FALLBACK_LOGIN || 'demo_finance').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'edition-route-fallback-guard', ts);

function resolvePasswordCandidates() {
  const explicitList = String(process.env.E2E_FALLBACK_PASSWORDS || '').trim();
  if (explicitList) {
    const values = explicitList.split(',').map((item) => item.trim()).filter(Boolean);
    if (values.length) return Array.from(new Set(values));
  }
  const explicitPassword = String(process.env.E2E_FALLBACK_PASSWORD || '').trim();
  if (explicitPassword) return [explicitPassword];
  return ['demo', '123456'];
}

const PASSWORD_CANDIDATES = resolvePasswordCandidates();

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  password_candidates_count: PASSWORD_CANDIDATES.length,
  status: 'PASS',
  console_errors: [],
  page_errors: [],
  intercepted: [],
};

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function fetchLoginToken() {
  const attempts = [];
  for (const password of PASSWORD_CANDIDATES) {
    const response = await fetch(`${API_BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Anonymous-Intent': 'true',
      },
      body: JSON.stringify({
        intent: 'login',
        params: {
          login: LOGIN,
          password,
          contract_mode: 'default',
          db: DB_NAME,
        },
      }),
    });
    const payload = {
      status: Number(response.status || 0),
      text: await response.text(),
    };
    attempts.push(payload.status);
    if (payload.status === 200) {
      const parsed = JSON.parse(String(payload.text || '{}'));
      const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
      const token = String(data?.session?.token || data?.token || '').trim();
      assert(token, 'login response missing token');
      return token;
    }
  }
  if (attempts.length && attempts.every((status) => status === 401)) {
    return null;
  }
  throw new Error(`login token fetch failed: status=${attempts.join(',') || 'unknown'}`);
}

async function bootstrapLogin(page) {
  const token = await fetchLoginToken();
  if (!token) return false;
  await page.addInitScript(({ runtimeToken, dbName }) => {
    sessionStorage.setItem(`sc_auth_token:${dbName}`, runtimeToken);
    sessionStorage.setItem('sc_auth_token:default', runtimeToken);
    sessionStorage.setItem('sc_auth_token:test', runtimeToken);
    sessionStorage.setItem('sc_auth_token', runtimeToken);
    sessionStorage.setItem('sc_active_db:default', dbName);
    sessionStorage.setItem('sc_active_db:test', dbName);
    localStorage.setItem('sc_active_db:default', dbName);
    localStorage.setItem('sc_active_db:test', dbName);
  }, { runtimeToken: token, dbName: DB_NAME });
  return true;
}

async function waitForRequestMatch(requests, predicate, timeoutMs = 20000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const hit = requests.find(predicate);
    if (hit) return hit;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return null;
}

async function waitForSessionSnapshot(page, predicate, timeoutMs = 20000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const snapshot = await page.evaluate(() => {
      const cacheKey = Object.keys(localStorage).find((key) => key.startsWith('sc_frontend_session_v0_4'));
      const cache = cacheKey ? JSON.parse(localStorage.getItem(cacheKey) || 'null') : null;
      return {
        pathname: window.location.pathname,
        search: window.location.search,
        requestedEditionKey: cache?.requestedEditionKey || '',
        effectiveEditionKey: cache?.effectiveEditionKey || '',
        editionRuntimeV1: cache?.editionRuntimeV1 || null,
        deliveryEngineV1: cache?.deliveryEngineV1 || null,
      };
    });
    if (predicate(snapshot)) return snapshot;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return null;
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
  page.on('request', (request) => {
    if (!request.url().includes('/api/v1/intent') || request.method() !== 'POST') return;
    try {
      const body = request.postDataJSON();
      summary.intercepted.push({
        intent: String(body?.intent || ''),
        params: body?.params || {},
      });
    } catch {
      // ignore parse failure
    }
  });

  const loginReady = await bootstrapLogin(page);
  if (!loginReady) {
    summary.status = 'SKIP_ENV';
    summary.skip_reason = 'fallback_lane_credentials_unavailable';
    summary.skip_detail = `all fallback credential candidates returned 401 for login=${LOGIN}`;
    writeJson('summary.json', summary);
    fs.writeFileSync(
      path.join(outDir, 'summary.md'),
      [
        '# Edition Route Fallback Guard',
        '',
        `- status: \`${summary.status}\``,
        `- reason: \`${summary.skip_reason}\``,
        `- detail: \`${summary.skip_detail}\``,
      ].join('\n'),
      'utf8',
    );
    console.log(`[edition_route_fallback_guard] SKIP_ENV ${summary.skip_detail}`);
  } else {
    await page.goto(`${BASE_URL}/my-work?edition=preview&db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
    await page.waitForURL((url) => url.pathname === '/my-work' && url.searchParams.get('edition') === 'preview', { timeout: 30000, waitUntil: 'commit' });

    const previewInit = await waitForRequestMatch(
      summary.intercepted,
      (item) => item.intent === 'system.init' && String(item.params?.edition_key || '').trim() === 'preview',
      30000,
    );
    const fallbackSummary = await waitForRequestMatch(
      summary.intercepted,
      (item) => item.intent === 'my.work.summary' && String(item.params?.edition_key || '').trim() === 'standard',
      30000,
    );
    const fallbackInitStandard = await waitForRequestMatch(
      summary.intercepted,
      (item) => item.intent === 'system.init' && String(item.params?.edition_key || '').trim() === 'standard',
      30000,
    );
    const fallbackSignal = fallbackSummary || fallbackInitStandard;
    summary.fallback_signal_intent = fallbackSummary ? 'my.work.summary' : (fallbackInitStandard ? 'system.init' : '');
    assert(previewInit, 'preview route should request preview system.init');
    assert(fallbackSignal, 'runtime should expose standard-edition fallback signal');

    const snapshot = await waitForSessionSnapshot(
      page,
      (value) =>
        value?.requestedEditionKey === 'preview'
        && value?.effectiveEditionKey === 'standard'
        && value?.editionRuntimeV1?.diagnostics?.fallback_reason === 'EDITION_ACCESS_DENIED'
        && value?.deliveryEngineV1?.product_key === 'construction.standard',
      30000,
    );
    assert(snapshot, 'session fallback runtime context did not stabilize');

    writeJson('session_snapshot.json', snapshot);
    await page.screenshot({ path: path.join(outDir, 'edition-route-fallback.png'), fullPage: true });
    writeJson('summary.json', summary);
    fs.writeFileSync(
      path.join(outDir, 'summary.md'),
      [
        '# Edition Route Fallback Guard',
        '',
        `- login: \`${LOGIN}\``,
        `- route: \`${snapshot.pathname}${snapshot.search}\``,
        `- requested: \`${snapshot.requestedEditionKey}\``,
        `- effective: \`${snapshot.effectiveEditionKey}\``,
        `- fallback_reason: \`${snapshot.editionRuntimeV1?.diagnostics?.fallback_reason || ''}\``,
        `- fallback_signal_intent: \`${summary.fallback_signal_intent || ''}\``,
        '',
        '## Checks',
        '- preview route keeps requested edition as preview',
        '- unauthorized runtime falls back to standard effective edition',
        '- fallback signal exposes `edition_key=standard` via `my.work.summary` or `system.init`',
        '- standard surface stays `construction.standard`',
      ].join('\n'),
      'utf8',
    );
    console.log(`[edition_route_fallback_guard] PASS artifacts=${outDir}`);
  }
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  try {
    if (page) {
      await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
    }
  } catch {
    // ignore screenshot failure
  }
  writeJson('summary.json', summary);
  console.log(`[edition_route_fallback_guard] FAIL ${summary.error}`);
  throw error;
} finally {
  if (browser) await browser.close();
}
