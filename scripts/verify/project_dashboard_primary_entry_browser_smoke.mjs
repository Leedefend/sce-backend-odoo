import fs from 'node:fs';
import { createRequire } from 'node:module';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

const require = createRequire(import.meta.url);
const playwrightEntry = require.resolve('playwright', { paths: [path.resolve(process.cwd(), 'frontend')] });
const { chromium, request } = require(playwrightEntry);
const LOCAL_RUNTIME_LIB_ROOT = path.resolve(process.cwd(), '.codex-runtime', 'playwright-libs');

function primeLocalRuntimeLibraries() {
  const candidateDirs = [
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'usr', 'lib', 'x86_64-linux-gnu'),
    path.join(LOCAL_RUNTIME_LIB_ROOT, 'lib', 'x86_64-linux-gnu'),
  ].filter((dir) => fs.existsSync(dir));
  if (!candidateDirs.length) return;
  const existing = String(process.env.LD_LIBRARY_PATH || '').trim();
  const segments = existing ? existing.split(':').filter(Boolean) : [];
  const merged = [...segments, ...candidateDirs].filter((item, idx, arr) => item && arr.indexOf(item) === idx);
  process.env.LD_LIBRARY_PATH = merged.join(':');
}

primeLocalRuntimeLibraries();

const BASE_URL = String(process.env.BASE_URL || 'http://localhost:8070').replace(/\/+$/, '');
const INTENT_BASE_URL = String(process.env.INTENT_BASE_URL || 'http://localhost:8070').replace(/\/+$/, '');
let RUNTIME_INTENT_BASE_URL = INTENT_BASE_URL;
const DB_NAME = String(process.env.DB_NAME || 'sc_prod_sim').trim();
const LOGIN = String(process.env.E2E_LOGIN || 'demo_pm').trim();
const PASSWORD = String(process.env.E2E_PASSWORD || 'demo').trim();
const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const FULL_CHROME_PATH = '/home/odoo/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome';
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'project-dashboard-primary-entry-browser-smoke', ts);

fs.mkdirSync(outDir, { recursive: true });

const summary = {
  base_url: BASE_URL,
  db_name: DB_NAME,
  login: LOGIN,
  cases: [],
  console_errors: [],
  http_5xx_resources: [],
  page_errors: [],
};

const stageTrace = [];

function isConnectEpermMessage(message) {
  return String(message || '').toLowerCase().includes('connect eperm');
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function recordStage(stage, payload = {}) {
  stageTrace.push({
    ts: new Date().toISOString(),
    stage,
    ...payload,
  });
  writeJson('stage_trace.json', stageTrace);
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    const message = String(error?.message || error);
    if (error?.name === 'AbortError') {
      throw new Error(`fetch_timeout:${timeoutMs}:${url}`);
    }
    throw new Error(message);
  } finally {
    clearTimeout(timer);
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function buildCustomFrontendOrigins(baseUrl) {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const out = [];
  const push = (origin) => {
    if (origin && typeof origin === 'string' && !out.includes(origin)) out.push(origin);
  };
  const explicitGatewayOrigins = String(process.env.GATEWAY_BASE_URLS || '')
    .split(',')
    .map((item) => item.trim().replace(/\/+$/, ''))
    .filter(Boolean);
  if (explicitGatewayOrigins.length > 0) {
    explicitGatewayOrigins.forEach((origin) => push(origin));
    return out.filter(Boolean);
  }

  const envFallbackOrigins = String(process.env.BASE_URL_FALLBACKS || '')
    .split(',')
    .map((item) => item.trim().replace(/\/+$/, ''))
    .filter(Boolean);
  push(base);
  envFallbackOrigins.forEach((origin) => push(origin));
  if (base.startsWith('http://127.0.0.1:')) {
    push(base.replace('http://127.0.0.1:', 'http://localhost:'));
    push(base.replace(/:\d+$/, ''));
    push(base.replace(/:\d+$/, ':80'));
  }
  if (base.startsWith('http://localhost:')) {
    push(base.replace('http://localhost:', 'http://127.0.0.1:'));
    push(base.replace(/:\d+$/, ''));
    push(base.replace(/:\d+$/, ':80'));
  }
  if (/^http:\/\/127\.0\.0\.1$/.test(base)) push('http://localhost');
  if (/^http:\/\/localhost$/.test(base)) push('http://127.0.0.1');
  return out.filter(Boolean);
}

function fetchHtmlByHttpModule(targetUrl, timeoutMs) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(targetUrl);
    const mod = parsedUrl.protocol === 'https:' ? https : http;
    const req = mod.request(parsedUrl, {
      method: 'GET',
      timeout: timeoutMs,
      headers: {
        Accept: 'text/html,application/xhtml+xml',
      },
    }, (resp) => {
      const chunks = [];
      resp.on('data', (chunk) => chunks.push(chunk));
      resp.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf-8');
        resolve({
          status: Number(resp.statusCode || 0),
          body,
        });
      });
    });
    req.on('timeout', () => req.destroy(new Error('http_module_timeout')));
    req.on('error', (error) => reject(error));
    req.end();
  });
}

async function fetchHtmlByPlaywrightRequest(targetUrl, timeoutMs) {
  const api = await request.newContext({
    ignoreHTTPSErrors: true,
    extraHTTPHeaders: {
      Accept: 'text/html,application/xhtml+xml',
    },
  });
  try {
    const resp = await api.get(targetUrl, {
      timeout: timeoutMs,
      failOnStatusCode: false,
    });
    const body = await resp.text();
    return {
      status: Number(resp.status() || 0),
      body,
    };
  } finally {
    await api.dispose();
  }
}

function probeTcpReachability(hostname, port, timeoutMs = 1500) {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    const socket = net.createConnection({ host: hostname, port });
    let settled = false;
    const finish = (ok, error = '') => {
      if (settled) return;
      settled = true;
      socket.destroy();
      resolve({ ok, error, elapsed_ms: Date.now() - startedAt });
    };
    socket.setTimeout(timeoutMs);
    socket.on('connect', () => finish(true));
    socket.on('timeout', () => finish(false, 'tcp_timeout'));
    socket.on('error', (error) => finish(false, String(error?.message || error)));
  });
}

