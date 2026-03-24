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
const LOGIN = String(process.env.E2E_FALLBACK_LOGIN || 'demo_finance').trim();
const PASSWORD = String(process.env.E2E_FALLBACK_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'edition-route-fallback-guard', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
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

async function fillLoginForm(page) {
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  await page.locator('input[placeholder*="数据库"]').fill(DB_NAME);
}

async function submitLogin(page) {
  await page.locator('button.submit').click();
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 20000, waitUntil: 'commit' });
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

  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  await fillLoginForm(page);
  await submitLogin(page);
  await page.goto(`${BASE_URL}/my-work?edition=preview`, { waitUntil: 'networkidle' });
  await page.waitForURL((url) => url.pathname === '/my-work' && url.searchParams.get('edition') === 'preview', { timeout: 20000 });

  const previewInit = await waitForRequestMatch(
    summary.intercepted,
    (item) => item.intent === 'system.init' && String(item.params?.edition_key || '').trim() === 'preview',
  );
  const fallbackSummary = await waitForRequestMatch(
    summary.intercepted,
    (item) => item.intent === 'my.work.summary' && String(item.params?.edition_key || '').trim() === 'standard',
  );
  assert(previewInit, 'preview route should request preview system.init');
  assert(fallbackSummary, 'subsequent runtime request should fallback to effective standard edition');

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
  assert(snapshot.requestedEditionKey === 'preview', 'requested edition should preserve preview');
  assert(snapshot.effectiveEditionKey === 'standard', 'effective edition should fallback to standard');
  assert(
    snapshot.editionRuntimeV1?.diagnostics?.fallback_reason === 'EDITION_ACCESS_DENIED',
    'fallback reason should be EDITION_ACCESS_DENIED',
  );
  assert(snapshot.deliveryEngineV1?.product_key === 'construction.standard', 'preview fallback must not pollute standard surface');

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
      '',
      '## Checks',
      '- preview route keeps requested edition as preview',
      '- unauthorized runtime falls back to standard effective edition',
      '- subsequent `my.work.summary` uses `edition_key=standard`',
      '- standard surface stays `construction.standard`',
    ].join('\n'),
    'utf8',
  );
  console.log(`[edition_route_fallback_guard] PASS artifacts=${outDir}`);
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
