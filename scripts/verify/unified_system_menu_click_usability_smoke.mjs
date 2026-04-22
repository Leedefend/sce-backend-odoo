import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';

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
const VERIFY_MAX_RUN_MS = Number(process.env.VERIFY_MAX_RUN_MS || 180000) || 180000;
const LIFECYCLE_CLEANUP_WAIT_MS = 1500;
const LIFECYCLE_KILL_WAIT_MS = 500;
const TARGET_MENU_ID = Number(process.env.TARGET_MENU_ID || 0) || 0;
const TARGET_MENU_CHAIN = String(process.env.TARGET_MENU_CHAIN || '')
  .split(',')
  .map((value) => Number(String(value || '').trim()))
  .filter((value) => Number.isInteger(value) && value > 0);
const TARGET_SKIP_MENU_IDS = String(process.env.TARGET_SKIP_MENU_IDS || '')
  .split(',')
  .map((value) => Number(String(value || '').trim()))
  .filter((value) => Number.isInteger(value) && value > 0);
const TARGET_END_MENU_ID = Number(process.env.TARGET_END_MENU_ID || 0) || 0;
const TARGET_TAIL_COUNT = Number(process.env.TARGET_TAIL_COUNT || 0) || 0;
const TARGET_SEQ_START = Number(process.env.TARGET_SEQ_START || 0) || 0;
const TARGET_SEQ_END = Number(process.env.TARGET_SEQ_END || 0) || 0;

const API_BASE_CANDIDATES = [
  API_BASE_URL,
  'http://127.0.0.1:18069',
  'http://localhost:18069',
  'http://127.0.0.1:8069',
  'http://localhost:8069',
].map((item) => String(item || '').replace(/\/+$/, '')).filter(Boolean);

const RUN_ROOT_DIR = path.join(ARTIFACTS_DIR, 'codex', 'unified-system-menu-click-usability-smoke');
const ACTIVE_RUN_LOCK_PATH = path.join(RUN_ROOT_DIR, 'active-run.json');
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(RUN_ROOT_DIR, ts);
fs.mkdirSync(outDir, { recursive: true });