async function runConnectivityDiagnostics(baseUrl, dbName) {
  const origins = buildCustomFrontendOrigins(baseUrl);
  const checks = [];
  let tcpReachable = false;
  let hasTcpPermissionBlocked = false;
  for (const origin of origins) {
    const parsed = new URL(origin);
    const hostname = parsed.hostname;
    const port = Number(parsed.port || (parsed.protocol === 'https:' ? 443 : 80));
    const tcp = await probeTcpReachability(hostname, port, 1500);
    checks.push({
      origin,
      transport: 'tcp',
      hostname,
      port,
      ok: tcp.ok,
      elapsed_ms: tcp.elapsed_ms,
      error: tcp.error || '',
    });
    if (!tcp.ok && String(tcp.error || '').toLowerCase().includes('eperm')) {
      hasTcpPermissionBlocked = true;
    }
    if (tcp.ok) {
      tcpReachable = true;
      const loginUrl = `${origin}/web/login?db=${encodeURIComponent(dbName)}`;
      const httpDiagStartedAt = Date.now();
      try {
        const resp = await fetchHtmlByHttpModule(loginUrl, 4000);
        checks.push({
          origin,
          transport: 'http_module_diag',
          url: loginUrl,
          status: resp.status,
          ok: resp.status >= 200 && resp.status < 500,
          elapsed_ms: Date.now() - httpDiagStartedAt,
          error: '',
        });
      } catch (error) {
        checks.push({
          origin,
          transport: 'http_module_diag',
          url: loginUrl,
          ok: false,
          error: String(error?.message || error),
          elapsed_ms: Date.now() - httpDiagStartedAt,
        });
      }
    }
  }
  return {
    ok: tcpReachable || hasTcpPermissionBlocked,
    checks,
    last_error: tcpReachable ? '' : (hasTcpPermissionBlocked ? 'tcp_permission_blocked' : 'no_tcp_reachability'),
    degraded: !tcpReachable && hasTcpPermissionBlocked,
  };
}

function orderOriginsByDiagnostics(origins, diagnostics = null) {
  if (!diagnostics || !Array.isArray(diagnostics.checks)) return origins;
  const scoreByOrigin = new Map();
  for (const origin of origins) scoreByOrigin.set(origin, 0);
  for (const check of diagnostics.checks) {
    const origin = String(check?.origin || '').trim();
    if (!scoreByOrigin.has(origin)) continue;
    const transport = String(check?.transport || '');
    const ok = Boolean(check?.ok);
    const baseScore = Number(scoreByOrigin.get(origin) || 0);
    if (transport === 'tcp') {
      scoreByOrigin.set(origin, baseScore + (ok ? 50 : -20));
      continue;
    }
    if (transport === 'http_module_diag') {
      scoreByOrigin.set(origin, baseScore + (ok ? 30 : -10));
    }
  }
  return [...origins].sort((left, right) => {
    const rightScore = Number(scoreByOrigin.get(right) || 0);
    const leftScore = Number(scoreByOrigin.get(left) || 0);
    return rightScore - leftScore;
  });
}

