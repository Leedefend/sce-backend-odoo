import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium } = require(playwrightEntry);

const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');

export function normalizePortalSmokeDbName(rawDbName) {
  const value = String(rawDbName || '').trim();
  if (!value) return 'sc_demo';
  if (value === 'sc-demo') return 'sc_demo';
  return value;
}

export function resolvePortalSmokeConfig(options = {}) {
  return {
    baseUrl: String(options.baseUrl || process.env.BASE_URL || 'http://127.0.0.1:5174').replace(/\/+$/, ''),
    apiBaseUrl: String(options.apiBaseUrl || process.env.API_BASE_URL || '').replace(/\/+$/, ''),
    dbName: normalizePortalSmokeDbName(options.dbName || process.env.DB_NAME || 'sc_demo'),
    login: String(options.login || process.env.E2E_LOGIN || 'wutao').trim(),
    password: String(options.password || process.env.E2E_PASSWORD || 'demo').trim(),
    artifactsDir: String(options.artifactsDir || process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts',
  };
}

export function primeLocalRuntimeLibraries() {
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

export function resolveApiBaseCandidates(rawApiBaseUrl = '') {
  return [
    String(rawApiBaseUrl || '').replace(/\/+$/, ''),
    'http://127.0.0.1:18069',
    'http://localhost:18069',
    'http://127.0.0.1:8069',
    'http://localhost:8069',
  ].filter(Boolean);
}

export async function fetchPortalLoginToken(options) {
  const dbName = String(options?.dbName || '').trim();
  const login = String(options?.login || '').trim();
  const password = String(options?.password || '').trim();
  const apiBaseCandidates = Array.isArray(options?.apiBaseCandidates)
    ? options.apiBaseCandidates.map((item) => String(item || '').replace(/\/+$/, '')).filter(Boolean)
    : [];
  const requestTimeoutMs = Number(options?.requestTimeoutMs || 12000) || 12000;
  const retryCount = Number(options?.retryCount || 5) || 5;
  const retryDelayMs = Number(options?.retryDelayMs || 1200) || 1200;
  const onAttempt = typeof options?.onAttempt === 'function' ? options.onAttempt : null;

  let lastError = null;
  for (const apiBase of apiBaseCandidates) {
    for (let attempt = 0; attempt < retryCount; attempt += 1) {
      onAttempt?.({ apiBase, attempt: attempt + 1, timeoutMs: requestTimeoutMs });
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(new Error(`login token request timeout after ${requestTimeoutMs}ms`)), requestTimeoutMs);
      try {
        const response = await fetch(`${apiBase}/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Anonymous-Intent': 'true',
          },
          signal: controller.signal,
          body: JSON.stringify({
            intent: 'login',
            params: {
              login,
              password,
              contract_mode: 'default',
              db: dbName,
            },
          }),
        });
        let parsed = null;
        try {
          parsed = await response.json();
        } catch {
          parsed = null;
        }
        const errorCode = String(parsed?.error?.code || '').trim();
        const errorMessage = String(parsed?.error?.message || '').trim();
        if (response.status === 401 && errorCode === 'AUTH_REQUIRED') {
          throw new Error(`invalid browser smoke credentials for db=${dbName} login=${login} api=${apiBase}: ${errorMessage || 'AUTH_REQUIRED'}`);
        }
        if (response.status !== 200) {
          lastError = new Error(`login http status drift from ${apiBase}: ${response.status}`);
          continue;
        }
        const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
        const token = String(data?.session?.token || data?.token || '').trim();
        if (token) {
          return { token, apiBase };
        }
        lastError = new Error(`login response missing token from ${apiBase}`);
      } catch (error) {
        lastError = error;
      } finally {
        clearTimeout(timeoutId);
      }
      await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
    }
  }
  throw new Error(`login token fetch failed: ${String(lastError?.message || lastError || 'unknown')}`);
}

export async function installPortalAuthInitScript(page, options) {
  const token = String(options?.token || '').trim();
  const dbName = String(options?.dbName || '').trim();
  const dbScopes = Array.isArray(options?.dbScopes) && options.dbScopes.length
    ? options.dbScopes.map((item) => String(item || '').trim()).filter(Boolean)
    : ['default', 'test', dbName];
  if (!token) {
    throw new Error('portal auth init requires token');
  }
  if (!dbName) {
    throw new Error('portal auth init requires dbName');
  }
  await page.addInitScript(({ token, dbName, dbScopes }) => {
    const scopedTokens = [...new Set(dbScopes.filter(Boolean))];
    const legacyTokenKeys = [];
    for (let index = 0; index < sessionStorage.length; index += 1) {
      const key = sessionStorage.key(index);
      if (key && key.startsWith('sc_auth_token')) {
        legacyTokenKeys.push(key);
      }
    }
    legacyTokenKeys.forEach((key) => sessionStorage.removeItem(key));
    scopedTokens.forEach((scope) => {
      sessionStorage.setItem(`sc_auth_token:${scope}`, token);
      sessionStorage.setItem(`sc_active_db:${scope}`, dbName);
      localStorage.setItem(`sc_active_db:${scope}`, dbName);
    });
    sessionStorage.setItem('sc_auth_token', token);
    const loginUrl = new URL(window.location.href);
    if (loginUrl.searchParams.get('db') !== dbName) {
      loginUrl.searchParams.set('db', dbName);
      window.history.replaceState(null, '', loginUrl.toString());
    }
  }, { token, dbName, dbScopes });
}

export async function bootstrapPortalBrowserAuth(page, options) {
  const apiBaseCandidates = resolveApiBaseCandidates(options?.apiBaseUrl);
  const auth = await fetchPortalLoginToken({
    dbName: options?.dbName,
    login: options?.login,
    password: options?.password,
    apiBaseCandidates,
    requestTimeoutMs: options?.requestTimeoutMs,
    retryCount: options?.retryCount,
    retryDelayMs: options?.retryDelayMs,
    onAttempt: options?.onAttempt,
  });
  await installPortalAuthInitScript(page, {
    token: auth.token,
    dbName: options?.dbName,
    dbScopes: options?.dbScopes,
  });
  return auth;
}

export async function waitForPortalBootstrapReady(page, options = {}) {
  const timeoutMs = Number(options.timeoutMs || 20000) || 20000;
  await page.waitForFunction(() => {
    if (!document.body) return false;
    if (window.location.pathname.startsWith('/login')) return false;
    const tokenPresent = Array.from({ length: sessionStorage.length })
      .map((_, index) => sessionStorage.key(index))
      .filter(Boolean)
      .some((key) => String(key || '').startsWith('sc_auth_token') && String(sessionStorage.getItem(String(key)) || '').trim());
    if (!tokenPresent) return false;
    const statusTitle = document.querySelector('.status-panel .title, .status-panel h2');
    const statusText = String(statusTitle?.textContent || '').trim();
    if (statusText.includes('初始化失败')) return true;
    const routeHost = document.querySelector('.router-host, .sidebar, [data-component="LayoutShell"]');
    return Boolean(routeHost);
  }, {}, { timeout: timeoutMs });
}

export async function launchPortalChromium(options = {}) {
  primeLocalRuntimeLibraries();
  return chromium.launch({
    headless: true,
    timeout: Number(options.timeout || 20000) || 20000,
    args: options.args || ['--no-sandbox', '--disable-setuid-sandbox', '--disable-seccomp-filter-sandbox', '--disable-namespace-sandbox'],
  });
}
