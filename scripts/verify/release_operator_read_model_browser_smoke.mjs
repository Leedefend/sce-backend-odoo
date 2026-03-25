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
const LOGIN = String(process.env.E2E_LOGIN || 'demo_pm').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'release-operator-read-model-browser-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  console_errors: [],
  page_errors: [],
  cases: [],
};

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function recoverFromTransientFailure(page) {
  const retryButton = page.getByRole('button', { name: /Retry|重试/ });
  if (await retryButton.count()) {
    await retryButton.first().click().catch(() => {});
  } else {
    await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
  }
  await page.waitForTimeout(1500);
}

async function waitForReadModelPage(page) {
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      await page.getByRole('heading', { name: '发布控制台' }).waitFor({ timeout: 12000 });
      await page.getByRole('heading', { name: '当前发布状态' }).waitFor({ timeout: 12000 });
      await page.waitForFunction(() => window.__releaseOperatorReadModelVersion === 'release_operator_read_model_v1', { timeout: 12000 });
      return;
    } catch (error) {
      lastError = error;
      await recoverFromTransientFailure(page);
    }
  }
  throw lastError;
}

async function fetchLoginToken(page) {
  let payload = null;
  for (let attempt = 0; attempt < 5; attempt += 1) {
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
          password: PASSWORD,
          contract_mode: 'default',
          db: DB_NAME,
        },
      }),
    });
    payload = { status: response.status, text: await response.text() };
    if (Number(payload?.status || 0) === 200) {
      const parsed = JSON.parse(String(payload?.text || '{}'));
      const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
      const token = String(data?.session?.token || data?.token || '').trim();
      assert(token, 'login response missing token');
      return token;
    }
    await page.waitForTimeout(1500);
  }
  assert(Number(payload?.status || 0) === 200, `login http status drift: ${payload?.status}`);
  return '';
}

async function bootstrapLogin(page) {
  const token = await fetchLoginToken(page);
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

  await bootstrapLogin(page);
  await page.goto(`${BASE_URL}/release/operator?product_key=construction.standard&db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  await waitForReadModelPage(page);

  const snapshot = await page.evaluate(() => {
    return {
      href: window.location.href,
      title: document.title,
      read_model_version: String(window.__releaseOperatorReadModelVersion || ''),
      headings: Array.from(document.querySelectorAll('h1, h2, h3')).map((el) => (el.textContent || '').trim()).filter(Boolean),
    };
  });

  assert(snapshot.read_model_version === 'release_operator_read_model_v1', 'missing release operator read model version');
  assert(snapshot.headings.includes('发布控制台'), 'missing release operator title');
  assert(snapshot.headings.includes('当前发布状态'), 'missing current release state section');
  assert(snapshot.headings.includes('待审批动作'), 'missing pending approval section');
  assert(snapshot.headings.includes('发布历史'), 'missing release history section');

  writeJson('read_model_snapshot.json', snapshot);
  await page.screenshot({ path: path.join(outDir, 'release_operator_read_model.png'), fullPage: true });

  summary.cases.push({
    case_id: 'release_operator_read_model_visible',
    status: 'PASS',
    route: '/release/operator?product_key=construction.standard',
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Release Operator Read Model Browser Smoke',
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
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  try {
    if (page) {
      await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
    }
  } catch {}
  writeJson('summary.json', summary);
  throw error;
} finally {
  if (browser) await browser.close();
}