async function probeCustomFrontendEntryReachability(baseUrl, dbName, diagnostics = null) {
  const origins = orderOriginsByDiagnostics(buildCustomFrontendOrigins(baseUrl), diagnostics);
  const checks = [];
  let lastError = '';
  const loginPaths = ['/web/login', '/login'];
  const probeTimeoutMsByAttempt = [6000, 12000];
  const originHandshakeFailureCounts = new Map();
  const isAbortLikeFetchError = (error) => {
    const message = String(error?.message || error || '').toLowerCase();
    return error?.name === 'AbortError' || message.includes('aborted') || message.includes('timeout');
  };
  const isFallbackEligibleError = (error) => {
    const message = String(error?.message || error || '').toLowerCase();
    return isAbortLikeFetchError(error) || message.includes('fetch failed');
  };
  const isConnectEpermError = (errorOrMessage) => {
    const message = String(errorOrMessage?.message || errorOrMessage || '').toLowerCase();
    return message.includes('connect eperm');
  };
  const isHandshakeFailureMessage = (message) => {
    const text = String(message || '').toLowerCase();
    return (
      text.includes('socket hang up')
      || text.includes('timeout')
      || text.includes('timed out')
      || text.includes('aborted')
      || text.includes('fetch failed')
      || text.includes('http_module_timeout')
      || text.includes('apirequestcontext.get')
    );
  };
  for (const origin of origins) {
    const handshakeFailures = Number(originHandshakeFailureCounts.get(origin) || 0);
    if (handshakeFailures >= 4) {
      checks.push({
        origin,
        transport: 'origin_short_circuit',
        ok: false,
        error: 'repeated_handshake_failure',
      });
      continue;
    }
    for (const loginPath of loginPaths) {
      const target = `${origin}${loginPath}?db=${encodeURIComponent(dbName)}`;
      for (let attempt = 1; attempt <= probeTimeoutMsByAttempt.length; attempt += 1) {
        const startedAt = Date.now();
        const timeoutMs = probeTimeoutMsByAttempt[attempt - 1];
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
          const resp = await fetch(target, { method: 'GET', signal: controller.signal, redirect: 'follow' });
          const html = await resp.text();
          const elapsedMs = Date.now() - startedAt;
          const normalized = String(html || '').toLowerCase();
          const has404Signature = normalized.includes("we couldn't find the page you're looking for");
          const hasLoginFieldSignature =
            normalized.includes('autocomplete="username"')
            || normalized.includes('name="login"')
            || normalized.includes('autocomplete="current-password"')
            || normalized.includes('type="password"');
          const hasSpaShellSignature =
            normalized.includes('<div id="app"></div>')
            || (normalized.includes('/assets/index-') && normalized.includes('<title>智能施工企业管理平台</title>'));
          const ok = resp.status >= 200 && resp.status < 400 && (hasLoginFieldSignature || hasSpaShellSignature) && !has404Signature;
          checks.push({
            url: target,
            attempt,
            timeout_ms: timeoutMs,
            status: resp.status,
            ok,
            elapsed_ms: elapsedMs,
            has_login_signature: hasLoginFieldSignature,
            has_404_signature: has404Signature,
          });
          if (ok) {
            return { ok: true, base_url: origin, login_url: target, checks };
          }
          lastError = has404Signature
            ? 'custom_login_route_missing'
            : `custom_login_contract_invalid: status=${resp.status}`;
          break;
        } catch (error) {
          const elapsedMs = Date.now() - startedAt;
          const message = String(error?.message || error);
          lastError = message;
          checks.push({
            url: target,
            attempt,
            timeout_ms: timeoutMs,
            ok: false,
            error: message,
            elapsed_ms: elapsedMs,
          });
          if (isConnectEpermError(message)) {
            checks.push({
              url: target,
              attempt,
              timeout_ms: timeoutMs,
              transport: 'eperm_fast_path',
              ok: false,
              error: 'connect_eperm_short_circuit',
            });
            const current = Number(originHandshakeFailureCounts.get(origin) || 0);
            originHandshakeFailureCounts.set(origin, current + 4);
            break;
          }
          if (isFallbackEligibleError(error)) {
            try {
              const fallbackStartedAt = Date.now();
              const fallbackResp = await fetchHtmlByHttpModule(target, timeoutMs);
              const fallbackElapsedMs = Date.now() - fallbackStartedAt;
              const normalized = String(fallbackResp.body || '').toLowerCase();
              const has404Signature = normalized.includes("we couldn't find the page you're looking for");
              const hasLoginFieldSignature =
                normalized.includes('autocomplete="username"')
                || normalized.includes('name="login"')
                || normalized.includes('autocomplete="current-password"')
                || normalized.includes('type="password"');
              const hasSpaShellSignature =
                normalized.includes('<div id="app"></div>')
                || (normalized.includes('/assets/index-') && normalized.includes('<title>智能施工企业管理平台</title>'));
              const ok = fallbackResp.status >= 200 && fallbackResp.status < 400 && (hasLoginFieldSignature || hasSpaShellSignature) && !has404Signature;
              checks.push({
                url: target,
                attempt,
                timeout_ms: timeoutMs,
                transport: 'http_module_fallback',
                status: fallbackResp.status,
                ok,
                elapsed_ms: fallbackElapsedMs,
                has_login_signature: hasLoginFieldSignature,
                has_404_signature: has404Signature,
              });
              if (ok) {
                return { ok: true, base_url: origin, login_url: target, checks };
              }
              lastError = has404Signature
                ? 'custom_login_route_missing'
                : `custom_login_contract_invalid: status=${fallbackResp.status}`;
            } catch (fallbackError) {
              const fallbackElapsedMs = Date.now() - startedAt;
              const fallbackMessage = String(fallbackError?.message || fallbackError);
              lastError = fallbackMessage;
              checks.push({
                url: target,
                attempt,
                timeout_ms: timeoutMs,
                transport: 'http_module_fallback',
                ok: false,
                error: fallbackMessage,
                elapsed_ms: fallbackElapsedMs,
              });
              if (isConnectEpermError(fallbackMessage)) {
                checks.push({
                  url: target,
                  attempt,
                  timeout_ms: timeoutMs,
                  transport: 'eperm_fast_path',
                  ok: false,
                  error: 'connect_eperm_short_circuit',
                });
                const current = Number(originHandshakeFailureCounts.get(origin) || 0);
                originHandshakeFailureCounts.set(origin, current + 4);
                break;
              }
              try {
                const pwStartedAt = Date.now();
                const pwResp = await fetchHtmlByPlaywrightRequest(target, timeoutMs);
                const pwElapsedMs = Date.now() - pwStartedAt;
                const normalized = String(pwResp.body || '').toLowerCase();
                const has404Signature = normalized.includes("we couldn't find the page you're looking for");
                const hasLoginFieldSignature =
                  normalized.includes('autocomplete="username"')
                  || normalized.includes('name="login"')
                  || normalized.includes('autocomplete="current-password"')
                  || normalized.includes('type="password"');
                const hasSpaShellSignature =
                  normalized.includes('<div id="app"></div>')
                  || (normalized.includes('/assets/index-') && normalized.includes('<title>智能施工企业管理平台</title>'));
                const ok = pwResp.status >= 200 && pwResp.status < 400 && (hasLoginFieldSignature || hasSpaShellSignature) && !has404Signature;
                checks.push({
                  url: target,
                  attempt,
                  timeout_ms: timeoutMs,
                  transport: 'playwright_api_request_fallback',
                  status: pwResp.status,
                  ok,
                  elapsed_ms: pwElapsedMs,
                  has_login_signature: hasLoginFieldSignature,
                  has_404_signature: has404Signature,
                });
                if (ok) {
                  return { ok: true, base_url: origin, login_url: target, checks };
                }
                lastError = has404Signature
                  ? 'custom_login_route_missing'
                  : `custom_login_contract_invalid: status=${pwResp.status}`;
              } catch (pwError) {
                const pwElapsedMs = Date.now() - startedAt;
                const pwMessage = String(pwError?.message || pwError);
                lastError = pwMessage;
                checks.push({
                  url: target,
                  attempt,
                  timeout_ms: timeoutMs,
                  transport: 'playwright_api_request_fallback',
                  ok: false,
                  error: pwMessage,
                  elapsed_ms: pwElapsedMs,
                });
                if (isConnectEpermError(pwMessage)) {
                  checks.push({
                    url: target,
                    attempt,
                    timeout_ms: timeoutMs,
                    transport: 'eperm_fast_path',
                    ok: false,
                    error: 'connect_eperm_short_circuit',
                  });
                  const current = Number(originHandshakeFailureCounts.get(origin) || 0);
                  originHandshakeFailureCounts.set(origin, current + 4);
                  break;
                }
                if (isHandshakeFailureMessage(pwMessage)) {
                  const current = Number(originHandshakeFailureCounts.get(origin) || 0);
                  originHandshakeFailureCounts.set(origin, current + 1);
                }
              }
            }
          }
          if (isHandshakeFailureMessage(lastError)) {
            const current = Number(originHandshakeFailureCounts.get(origin) || 0);
            originHandshakeFailureCounts.set(origin, current + 1);
          }
          const retriableAbort = isAbortLikeFetchError(error) && attempt < probeTimeoutMsByAttempt.length;
          if (!retriableAbort) break;
        } finally {
          clearTimeout(timer);
        }
      }
      if (Number(originHandshakeFailureCounts.get(origin) || 0) >= 4) {
        checks.push({
          origin,
          url: target,
          transport: 'origin_short_circuit',
          ok: false,
          error: 'repeated_handshake_failure',
        });
        break;
      }
    }
  }
  return { ok: false, base_url: '', checks, last_error: lastError || 'unreachable' };
}