function log(message) {
  console.log(`[unified_system_menu_click_usability_smoke] ${message}`);
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function writeProgress(payload) {
  writeJson('progress.json', payload);
}

function readJsonIfExists(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (_error) {
    return null;
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isPidAlive(pid) {
  const numericPid = Number(pid || 0);
  if (!Number.isInteger(numericPid) || numericPid <= 0) {
    return false;
  }
  try {
    process.kill(numericPid, 0);
    return true;
  } catch (_error) {
    return false;
  }
}

function listMatchingPids(commandPattern, excludePid) {
  try {
    const output = execFileSync('ps', ['-eo', 'pid=,args='], { encoding: 'utf8' });
    return output
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const match = line.match(/^(\d+)\s+(.*)$/);
        if (!match) return null;
        return {
          pid: Number(match[1]),
          cmd: match[2],
        };
      })
      .filter(Boolean)
      .filter((entry) => entry.pid !== excludePid && entry.cmd.includes(commandPattern))
      .map((entry) => entry.pid);
  } catch (_error) {
    return [];
  }
}

async function terminatePidSet(pids, signal) {
  for (const pid of pids) {
    try {
      process.kill(pid, signal);
    } catch (_error) {
      // Ignore already-exited processes.
    }
  }
}

async function cleanupCompetingRuns() {
  const competingNodePids = listMatchingPids('node scripts/verify/unified_system_menu_click_usability_smoke.mjs', process.pid);
  const competingMakePids = listMatchingPids('make verify.portal.unified_system_menu_click_usability_smoke.host', process.ppid);
  const allCompetingPids = [...new Set([...competingNodePids, ...competingMakePids])];
  if (!allCompetingPids.length) {
    return;
  }
  writeProgress({
    stage: 'competing_run_detected',
    competing_pids: allCompetingPids,
    updated_at: new Date().toISOString(),
  });
  await terminatePidSet(allCompetingPids, 'SIGTERM');
  await sleep(LIFECYCLE_CLEANUP_WAIT_MS);
  const remainingAfterTerm = allCompetingPids.filter((pid) => isPidAlive(pid));
  if (remainingAfterTerm.length) {
    await terminatePidSet(remainingAfterTerm, 'SIGKILL');
    await sleep(LIFECYCLE_KILL_WAIT_MS);
  }
  const stubbornPids = allCompetingPids.filter((pid) => isPidAlive(pid));
  writeProgress({
    stage: 'competing_run_cleanup_done',
    competing_pids: allCompetingPids,
    stubborn_pids: stubbornPids,
    updated_at: new Date().toISOString(),
  });
  if (stubbornPids.length) {
    throw new Error(`stale competing runs still alive after cleanup: ${stubbornPids.join(',')}`);
  }
}

function clearStaleRunLock() {
  const existing = readJsonIfExists(ACTIVE_RUN_LOCK_PATH);
  if (!existing) {
    return;
  }
  if (Number(existing.pid || 0) === process.pid) {
    return;
  }
  if (isPidAlive(existing.pid)) {
    throw new Error(`active run lock still owned by live pid=${existing.pid}`);
  }
  fs.rmSync(ACTIVE_RUN_LOCK_PATH, { force: true });
  writeProgress({
    stage: 'stale_run_lock_cleared',
    stale_pid: Number(existing.pid || 0),
    updated_at: new Date().toISOString(),
  });
}

function acquireRunLock() {
  fs.writeFileSync(ACTIVE_RUN_LOCK_PATH, `${JSON.stringify({
    pid: process.pid,
    ppid: process.ppid,
    out_dir: outDir,
    started_at: new Date().toISOString(),
    timeout_ms: VERIFY_MAX_RUN_MS,
  }, null, 2)}\n`, 'utf8');
  writeProgress({
    stage: 'lifecycle_lock_acquired',
    pid: process.pid,
    ppid: process.ppid,
    timeout_ms: VERIFY_MAX_RUN_MS,
    updated_at: new Date().toISOString(),
  });
}

function releaseRunLock() {
  const existing = readJsonIfExists(ACTIVE_RUN_LOCK_PATH);
  if (existing && Number(existing.pid || 0) !== process.pid) {
    return;
  }
  fs.rmSync(ACTIVE_RUN_LOCK_PATH, { force: true });
}

async function acquireLifecycleOwnership() {
  await cleanupCompetingRuns();
  clearStaleRunLock();
  acquireRunLock();
}

async function runWithLifecycleTimeout(runFn) {
  let timeoutId = null;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = setTimeout(() => {
      writeProgress({
        stage: 'lifecycle_timeout',
        timeout_ms: VERIFY_MAX_RUN_MS,
        updated_at: new Date().toISOString(),
      });
      reject(new Error(`verify lifecycle timeout after ${VERIFY_MAX_RUN_MS}ms`));
    }, VERIFY_MAX_RUN_MS);
  });
  try {
    return await Promise.race([runFn(), timeoutPromise]);
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

async function fetchLoginToken() {
  const REQUEST_TIMEOUT_MS = 12000;
  let lastError = null;
  for (const apiBase of API_BASE_CANDIDATES) {
    for (let attempt = 0; attempt < 5; attempt += 1) {
      writeProgress({
        stage: 'fetch_login_token',
        api_base: apiBase,
        attempt: attempt + 1,
        timeout_ms: REQUEST_TIMEOUT_MS,
        updated_at: new Date().toISOString(),
      });
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(new Error(`login token request timeout after ${REQUEST_TIMEOUT_MS}ms`)), REQUEST_TIMEOUT_MS);
      try {
        const response = await fetch(`${apiBase}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Anonymous-Intent': 'true',
          },
          signal: controller.signal,
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
          clearTimeout(timeoutId);
          await new Promise((resolve) => setTimeout(resolve, 1200));
          continue;
        }
        const parsed = await response.json();
        const data = parsed?.data && typeof parsed.data === 'object' ? parsed.data : parsed;
        const token = String(data?.session?.token || data?.token || '').trim();
        if (token) {
          clearTimeout(timeoutId);
          return { token, apiBase };
        }
        lastError = new Error(`login response missing token from ${apiBase}`);
      } catch (error) {
        lastError = error;
      } finally {
        clearTimeout(timeoutId);
      }
      await new Promise((resolve) => setTimeout(resolve, 1200));
    }
  }
  throw new Error(`login token fetch failed: ${String(lastError?.message || lastError || 'unknown')}`);
}

function asRecord(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}

function asText(value) {
  return String(value || '').trim();
}

function asPositiveInt(value) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : 0;
}

function mergeRouteQuery(route, paramsToMerge) {
  const rawRoute = asText(route);
  if (!rawRoute) {
    return '';
  }
  const routeUrl = new URL(rawRoute, 'http://localhost');
  for (const [key, value] of Object.entries(paramsToMerge || {})) {
    if (value === undefined || value === null || String(value).trim() === '') {
      continue;
    }
    routeUrl.searchParams.set(key, String(value));
  }
  return `${routeUrl.pathname}${routeUrl.search}${routeUrl.hash}`;
}

function buildSceneRoute(sceneKey, actionId, route) {
  const normalizedSceneKey = asText(sceneKey);
  const baseRoute = asText(route) || (normalizedSceneKey ? `/s/${normalizedSceneKey}` : '');
  if (!baseRoute || !normalizedSceneKey) {
    return '';
  }
  return mergeRouteQuery(baseRoute, {
    scene_key: normalizedSceneKey,
    action_id: actionId > 0 ? String(actionId) : undefined,
  });
}

function resolveExplainedLeaf(node, ancestors) {
  const menuId = asPositiveInt(node.menu_id || node.id);
  if (!menuId) {
    return { include: null, skip_reason: 'missing_menu_id', skipped: null };
  }
  const target = asRecord(node.target);
  const entryTarget = asRecord(node.entry_target);
  const compatibilityRefs = asRecord(entryTarget.compatibility_refs);
  const context = asRecord(entryTarget.context);
  const meta = asRecord(node.meta);
  const targetType = asText(node.target_type || meta.target_type);
  const sceneKey =
    asText(target.scene_key)
    || asText(entryTarget.scene_key)
    || asText(meta.scene_key);
  const actionId =
    asPositiveInt(target.action_id)
    || asPositiveInt(compatibilityRefs.action_id)
    || asPositiveInt(context.action_id)
    || asPositiveInt(meta.action_id);
  const route =
    buildSceneRoute(sceneKey, actionId, asText(entryTarget.route))
    || buildSceneRoute(sceneKey, actionId, asText(node.route))
    || asText(entryTarget.route)
    || asText(node.route)
    || asText(meta.route);
  const isClickable = node.is_clickable === true && targetType !== 'unavailable' && targetType !== 'directory';
  let skipReason = '';
  if (node.is_visible === false) {
    skipReason = 'hidden';
  } else if (!isClickable) {
    skipReason = targetType === 'directory' ? 'directory' : targetType === 'unavailable' ? 'unavailable' : 'not_clickable';
  } else if (!route) {
    skipReason = 'missing_route';
  }
  if (skipReason) {
    return {
      include: null,
      skip_reason: skipReason,
      skipped: {
        menu_id: menuId,
        label: String(node.label || node.title || node.name || node.key || `menu_${menuId}`),
        path: [...ancestors, String(node.label || node.title || node.name || node.key || '')].filter(Boolean).join('/'),
        target_type: targetType || 'unknown',
      },
    };
  }
  return {
    include: {
      menu_id: menuId,
      label: String(node.label || node.title || node.name || node.key || `menu_${menuId}`),
      path: [...ancestors, String(node.label || node.title || node.name || node.key || '')].filter(Boolean).join('/'),
      scene_key: sceneKey,
      route,
      action_id: actionId,
      menu_xmlid: asText(target.menu_xmlid) || asText(meta.menu_xmlid),
      source_kind: 'nav_explained.tree',
    },
    skip_reason: '',
    skipped: null,
  };
}

function flattenLeafMenus(nodes, sourceKind = 'runtime') {
  const out = [];
  const skipped = [];
  const skipReasonCounts = {};
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
      if (sourceKind === 'nav_explained.tree') {
        const explainedLeaf = resolveExplainedLeaf(node, ancestors);
        if (explainedLeaf.include) {
          out.push(explainedLeaf.include);
        } else if (explainedLeaf.skip_reason) {
          skipReasonCounts[explainedLeaf.skip_reason] = (skipReasonCounts[explainedLeaf.skip_reason] || 0) + 1;
          if (explainedLeaf.skipped) {
            skipped.push({ ...explainedLeaf.skipped, skip_reason: explainedLeaf.skip_reason });
          }
        }
        continue;
      }
      const meta = node.meta && typeof node.meta === 'object' ? node.meta : {};
      out.push({
        menu_id: menuId,
        label: String(node.label || node.title || node.name || node.key || `menu_${menuId}`),
        path: [...ancestors, String(node.label || node.title || node.name || node.key || '')].filter(Boolean).join('/'),
        scene_key: String(meta.scene_key || '').trim(),
        route: String(meta.route || '').trim(),
        action_id: Number(meta.action_id || 0) || 0,
        menu_xmlid: String(meta.menu_xmlid || '').trim(),
        source_kind: sourceKind,
      });
    }
  };
  walk(nodes, []);
  return {
    included: out,
    skipped,
    skip_reason_counts: skipReasonCounts,
  };
}

async function readMenusFromStorage(page) {
  writeProgress({
    stage: 'runtime_storage_read_start',
    updated_at: new Date().toISOString(),
  });
  const result = await page.evaluate(() => {
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
  writeProgress({
    stage: 'runtime_storage_read_done',
    cache_key: String(result?.cache_key || ''),
    release_tree_count: Array.isArray(result?.release_tree) ? result.release_tree.length : 0,
    menu_tree_count: Array.isArray(result?.menu_tree) ? result.menu_tree.length : 0,
    updated_at: new Date().toISOString(),
  });
  return result;
}

async function readExplainedMenusFromApi(page, dbName) {
  writeProgress({
    stage: 'nav_api_read_start',
    db_name: dbName,
    updated_at: new Date().toISOString(),
  });
  const result = await page.evaluate(async ({ dbName }) => {
    const token =
      sessionStorage.getItem(`sc_auth_token:${dbName}`)
      || sessionStorage.getItem('sc_auth_token:default')
      || sessionStorage.getItem('sc_auth_token:test')
      || sessionStorage.getItem('sc_auth_token')
      || '';
    const dbHeader =
      localStorage.getItem('sc_active_db:default')
      || dbName
      || '';
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (dbHeader) {
      headers['X-Odoo-DB'] = dbHeader;
    }
    const response = await fetch('/api/menu/navigation', {
      method: 'POST',
      headers,
      body: JSON.stringify({}),
      credentials: 'omit',
    });
    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        tree: [],
      };
    }
    const body = await response.json();
    const navExplained = body && typeof body === 'object' && body.nav_explained && typeof body.nav_explained === 'object'
      ? body.nav_explained
      : {};
    const tree = Array.isArray(navExplained.tree) ? navExplained.tree : [];
    return {
      ok: true,
      status: response.status,
      tree,
    };
  }, { dbName });
  writeProgress({
    stage: 'nav_api_read_done',
    ok: Boolean(result?.ok),
    status: Number(result?.status || 0),
    tree_count: Array.isArray(result?.tree) ? result.tree.length : 0,
    updated_at: new Date().toISOString(),
  });
  return result;
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

function isMenu314InternalErrorText(menuId, text) {
  if (Number(menuId || 0) !== 314) {
    return false;
  }
  const normalized = String(text || '').toLowerCase();
  const tokens = [
    'system exception',
    'internal_error',
    '错误码：500',
    '错误码:500',
  ];
  return tokens.some((token) => normalized.includes(token.toLowerCase()));
}

function isBrowserClosureErrorMessage(message) {
  const normalized = String(message || '').toLowerCase();
  return (
    normalized.includes('target page, context or browser has been closed')
    || normalized.includes('browser has been closed')
    || normalized.includes('context closed')
    || normalized.includes('page has been closed')
  );
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
  const targetUrl = String(leaf.route || '').trim()
    ? `${BASE_URL}${String(leaf.route).startsWith('/') ? '' : '/'}${String(leaf.route)}`
    : `${BASE_URL}/m/${leaf.menu_id}?menu_id=${leaf.menu_id}`;
  const result = {
    ...leaf,
    target_url: targetUrl,
    final_url: '',
    status: 'PASS',
    error_text: '',
    networkidle_timeout: false,
    stability_closure_detected: false,
    sequence_index: 0,
    predecessor_menu_id: 0,
    predecessor_route: '',
    success_count_before_leaf: 0,
    failure_count_before_leaf: 0,
  };
  try {
    writeProgress({
      stage: 'leaf_verify_goto_start',
      menu_id: leaf.menu_id,
      route: leaf.route,
      target_url: targetUrl,
      updated_at: new Date().toISOString(),
    });
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    writeProgress({
      stage: 'leaf_verify_goto_done',
      menu_id: leaf.menu_id,
      final_url: page.url(),
      updated_at: new Date().toISOString(),
    });
    const settle = await waitForPageSettled(page, { allowNetworkIdleTimeout: true });
    writeProgress({
      stage: 'leaf_verify_settle_done',
      menu_id: leaf.menu_id,
      networkidle_timeout: settle.networkIdleTimedOut,
      final_url: page.url(),
      updated_at: new Date().toISOString(),
    });
    result.networkidle_timeout = settle.networkIdleTimedOut;
    result.final_url = page.url();
    writeProgress({
      stage: 'leaf_verify_dom_read_start',
      menu_id: leaf.menu_id,
      final_url: result.final_url,
      updated_at: new Date().toISOString(),
    });
    result.error_text = await page.evaluate(() => {
      const text = Array.from(document.querySelectorAll('body, .status-panel, [data-component="StatusPanel"]'))
        .map((node) => node.textContent || '')
        .join('\n');
      return String(text || '').slice(0, 1200);
    });
    writeProgress({
      stage: 'leaf_verify_dom_read_done',
      menu_id: leaf.menu_id,
      final_url: result.final_url,
      error_text_preview: String(result.error_text || '').slice(0, 160),
      updated_at: new Date().toISOString(),
    });
    if (
      result.final_url.includes('reason=CONTRACT_CONTEXT_MISSING')
      || result.final_url.includes('diag=legacy_route_missing_action_id')
      || result.final_url.includes('diag=scene_registry_missing')
      || isFailureText(result.error_text)
      || isMenu314InternalErrorText(leaf.menu_id, result.error_text)
    ) {
      result.status = 'FAIL';
    }
  } catch (error) {
    result.status = 'FAIL';
    result.error_text = String(error?.message || error);
    result.final_url = page.url();
    result.stability_closure_detected = isBrowserClosureErrorMessage(result.error_text);
    writeProgress({
      stage: 'leaf_verify_error',
      menu_id: leaf.menu_id,
      route: leaf.route,
      final_url: result.final_url,
      error: result.error_text,
      stability_closure_detected: result.stability_closure_detected,
      updated_at: new Date().toISOString(),
    });
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
  discovered_leaf_count: 0,
  executed_leaf_count: 0,
  skipped_leaf_count: 0,
  skipped_leaf_reason_counts: {},
  stability_closure_detected: false,
  aborted_after_menu_id: 0,
  aborted_after_reason: '',
  first_failure_sequence_index: 0,
  first_failure_predecessor_menu_id: 0,
  first_failure_predecessor_route: '',
  success_count_before_first_failure: 0,
};

function buildProgressPayload({
  stage,
  sourceKind = 'none',
  discoveredLeafCount = 0,
  executedLeafCount = 0,
  skippedLeafCount = 0,
  failedCount = 0,
  currentLeaf = null,
}) {
  return {
    stage,
    nav_source: sourceKind,
    discovered_leaf_count: discoveredLeafCount,
    executed_leaf_count: executedLeafCount,
    skipped_leaf_count: skippedLeafCount,
    failed_count: failedCount,
    current_leaf: currentLeaf,
    target_menu_id: TARGET_MENU_ID || null,
    target_menu_chain: TARGET_MENU_CHAIN.length ? TARGET_MENU_CHAIN : null,
    target_skip_menu_ids: TARGET_SKIP_MENU_IDS.length ? TARGET_SKIP_MENU_IDS : null,
    target_end_menu_id: TARGET_END_MENU_ID || null,
    target_tail_count: TARGET_TAIL_COUNT || null,
    target_seq_start: TARGET_SEQ_START || null,
    target_seq_end: TARGET_SEQ_END || null,
    updated_at: new Date().toISOString(),
  };
}

let browser;
let runResult = {
  failedCount: 0,
  completed: false,
};
try {
  writeProgress(buildProgressPayload({ stage: 'booting' }));
  await acquireLifecycleOwnership();
  runResult = await runWithLifecycleTimeout(async () => {
    log('fetch login token');
    const { token, apiBase } = await fetchLoginToken();
    summary.used_api_base = apiBase;
    writeProgress({
      stage: 'fetch_login_token_done',
      api_base: apiBase,
      token_present: Boolean(token),
      updated_at: new Date().toISOString(),
    });

    browser = await chromium.launch({
      headless: true,
      timeout: 20000,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-seccomp-filter-sandbox', '--disable-namespace-sandbox'],
    });
    writeProgress({
      stage: 'browser_launch_done',
      updated_at: new Date().toISOString(),
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

    writeProgress({
      stage: 'page_goto_start',
      url: `${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`,
      updated_at: new Date().toISOString(),
    });
    await page.goto(`${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
    writeProgress({
      stage: 'page_goto_done',
      current_url: page.url(),
      updated_at: new Date().toISOString(),
    });
    await waitForPageSettled(page, { allowNetworkIdleTimeout: true });
    await page.waitForTimeout(1500);

    const runtime = await readMenusFromStorage(page);
    const explained = await readExplainedMenusFromApi(page, DB_NAME);
    let sourceTree = [];
    let sourceKind = 'none';
    if (explained.ok && explained.tree.length) {
      sourceTree = explained.tree;
      sourceKind = 'nav_explained.tree';
    } else if (runtime.release_tree.length) {
      sourceTree = runtime.release_tree;
      sourceKind = 'release_tree';
    } else if (runtime.menu_tree.length) {
      sourceTree = runtime.menu_tree;
      sourceKind = 'menu_tree';
    }
    const flattened = flattenLeafMenus(sourceTree, sourceKind);
    const allLeaves = flattened.included;
    let leaves = allLeaves;
    if (TARGET_MENU_CHAIN.length) {
      const byMenuId = new Map(allLeaves.map((leaf) => [leaf.menu_id, leaf]));
      leaves = TARGET_MENU_CHAIN.map((menuId) => byMenuId.get(menuId)).filter(Boolean);
    }
    if (TARGET_SEQ_START > 0 || TARGET_SEQ_END > 0) {
      const startIndex = Math.max(1, TARGET_SEQ_START || 1);
      const endIndex = Math.max(startIndex, TARGET_SEQ_END || allLeaves.length);
      const allowedMenuIds = new Set(allLeaves.slice(startIndex - 1, endIndex).map((leaf) => leaf.menu_id));
      leaves = leaves.filter((leaf) => allowedMenuIds.has(leaf.menu_id));
    }
    if (TARGET_MENU_ID > 0) {
      leaves = leaves.filter((leaf) => leaf.menu_id === TARGET_MENU_ID);
    }
    if (TARGET_SKIP_MENU_IDS.length) {
      const skippedMenuIds = new Set(TARGET_SKIP_MENU_IDS);
      leaves = leaves.filter((leaf) => !skippedMenuIds.has(leaf.menu_id));
    }
    if (TARGET_END_MENU_ID > 0 && TARGET_TAIL_COUNT > 0) {
      const endIndex = leaves.findIndex((leaf) => leaf.menu_id === TARGET_END_MENU_ID);
      if (endIndex >= 0) {
        const startIndex = Math.max(0, endIndex - TARGET_TAIL_COUNT + 1);
        leaves = leaves.slice(startIndex, endIndex + 1);
      }
    }
    summary.nav_source = sourceKind;
    summary.discovered_leaf_count = allLeaves.length + flattened.skipped.length;
    summary.executed_leaf_count = leaves.length;
    summary.skipped_leaf_count = flattened.skipped.length;
    summary.skipped_leaf_reason_counts = flattened.skip_reason_counts;
    summary.leaf_count = leaves.length;
    assert(
      leaves.length > 0,
      TARGET_MENU_CHAIN.length
        ? `target menu chain not discovered: ${TARGET_MENU_CHAIN.join(',')}`
        : TARGET_MENU_ID > 0
          ? `target menu not discovered: ${TARGET_MENU_ID}`
          : TARGET_SEQ_START > 0 || TARGET_SEQ_END > 0
            ? `target sequence window not discovered: ${TARGET_SEQ_START || 1}-${TARGET_SEQ_END || allLeaves.length}`
          : 'no menu leaves discovered from runtime storage',
    );
    writeProgress(buildProgressPayload({
      stage: 'prepared',
      sourceKind,
      discoveredLeafCount: summary.discovered_leaf_count,
      executedLeafCount: 0,
      skippedLeafCount: summary.skipped_leaf_count,
      failedCount: 0,
    }));
    writeProgress({
      stage: 'target_selection_done',
      target_menu_id: TARGET_MENU_ID || null,
      target_menu_chain: TARGET_MENU_CHAIN.length ? TARGET_MENU_CHAIN : null,
      target_skip_menu_ids: TARGET_SKIP_MENU_IDS.length ? TARGET_SKIP_MENU_IDS : null,
      target_end_menu_id: TARGET_END_MENU_ID || null,
      target_tail_count: TARGET_TAIL_COUNT || null,
      target_seq_start: TARGET_SEQ_START || null,
      target_seq_end: TARGET_SEQ_END || null,
      selected_leaf_count: leaves.length,
      total_leaf_count: allLeaves.length,
      updated_at: new Date().toISOString(),
    });

    const cases = [];
    let successfulLeafCount = 0;
    let previousLeaf = null;
    writeProgress({
      stage: 'leaf_loop_entry',
      leaf_count: leaves.length,
      updated_at: new Date().toISOString(),
    });
    for (let index = 0; index < leaves.length; index += 1) {
      const leaf = leaves[index];
      const failedCountBeforeLeaf = cases.filter((item) => item.status !== 'PASS').length;
      writeProgress(buildProgressPayload({
        stage: 'executing',
        sourceKind,
        discoveredLeafCount: summary.discovered_leaf_count,
        executedLeafCount: index,
        skippedLeafCount: summary.skipped_leaf_count,
        failedCount: failedCountBeforeLeaf,
        currentLeaf: {
          index: index + 1,
          total: leaves.length,
          menu_id: leaf.menu_id,
          route: leaf.route,
        },
      }));
      const item = await verifyLeaf(page, leaf);
      item.sequence_index = index + 1;
      item.predecessor_menu_id = Number(previousLeaf?.menu_id || 0);
      item.predecessor_route = String(previousLeaf?.route || '');
      item.success_count_before_leaf = successfulLeafCount;
      item.failure_count_before_leaf = failedCountBeforeLeaf;
      cases.push(item);
      writeJson('cases.partial.json', cases);
      writeProgress({
        stage: 'accumulation_checkpoint',
        target_menu_id: TARGET_MENU_ID || null,
        target_skip_menu_ids: TARGET_SKIP_MENU_IDS.length ? TARGET_SKIP_MENU_IDS : null,
        target_end_menu_id: TARGET_END_MENU_ID || null,
        target_tail_count: TARGET_TAIL_COUNT || null,
        sequence_index: item.sequence_index,
        menu_id: item.menu_id,
        route: item.route,
        predecessor_menu_id: item.predecessor_menu_id,
        predecessor_route: item.predecessor_route,
        success_count_before_leaf: item.success_count_before_leaf,
        failure_count_before_leaf: item.failure_count_before_leaf,
        current_status: item.status,
        updated_at: new Date().toISOString(),
      });
      if (item.status === 'PASS') {
        successfulLeafCount += 1;
      }
      if (item.stability_closure_detected) {
        summary.stability_closure_detected = true;
        summary.aborted_after_menu_id = leaf.menu_id;
        summary.aborted_after_reason = 'browser_context_closed';
        summary.first_failure_sequence_index = item.sequence_index;
        summary.first_failure_predecessor_menu_id = item.predecessor_menu_id;
        summary.first_failure_predecessor_route = item.predecessor_route;
        summary.success_count_before_first_failure = item.success_count_before_leaf;
        writeProgress({
          stage: 'stability_closure_failfast',
          menu_id: leaf.menu_id,
          route: leaf.route,
          error: item.error_text,
          sequence_index: item.sequence_index,
          predecessor_menu_id: item.predecessor_menu_id,
          predecessor_route: item.predecessor_route,
          success_count_before_leaf: item.success_count_before_leaf,
          updated_at: new Date().toISOString(),
        });
        break;
      }
      writeProgress(buildProgressPayload({
        stage: 'executing',
        sourceKind,
        discoveredLeafCount: summary.discovered_leaf_count,
        executedLeafCount: index + 1,
        skippedLeafCount: summary.skipped_leaf_count,
        failedCount: cases.filter((entry) => entry.status !== 'PASS').length,
        currentLeaf: {
          index: index + 1,
          total: leaves.length,
          menu_id: leaf.menu_id,
          route: leaf.route,
          status: item.status,
        },
      }));
      previousLeaf = item;
    }
    writeJson('cases.json', cases);
    if (flattened.skipped.length) {
      writeJson('skipped_cases.json', flattened.skipped);
    }

    const failed = cases.filter((item) => item.status !== 'PASS');
    summary.non_blocking_networkidle_timeouts = cases.filter((item) => item.networkidle_timeout).length;
    summary.fail_count = failed.length;
    summary.failed_menu_ids = failed.map((item) => item.menu_id);
    if (failed.length) {
      summary.status = 'FAIL';
      writeJson('failed_cases.json', failed);
    }
    writeJson('summary.json', summary);
    writeProgress(buildProgressPayload({
      stage: failed.length ? 'completed_fail' : 'completed_pass',
      sourceKind,
      discoveredLeafCount: summary.discovered_leaf_count,
      executedLeafCount: leaves.length,
      skippedLeafCount: summary.skipped_leaf_count,
      failedCount: failed.length,
    }));
    return {
      failedCount: failed.length,
      completed: true,
    };
  });
  if (runResult.failedCount > 0) {
    log(`FAIL menu click usability failures=${runResult.failedCount}`);
    log(`artifacts: ${outDir}`);
    process.exitCode = 1;
  } else {
    log(`PASS leaf_count=${summary.leaf_count}`);
    log(`artifacts: ${outDir}`);
  }
} catch (error) {
  summary.status = 'FAIL';
  summary.error = String(error?.message || error);
  writeJson('summary.json', summary);
  writeProgress(buildProgressPayload({
    stage: 'errored',
    sourceKind: summary.nav_source || 'none',
    discoveredLeafCount: summary.discovered_leaf_count || 0,
    executedLeafCount: summary.executed_leaf_count || 0,
    skippedLeafCount: summary.skipped_leaf_count || 0,
    failedCount: summary.fail_count || 0,
    currentLeaf: { error: summary.error },
  }));
  log(`FAIL ${summary.error}`);
  log(`artifacts: ${outDir}`);
  process.exitCode = 1;
} finally {
  if (browser) {
    await browser.close().catch(() => {});
  }
  releaseRunLock();
}