async function fetchLoginTokenByApi() {
  const intentUrl = `${RUNTIME_INTENT_BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  recordStage('login_intent:start', { intentUrl });
  const errors = [];
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const loginResp = await fetchWithTimeout(intentUrl, {
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
            db: DB_NAME,
            contract_mode: 'default',
          },
        }),
      }, 12000);
      if (!loginResp.ok) throw new Error(`login intent failed: ${loginResp.status}`);
      const loginPayload = JSON.parse(await loginResp.text());
      const token = String(loginPayload?.data?.session?.token || loginPayload?.data?.token || '').trim();
      if (!token) throw new Error('login intent missing token');
      recordStage('login_intent:done', { attempt });
      return token;
    } catch (error) {
      const message = String(error?.message || error);
      errors.push({ attempt, error: message });
      recordStage('login_intent:retry', { attempt, error: message });
      if (attempt >= 3) break;
      await sleep(500 * attempt);
    }
  }
  writeJson('login_intent_errors.json', errors);
  throw new Error(`login intent token recovery failed after ${errors.length} tries`);
}

async function bootstrapLoginToken(page, token) {
  await page.addInitScript(({ runtimeToken, dbName }) => {
    const tokenScopes = new Set([
      dbName,
      'default',
      'test',
      'sc_demo',
      'sc_prod_sim',
      'sc_p2',
      'sc_p3',
    ]);
    for (const scope of tokenScopes) {
      if (!scope) continue;
      sessionStorage.setItem(`sc_auth_token:${scope}`, runtimeToken);
    }
    sessionStorage.setItem('sc_auth_token', runtimeToken);
    const dbScopes = new Set([dbName, 'default', 'test']);
    for (const scope of dbScopes) {
      if (!scope) continue;
      sessionStorage.setItem(`sc_active_db:${scope}`, dbName);
      localStorage.setItem(`sc_active_db:${scope}`, dbName);
    }
  }, { runtimeToken: token, dbName: DB_NAME });
}

async function persistLoginToken(page, token) {
  const runtimeToken = String(token || '').trim();
  if (!runtimeToken) return;
  await bootstrapLoginToken(page, runtimeToken);
  await page.evaluate(({ injectedToken, dbName }) => {
    const tokenScopes = new Set([
      dbName,
      'default',
      'test',
      'sc_demo',
      'sc_prod_sim',
      'sc_p2',
      'sc_p3',
    ]);
    for (const scope of tokenScopes) {
      if (!scope) continue;
      sessionStorage.setItem(`sc_auth_token:${scope}`, injectedToken);
    }
    sessionStorage.setItem('sc_auth_token', injectedToken);
    const dbScopes = new Set([dbName, 'default', 'test']);
    for (const scope of dbScopes) {
      if (!scope) continue;
      sessionStorage.setItem(`sc_active_db:${scope}`, dbName);
      localStorage.setItem(`sc_active_db:${scope}`, dbName);
    }
  }, { injectedToken: runtimeToken, dbName: DB_NAME });
}

async function resolveProjectEntryRouteByApi(token) {
  const runtimeToken = String(token || '').trim() || await fetchLoginTokenByApi();
  const intentUrl = `${RUNTIME_INTENT_BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  const entryResp = await fetchWithTimeout(intentUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${runtimeToken}`,
    },
    body: JSON.stringify({
      intent: 'project.entry.context.resolve',
      params: {},
    }),
  }, 12000);
  if (!entryResp.ok) throw new Error(`project.entry.context.resolve failed: ${entryResp.status}`);
  const entryPayload = JSON.parse(await entryResp.text());
  const route = String(entryPayload?.data?.route || '').trim();
  if (!route.startsWith('/')) throw new Error('invalid backend entry route');
  const projectId = Number(entryPayload?.data?.project_context?.project_id || 0);
  let sceneKey = '';
  if (Number.isFinite(projectId) && projectId > 0) {
    const dashboardResp = await fetchWithTimeout(intentUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${runtimeToken}`,
      },
      body: JSON.stringify({
        intent: 'project.dashboard.enter',
        params: { project_id: projectId },
      }),
    }, 12000);
    if (dashboardResp.ok) {
      const dashboardPayload = JSON.parse(await dashboardResp.text());
      sceneKey = String(dashboardPayload?.data?.scene_key || '').trim();
    }
  }
  return {
    route,
    scene_key: sceneKey,
    project_context: entryPayload?.data?.project_context || null,
  };
}

function shouldUseFullChromeFallback(errorMessage) {
  const text = String(errorMessage || '');
  return text.includes('error while loading shared libraries');
}

function buildLoginUrlCandidates(baseUrl, dbName) {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const encodedDb = encodeURIComponent(dbName);
  const out = new Set();
  const push = (url) => {
    if (url && typeof url === 'string') out.add(url);
  };

  if (/^http:\/\/(127\.0\.0\.1|localhost)$/.test(base)) {
    push(`http://localhost:8070/web/login?db=${encodedDb}`);
    push(`http://127.0.0.1:8070/web/login?db=${encodedDb}`);
    push(`http://localhost:8070/login?db=${encodedDb}`);
    push(`http://127.0.0.1:8070/login?db=${encodedDb}`);
  }
  push(`${base}/web/login?db=${encodedDb}`);
  push(`${base}/login?db=${encodedDb}`);
  if (base.startsWith('http://127.0.0.1')) {
    push(`${base.replace('http://127.0.0.1', 'http://localhost')}/login?db=${encodedDb}`);
    push(`${base.replace('http://127.0.0.1', 'http://localhost')}/web/login?db=${encodedDb}`);
  }
  if (base.startsWith('http://localhost')) {
    push(`${base.replace('http://localhost', 'http://127.0.0.1')}/login?db=${encodedDb}`);
    push(`${base.replace('http://localhost', 'http://127.0.0.1')}/web/login?db=${encodedDb}`);
  }
  return Array.from(out);
}

function buildRootUrlCandidates(baseUrl, dbName, sceneKey = '') {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const encodedDb = encodeURIComponent(dbName);
  const encodedScene = sceneKey ? `&scene_key=${encodeURIComponent(sceneKey)}` : '';
  const out = new Set();
  const push = (url) => {
    if (url && typeof url === 'string') out.add(url);
  };
  if (/^http:\/\/(127\.0\.0\.1|localhost)$/.test(base)) {
    push(`http://localhost:8070/?db=${encodedDb}${encodedScene}`);
    push(`http://127.0.0.1:8070/?db=${encodedDb}${encodedScene}`);
  }
  push(`${base}/?db=${encodedDb}${encodedScene}`);
  if (base.startsWith('http://127.0.0.1')) {
    push(`${base.replace('http://127.0.0.1', 'http://localhost')}/?db=${encodedDb}${encodedScene}`);
  }
  if (base.startsWith('http://localhost')) {
    push(`${base.replace('http://localhost', 'http://127.0.0.1')}/?db=${encodedDb}${encodedScene}`);
  }
  return Array.from(out);
}

async function gotoRootWithRecovery(page, sceneKey = '') {
  const candidates = buildRootUrlCandidates(BASE_URL, DB_NAME, sceneKey);
  const errors = [];
  for (const candidate of candidates) {
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await page.goto(candidate, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await page.waitForLoadState('domcontentloaded');
        return candidate;
      } catch (error) {
        errors.push({
          url: candidate,
          attempt,
          message: String(error?.message || error),
        });
        if (!isRetriableNavigationError(error) || attempt >= 3) break;
        await sleep(1000 * attempt);
      }
    }
  }
  writeJson('root_navigation_errors.json', errors);
  throw new Error(`root navigation failed after recovery attempts (${errors.length} tries)`);
}

function isRetriableNavigationError(error) {
  const message = String(error?.message || error || '');
  return (
    message.includes('ERR_NETWORK_CHANGED') ||
    message.includes('ERR_CONNECTION_RESET') ||
    message.includes('ERR_CONNECTION_REFUSED') ||
    message.includes('ERR_CONNECTION_CLOSED') ||
    message.includes('net::ERR_ABORTED') ||
    message.includes('Timeout')
  );
}

async function gotoLoginWithRecovery(page) {
  const candidates = buildLoginUrlCandidates(BASE_URL, DB_NAME);
  const errors = [];
  for (const candidate of candidates) {
    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try {
        await page.goto(candidate, { waitUntil: 'domcontentloaded', timeout: 12000 });
        await page.waitForLoadState('domcontentloaded');
        if (!(await isLoginSurfaceReady(page))) {
          throw new Error(`login form not found on page: ${candidate}`);
        }
        return candidate;
      } catch (error) {
        errors.push({
          url: candidate,
          attempt,
          message: String(error?.message || error),
        });
        if (!isRetriableNavigationError(error) || attempt >= 3) break;
        await sleep(1000 * attempt);
      }
    }
  }
  writeJson('login_navigation_errors.json', errors);
  throw new Error(`login navigation failed after recovery attempts (${errors.length} tries)`);
}

async function pickVisibleLocator(page, selectors, timeout = 1500) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      await locator.waitFor({ timeout });
      return locator;
    } catch {}
  }
  return null;
}

async function isLoginSurfaceReady(page) {
  const userField = await pickVisibleLocator(page, ['input[autocomplete="username"]', 'input[name="login"]', 'input[type="email"]']);
  const passwordField = await pickVisibleLocator(page, ['input[autocomplete="current-password"]', 'input[name="password"]', 'input[type="password"]']);
  return Boolean(userField && passwordField);
}

async function fillLoginForm(page) {
  const userField = await pickVisibleLocator(page, ['input[autocomplete="username"]', 'input[name="login"]', 'input[type="email"]'], 20000);
  const passwordField = await pickVisibleLocator(page, ['input[autocomplete="current-password"]', 'input[name="password"]', 'input[type="password"]'], 20000);
  assert(Boolean(userField), 'login form missing username field');
  assert(Boolean(passwordField), 'login form missing password field');
  await userField.fill(LOGIN);
  await passwordField.fill(PASSWORD);
  const dbField = await pickVisibleLocator(
    page,
    ['input[placeholder*="数据库"]', 'input[name="db"]', 'input[placeholder*="Database"]', 'input[name="database"]'],
    2000,
  );
  if (dbField) {
    await dbField.fill(DB_NAME);
  }
}

async function collectLoginSnapshot(page) {
  return await page.evaluate(() => {
    const text = document.body?.innerText || '';
    const visibleText = text.replace(/\s+/g, ' ').trim();
    const loginErrorCandidates = [
      '.alert',
      '.alert-danger',
      '.o_login_error_message',
      '.oe_login_form .text-danger',
      '.invalid-feedback',
      '.error',
      '[role="alert"]',
    ];
    const loginErrors = Array.from(document.querySelectorAll(loginErrorCandidates.join(',')))
      .map((node) => (node.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean)
      .slice(0, 10);
    return {
      url: window.location.href,
      has_login_user: Boolean(document.querySelector('input[autocomplete="username"], input[name="login"], input[type="email"]')),
      has_login_password: Boolean(document.querySelector('input[autocomplete="current-password"], input[name="password"], input[type="password"]')),
      has_token: Boolean(sessionStorage.getItem('sc_auth_token')),
      login_errors: loginErrors,
      visible_text_excerpt: visibleText.slice(0, 800),
    };
  });
}

async function submitLogin(page) {
  const beforeSubmit = await collectLoginSnapshot(page);
  recordStage('login_submit:before', beforeSubmit);
  const submitButton = await pickVisibleLocator(
    page,
    [
      'button.submit',
      'button[type="submit"]',
      'button.btn-primary[type="submit"]',
      'form button.btn-primary',
      'form button:has-text("Log in")',
      'form button:has-text("Sign in")',
      'form button:has-text("登录")',
    ],
    5000,
  );
  let submitMethod = 'keyboard_enter';
  if (submitButton) {
    submitMethod = 'button_click';
    await submitButton.click();
  } else {
    await page.keyboard.press('Enter');
  }
  recordStage('login_submit:triggered', { method: submitMethod, url: page.url() });
  try {
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 12000, waitUntil: 'commit' });
    const afterUrlChange = await collectLoginSnapshot(page);
    writeJson('login_submit_result.json', {
      outcome: 'url_changed',
      method: submitMethod,
      before: beforeSubmit,
      after: afterUrlChange,
    });
    recordStage('login_submit:url_changed', afterUrlChange);
    return;
  } catch {}
  try {
    await page.waitForFunction(() => {
      const hasLoginUser = Boolean(document.querySelector('input[autocomplete="username"], input[name="login"], input[type="email"]'));
      const hasLoginPassword = Boolean(document.querySelector('input[autocomplete="current-password"], input[name="password"], input[type="password"]'));
      const hasLoginSurface = hasLoginUser && hasLoginPassword;
      const hasToken = Boolean(sessionStorage.getItem('sc_auth_token'));
      const errorText = (document.body?.innerText || '').toLowerCase();
      const hasLoginError =
        errorText.includes('wrong login/password') ||
        errorText.includes('incorrect login/password') ||
        errorText.includes('invalid login') ||
        errorText.includes('用户名或密码') ||
        errorText.includes('账号或密码') ||
        errorText.includes('登录失败');
      return !hasLoginSurface || hasToken || hasLoginError;
    }, null, { timeout: 12000 });
    const afterSurfaceChange = await collectLoginSnapshot(page);
    writeJson('login_submit_result.json', {
      outcome: 'surface_changed',
      method: submitMethod,
      before: beforeSubmit,
      after: afterSurfaceChange,
    });
    recordStage('login_submit:surface_changed', afterSurfaceChange);
  } catch (error) {
    const timeoutState = await collectLoginSnapshot(page);
    writeJson('login_submit_result.json', {
      outcome: 'timeout',
      method: submitMethod,
      error: String(error?.message || error),
      before: beforeSubmit,
      after: timeoutState,
    });
    recordStage('login_submit:timeout', { ...timeoutState, error: String(error?.message || error) });
    throw error;
  }
}

async function ensureProjectDashboardSurface(page) {
  const current = new URL(page.url());
  const origin = `${current.protocol}//${current.host}`;
  const candidates = [
    `${origin}/?db=${encodeURIComponent(DB_NAME)}`,
    `${origin}/web?db=${encodeURIComponent(DB_NAME)}`,
  ];
  const errors = [];
  for (const candidate of candidates) {
    try {
      await page.goto(candidate, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
      return candidate;
    } catch (error) {
      errors.push({ url: candidate, message: String(error?.message || error) });
    }
  }
  writeJson('project_route_navigation_errors.json', errors);
  throw new Error('failed to open project dashboard surface after login');
}

function buildSemanticEntryUrlCandidates(baseUrl, dbName, backendEntry = null) {
  const base = String(baseUrl || '').replace(/\/+$/, '');
  const encodedDb = encodeURIComponent(dbName);
  const out = new Set();
  const push = (url) => {
    if (url && typeof url === 'string') out.add(url);
  };
  const baseOrigins = [];
  const pushOrigin = (origin) => {
    if (origin && typeof origin === 'string' && !baseOrigins.includes(origin)) {
      baseOrigins.push(origin);
    }
  };
  const isBareLocalhost = /^http:\/\/(127\.0\.0\.1|localhost)$/.test(base);
  pushOrigin(base);
  if (base.startsWith('http://127.0.0.1:')) {
    pushOrigin(base.replace('http://127.0.0.1:', 'http://localhost:'));
  }
  if (base.startsWith('http://localhost:')) {
    pushOrigin(base.replace('http://localhost:', 'http://127.0.0.1:'));
  }
  if (isBareLocalhost) {
    pushOrigin(base.replace('http://127.0.0.1', 'http://localhost'));
    pushOrigin(base.replace('http://localhost', 'http://127.0.0.1'));
  }
  const route = String(backendEntry?.route || '').trim();
  const sceneKey = String(backendEntry?.scene_key || '').trim();
  const routeHasQuery = route.includes('?');

  for (const origin of baseOrigins) {
    if (route.startsWith('/')) {
      push(`${origin}${route}${routeHasQuery ? '&' : '?'}db=${encodedDb}`);
      if (sceneKey) {
        push(`${origin}${route}${routeHasQuery ? '&' : '?'}db=${encodedDb}&scene_key=${encodeURIComponent(sceneKey)}`);
      }
    }
    if (sceneKey) {
      push(`${origin}/s/${encodeURIComponent(sceneKey)}?db=${encodedDb}`);
      push(`${origin}/?db=${encodedDb}&scene_key=${encodeURIComponent(sceneKey)}`);
    }
    push(`${origin}/?db=${encodedDb}`);
  }
  return Array.from(out);
}

function isLoginLikeUrl(rawUrl) {
  const text = String(rawUrl || '').trim();
  if (!text) return false;
  try {
    const parsed = new URL(text);
    return parsed.pathname.includes('/login');
  } catch {
    return text.includes('/login');
  }
}

async function gotoSemanticEntryWithRecovery(page, backendEntry = null, options = {}) {
  const candidates = buildSemanticEntryUrlCandidates(summary.effective_base_url || BASE_URL, DB_NAME, backendEntry);
  const bootstrapUrl = String(options.bootstrapUrl || '').trim();
  if (!backendEntry?.route && !backendEntry?.scene_key && bootstrapUrl) {
    candidates.unshift(bootstrapUrl);
  }
  const errors = [];
  for (const candidate of candidates) {
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await page.goto(candidate, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await page.waitForLoadState('domcontentloaded');
        return candidate;
      } catch (error) {
        const message = String(error?.message || error);
        if (message.includes('interrupted by another navigation')) {
          await page.waitForLoadState('domcontentloaded').catch(() => {});
          return page.url();
        }
        errors.push({
          url: candidate,
          attempt,
          message,
        });
        if (!isRetriableNavigationError(error) || attempt >= 3) break;
        await sleep(1000 * attempt);
      }
    }
  }
  writeJson('semantic_entry_navigation_errors.json', errors);
  throw new Error(`semantic entry navigation failed after recovery attempts (${errors.length} tries)`);
}

async function detectDashboardProfile(page, timeoutMs = 8000) {
  const profile = await page.waitForFunction(() => {
    const text = document.body?.innerText || '';
    if (text.includes("We couldn't find the page you're looking for!")) return 'not_found';
    const oldProfile = text.includes('项目驾驶舱') && text.includes('下一步动作');
    const hasMetrics = text.includes('项目总数') || text.includes('项目阶段');
    const hasProjectCardToken = /FR-\d+[A-Z0-9-]*/i.test(text);
    const hasPagingToken = /\b\d+\s*-\s*\d+\s*\/\s*\d+\b/.test(text);
    const hasProjectDetailToken = /FR-\d+/i.test(text) && (text.includes('Owner') || text.includes('负责人'));
    const newProfile = text.includes('项目管理') && (hasMetrics || hasProjectCardToken || hasPagingToken);
    const detailProfile = hasProjectCardToken || hasProjectDetailToken;
    if (detailProfile) return 'new';
    if (oldProfile) return 'old';
    if (newProfile) return 'new';
    return null;
  }, null, { timeout: timeoutMs });
  return await profile.jsonValue();
}

async function collectDashboardTimeoutSnapshot(page) {
  return await page.evaluate(() => {
    const text = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      pathname: window.location.pathname || '',
      title: document.title || '',
      has_native_navbar: Boolean(document.querySelector('.o_main_navbar')),
      has_discuss_token: Boolean(document.querySelector('.o-mail-Discuss')),
      has_scene_eyebrow: Boolean(document.querySelector('.eyebrow')),
      has_status_panel: Boolean(document.querySelector('[data-component="StatusPanel"], .status-panel')),
      has_menu_tree: Boolean(document.querySelector('[data-component="SidebarNav"], .menu, .nav-shell')),
      visible_text_excerpt: text.slice(0, 1600),
    };
  });
}

async function tryNavigateDashboardViaUi(page) {
  const candidateSelectors = [
    'header button',
    'header a',
    '[role="tab"]',
    '.tab',
    '.sidebar .label',
    '.sidebar a',
    '.sidebar button',
    'a',
    'button',
    '.menu-item',
    '.nav-item',
  ];
  const candidateTexts = ['项目2.0', '项目管理', '项目驾驶舱', '项目总览', '总览', '项目'];
  for (const selector of candidateSelectors) {
    for (const text of candidateTexts) {
      const locator = page.locator(`${selector}:has-text("${text}")`).first();
      try {
        if ((await locator.count()) > 0) {
          await locator.click({ timeout: 3000 });
          await sleep(1000);
          return;
        }
      } catch {}
    }
  }
}

async function waitForDashboard(page, semanticEntryUrl = '') {
  let lastError = null;
  for (let round = 0; round < 4; round += 1) {
    try {
      const nativeSurface = await page.evaluate(() => {
        const pathname = window.location.pathname || '';
        const hasNativeNav = Boolean(document.querySelector('.o_main_navbar'));
        const hasDiscussToken = Boolean(document.querySelector('.o-mail-Discuss'));
        return pathname.startsWith('/web') || hasNativeNav || hasDiscussToken;
      });
      if (nativeSurface) {
        throw new Error('native_odoo_surface_detected');
      }
      const value = await detectDashboardProfile(page, 10000);
      assert(value !== 'not_found', 'project dashboard surface resolved to 404');
      assert(value === 'old' || value === 'new', 'project dashboard semantic markers not ready');
      return value;
    } catch (error) {
      lastError = error;
      const timeoutSnapshot = await collectDashboardTimeoutSnapshot(page).catch(() => null);
      if (timeoutSnapshot) {
        writeJson('dashboard_timeout_snapshot.json', {
          round,
          error: String(error?.message || error),
          snapshot: timeoutSnapshot,
        });
        recordStage('dashboard_wait:retry', {
          round,
          error: String(error?.message || error),
          url: timeoutSnapshot.url,
          pathname: timeoutSnapshot.pathname,
          has_native_navbar: timeoutSnapshot.has_native_navbar,
          has_scene_eyebrow: timeoutSnapshot.has_scene_eyebrow,
        });
      }
      if (semanticEntryUrl) {
        try {
          await page.goto(semanticEntryUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
          await page.waitForLoadState('domcontentloaded');
          await sleep(800);
        } catch {}
      }
      await tryNavigateDashboardViaUi(page);
    }
  }
  throw lastError || new Error('project dashboard semantic markers not ready');
}

async function ensureAuthenticatedSession(page, semanticEntryUrl = '') {
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    recordStage('auth_attempt:start', { attempt, url: page.url() });
    const onLoginSurface = await isLoginSurfaceReady(page);
    if (!onLoginSurface) {
      recordStage('auth_attempt:skipped', { attempt, reason: 'login_surface_not_ready', url: page.url() });
      return false;
    }
    await fillLoginForm(page);
    await submitLogin(page);
    await sleep(1200);
    const postSubmitSnapshot = await collectLoginSnapshot(page);
    if (!postSubmitSnapshot.has_token) {
      try {
        const runtimeToken = await fetchLoginTokenByApi();
        await persistLoginToken(page, runtimeToken);
        recordStage('auth_attempt:token_restored', { attempt, url: page.url() });
      } catch (error) {
        recordStage('auth_attempt:token_restore_failed', {
          attempt,
          url: page.url(),
          error: String(error?.message || error),
        });
      }
    }
    if (semanticEntryUrl && !isLoginLikeUrl(semanticEntryUrl)) {
      recordStage('auth_attempt:semantic_entry_reload', { attempt, target: semanticEntryUrl });
      await page.goto(semanticEntryUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForLoadState('domcontentloaded');
      await sleep(600);
    }
    const stillOnLogin = await isLoginSurfaceReady(page);
    recordStage('auth_attempt:after_submit', {
      attempt,
      still_on_login: stillOnLogin,
      url: page.url(),
    });
    if (!stillOnLogin) return true;
  }
  throw new Error('login surface remains after credential submit');
}

async function clickActionCard(page, labelText) {
  const patterns = Array.isArray(labelText) ? labelText : [labelText];
  let card = null;
  for (const pattern of patterns) {
    const candidate = page.locator('.action-card').filter({ hasText: pattern }).first();
    try {
      await candidate.waitFor({ timeout: 10000 });
      card = candidate;
      break;
    } catch {}
  }
  if (!card) {
    throw new Error(`action not found: ${patterns.join(' | ')}`);
  }
  await card.waitFor({ timeout: 20000 });
  await card.locator('button.primary-button').click();
}

async function clickPrimaryRecommendedAction(page) {
  const primaryCard = page.locator('.action-card-primary').first();
  await primaryCard.waitFor({ timeout: 20000 });
  await primaryCard.locator('button.primary-button').click();
}

async function waitForScene(page, sceneLabel) {
  recordStage('wait_for_scene:start', { sceneLabel, url: page.url() });
  await page.waitForURL((url) => url.pathname === '/s/project.management' || url.pathname === '/', { timeout: 20000 });
  await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
  await sleep(1200);
  await page.locator('.eyebrow').filter({ hasText: sceneLabel }).first().waitFor({ timeout: 20000 });
  recordStage('wait_for_scene:done', { sceneLabel, url: page.url() });
}

async function waitForAnyMainlineScene(page) {
  recordStage('wait_for_any_mainline_scene:start', { url: page.url() });
  await page.waitForURL((url) => url.pathname === '/s/project.management' || url.pathname === '/', { timeout: 20000 });
  await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
  await sleep(1200);
  const allowed = ['执行推进', '成本记录', '付款记录', '结算结果'];
  await page.waitForFunction((labels) => {
    const text = Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    return labels.some((label) => text.includes(label));
  }, allowed, { timeout: 20000 });
  recordStage('wait_for_any_mainline_scene:done', { url: page.url() });
}

async function waitForPrimaryActionResult(page) {
  recordStage('wait_for_primary_action_result:start', { url: page.url() });
  await page.waitForURL((url) => url.pathname === '/s/project.management' || url.pathname === '/', { timeout: 20000 });
  await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
  await sleep(1200);
  const result = await page.waitForFunction(() => {
    const eyebrowTexts = Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean);
    const inMainline = ['执行推进', '成本记录', '付款记录', '结算结果'].some((label) => eyebrowTexts.includes(label));
    const feedback = document.querySelector('.feedback-banner');
    const onDashboard = eyebrowTexts.includes('项目驾驶舱');
    if (inMainline) return { mode: 'scene', eyebrowTexts };
    if (feedback && onDashboard) {
      return {
        mode: 'dashboard_feedback',
        eyebrowTexts,
        feedbackText: (feedback.textContent || '').trim(),
      };
    }
    return null;
  }, { timeout: 20000 });
  const value = await result.jsonValue();
  recordStage('wait_for_primary_action_result:done', { url: page.url(), mode: value?.mode || '' });
  return value;
}

let browser;
let page;
try {
  const connectivityDiagnostics = await runConnectivityDiagnostics(BASE_URL, DB_NAME);
  summary.connectivity_diagnostics = connectivityDiagnostics;
  if (!connectivityDiagnostics.ok) {
    throw new Error(`connectivity_diagnostics_failed: ${connectivityDiagnostics.last_error || 'unknown'}`);
  }
  if (connectivityDiagnostics.degraded) {
    summary.connectivity_diagnostics_degraded = true;
  }

  const preflight = await probeCustomFrontendEntryReachability(BASE_URL, DB_NAME, connectivityDiagnostics);
  summary.custom_frontend_preflight = preflight;
  if (!preflight.ok) {
    const preflightError = String(preflight.last_error || 'unknown');
    if (isConnectEpermMessage(preflightError)) {
      summary.permission_lane_blocked = true;
      throw new Error(`permission_lane_blocked: ${preflightError}`);
    }
    throw new Error(`custom_frontend_entry_unreachable: ${preflightError}`);
  }
  summary.effective_base_url = preflight.base_url || BASE_URL;
  summary.effective_login_url = preflight.login_url || '';
  RUNTIME_INTENT_BASE_URL = summary.effective_base_url || INTENT_BASE_URL;

  const launchBase = {
    headless: true,
    timeout: 20000,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-seccomp-filter-sandbox',
      '--disable-namespace-sandbox',
    ],
  };
  let defaultError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      browser = await chromium.launch(launchBase);
      summary.launch_mode = 'default';
      summary.default_launch_attempt = attempt;
      break;
    } catch (error) {
      defaultError = error;
      summary.default_launch_error = String(error?.message || error);
      if (attempt < 3) {
        await sleep(attempt * 500);
      }
    }
  }
  if (!browser) {
    const canFallback =
      fs.existsSync(FULL_CHROME_PATH) &&
      shouldUseFullChromeFallback(summary.default_launch_error || String(defaultError?.message || defaultError));
    if (!canFallback) throw defaultError;
    browser = await chromium.launch({ ...launchBase, executablePath: FULL_CHROME_PATH });
    summary.launch_mode = 'full_chrome_fallback';
  }
  page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  page.on('console', (msg) => {
    if (msg.type() === 'error') summary.console_errors.push(msg.text());
  });
  page.on('response', (resp) => {
    try {
      const status = Number(resp.status() || 0);
      if (status >= 500) {
        const request = resp.request();
        let intentHint = '';
        try {
          const jsonBody = request?.postDataJSON?.();
          intentHint = String(jsonBody?.intent || '').trim();
        } catch {}
        if (!intentHint) {
          try {
            const rawBody = String(request?.postData?.() || '');
            const match = rawBody.match(/"intent"\s*:\s*"([^"]+)"/);
            intentHint = String(match?.[1] || '').trim();
          } catch {}
        }
        const resource = {
          status,
          url: String(resp.url() || ''),
          method: String(request?.method?.() || ''),
          resource_type: String(request?.resourceType?.() || ''),
          intent_hint: intentHint,
        };
        const key = `${resource.method}|${resource.status}|${resource.resource_type}|${resource.url}`;
        const exists = summary.http_5xx_resources.some(
          (item) => `${item.method}|${item.status}|${item.resource_type}|${item.url}` === key,
        );
        if (!exists) summary.http_5xx_resources.push(resource);
      }
    } catch {}
  });
  page.on('pageerror', (err) => {
    summary.page_errors.push(String(err?.message || err));
  });

  let bootstrapToken = '';
  try {
    bootstrapToken = await fetchLoginTokenByApi();
    summary.login_mode = 'token_bootstrap';
    await bootstrapLoginToken(page, bootstrapToken);
  } catch (error) {
    summary.login_mode = 'form_login_only';
    summary.login_intent_error = String(error?.message || error);
  }

  let backendEntry = null;
  if (bootstrapToken) {
    try {
      recordStage('backend_entry:resolve:start');
      backendEntry = await resolveProjectEntryRouteByApi(bootstrapToken);
      summary.backend_entry_route = backendEntry.route;
      summary.backend_scene_key = backendEntry.scene_key || '';
      summary.backend_project_context = backendEntry.project_context;
      recordStage('backend_entry:resolve:done', { route: backendEntry.route, scene_key: backendEntry.scene_key || '' });
    } catch (error) {
      summary.backend_entry_route_error = String(error?.message || error);
      recordStage('backend_entry:resolve:fail', { error: summary.backend_entry_route_error });
    }
  }
  recordStage('semantic_entry:start');
  summary.project_route_url_used = await gotoSemanticEntryWithRecovery(page, backendEntry, {
    bootstrapUrl: summary.effective_login_url || '',
  });
  recordStage('semantic_entry:done', { url: summary.project_route_url_used });
  summary.backend_scene_entry_url = summary.project_route_url_used;
  await sleep(1200);
  recordStage('auth_fallback:start', { url: summary.project_route_url_used });
  summary.login_form_fallback_used = await ensureAuthenticatedSession(page, summary.project_route_url_used);
  recordStage('auth_fallback:done', { used: Boolean(summary.login_form_fallback_used), url: page.url() });
  recordStage('dashboard_wait:start', { url: page.url() });
  const dashboardProfile = await waitForDashboard(page, summary.project_route_url_used);
  summary.dashboard_profile = dashboardProfile;
  recordStage('dashboard_wait:done', { profile: dashboardProfile, url: page.url() });

  const dashboardText = await page.locator('body').innerText();
  const hasLegacyDashboard = dashboardProfile === 'old';
  let projectOptionCount = 0;
  let optionTexts = [];
  let primaryResult = { mode: 'dashboard_only' };
  if (hasLegacyDashboard) {
    assert(dashboardText.includes('阶段说明'), 'dashboard missing stage explain');
    assert(dashboardText.includes('里程碑说明'), 'dashboard missing milestone explain');
    assert(dashboardText.includes('当前状态说明'), 'dashboard missing status explain');
    assert(dashboardText.includes('流程地图'), 'dashboard missing flow map');
    await page.locator('.project-switcher').first().waitFor({ timeout: 20000 });
    projectOptionCount = await page.locator('.project-switcher option').count();
    optionTexts = await page.locator('.project-switcher option').evaluateAll((nodes) =>
      nodes.map((node) => (node.textContent || '').trim()),
    );
    assert(projectOptionCount >= 2, `project switcher should expose at least 2 projects, got ${projectOptionCount}`);
    assert(
      optionTexts.some((text) => text.includes('展厅-')),
      `project switcher should include showroom demo projects, got: ${optionTexts.join(' | ')}`,
    );
    await page.locator('.recommended-badge').first().waitFor({ timeout: 20000 });

    await clickActionCard(page, '下一步：进入执行推进');
    await waitForScene(page, '执行推进');
    const execButton = page.locator('.action-list .action-card button.primary-button').first();
    await execButton.waitFor({ timeout: 20000 });
    await execButton.click();
    await waitForDashboard(page);

    await clickPrimaryRecommendedAction(page);
    primaryResult = await waitForPrimaryActionResult(page);
  } else {
    const hasDashboardTitle = dashboardText.includes('项目管理');
    const hasDashboardMetrics = dashboardText.includes('项目总数') || dashboardText.includes('项目阶段');
    const hasProjectCards = await page.locator('[class*="kanban"], [class*="card"]').count();
    const hasProjectDetailToken = /FR-\d+/i.test(dashboardText) && (dashboardText.includes('Owner') || dashboardText.includes('负责人'));
    assert(
      hasDashboardTitle || hasDashboardMetrics || hasProjectCards > 0 || hasProjectDetailToken,
      'project management surface missing both dashboard and project-detail semantic markers',
    );
  }

  const sceneSnapshot = await page.evaluate(() => ({
    eyebrow: Array.from(document.querySelectorAll('.eyebrow'))
      .map((el) => (el.textContent || '').trim())
      .filter(Boolean),
    hasCostForm: Boolean(document.querySelector('.cost-form-card')),
    hasPaymentForm: Boolean(document.querySelector('.payment-form-card')),
    hasSettlementSummary: Boolean(document.querySelector('.metric-list')),
  }));

  const finalSnapshot = await page.evaluate(() => ({
    href: window.location.href,
    pathname: window.location.pathname,
    text: document.body.innerText,
  }));
  assert(!finalSnapshot.href.includes('project_id='), 'dashboard route should not depend on project_id query');
  assert(primaryResult && ['scene', 'dashboard_feedback', 'dashboard_only'].includes(primaryResult.mode), 'invalid primary result mode');
  if (primaryResult.mode === 'dashboard_feedback') {
    assert(finalSnapshot.text.includes('流程地图'), 'dashboard feedback state missing flow map');
    assert(finalSnapshot.text.includes('下一目标'), 'dashboard feedback state missing completion target');
  }

  writeJson('primary_action_result.json', primaryResult);
  writeJson('scene_snapshot.json', sceneSnapshot);
  writeJson('dashboard_snapshot.json', finalSnapshot);
  await page.screenshot({ path: path.join(outDir, 'project_dashboard_primary_entry.png'), fullPage: true });

  summary.cases.push({
    case_id: 'project_dashboard_primary_entry',
    status: 'PASS',
    route: finalSnapshot.pathname,
    project_option_count: projectOptionCount,
    project_option_samples: optionTexts.slice(0, 6),
    dashboard_profile: dashboardProfile,
    primary_result_mode: primaryResult.mode,
  });

  writeJson('summary.json', summary);
  fs.writeFileSync(
    path.join(outDir, 'summary.md'),
    [
      '# Project Dashboard Primary Entry Browser Smoke',
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
