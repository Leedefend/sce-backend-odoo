#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || process.env.SCENE_LOGIN || 'admin';
const PASSWORD =
  process.env.E2E_PASSWORD ||
  process.env.SCENE_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const REPO_ROOT = process.env.REPO_ROOT || '/mnt';
const ALLOW_SKIP_UNKNOWN_INTENT = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.MY_WORK_SMOKE_ALLOW_SKIP || '').trim().toLowerCase()
);

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'cross-stack-contract-smoke-v0_1', ts);

function log(msg) {
  console.log(`[fe_cross_stack_contract_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload || {});
    const opts = {
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    };
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        let parsed = {};
        try {
          parsed = JSON.parse(data || '{}');
        } catch {
          parsed = { raw: data };
        }
        resolve({ status: res.statusCode || 0, body: parsed });
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function assert(cond, message) {
  if (!cond) {
    throw new Error(message);
  }
}

function extractTraceId(body) {
  if (!body || typeof body !== 'object') return '';
  const meta = body.meta && typeof body.meta === 'object' ? body.meta : {};
  return String(meta.trace_id || meta.traceId || body.trace_id || body.traceId || '');
}

function assertIntentEnvelope(resp, intentName) {
  assert(resp.status < 400, `${intentName} failed: status=${resp.status}`);
  assert(resp.body && typeof resp.body === 'object', `${intentName} missing response body`);
  assert(resp.body.ok === true, `${intentName} missing ok=true envelope`);
  const traceId = extractTraceId(resp.body);
  assert(Boolean(traceId), `${intentName} missing meta.trace_id`);
  const meta = resp.body.meta && typeof resp.body.meta === 'object' ? resp.body.meta : {};
  const metaIntent = String(meta.intent || '');
  if (metaIntent) {
    assert(metaIntent === intentName, `${intentName} meta.intent mismatch: ${metaIntent}`);
  }
}

function resolveRepoRoot() {
  const candidates = [REPO_ROOT, '/mnt/extra-addons', '/mnt', process.cwd()];
  for (const candidate of candidates) {
    const appShellPath = path.join(candidate, 'frontend/apps/web/src/layouts/AppShell.vue');
    if (fs.existsSync(appShellPath)) {
      return candidate;
    }
  }
  return null;
}

function collectSceneKeys(nodes, out = []) {
  for (const node of nodes || []) {
    if (!node || typeof node !== 'object') continue;
    if (typeof node.scene_key === 'string' && node.scene_key) {
      out.push(node.scene_key);
    }
    if (node.meta && typeof node.meta === 'object' && typeof node.meta.scene_key === 'string' && node.meta.scene_key) {
      out.push(node.meta.scene_key);
    }
    if (Array.isArray(node.children) && node.children.length) {
      collectSceneKeys(node.children, out);
    }
  }
  return out;
}

function verifyFrontendContracts() {
  const repoRoot = resolveRepoRoot();
  if (!repoRoot) {
    return {
      ok: true,
      missing: [],
      checked_files: 0,
      repo_root: null,
      skipped: true,
      skip_reason: 'frontend workspace not mounted in runtime container',
    };
  }
  const checks = [
    {
      file: path.join(repoRoot, 'frontend/apps/web/src/layouts/AppShell.vue'),
      patterns: ['router.push({ path: `/s/${sceneKey}`', 'resolveSceneKeyFromNode(node)'],
    },
    {
      file: path.join(repoRoot, 'frontend/apps/web/src/views/MyWorkView.vue'),
      patterns: ['resolveSuggestedAction(', 'runSuggestedAction('],
    },
  ];

  const missing = [];
  for (const check of checks) {
    if (!fs.existsSync(check.file)) {
      missing.push(`${check.file}: missing file`);
      continue;
    }
    const text = fs.readFileSync(check.file, 'utf-8');
    for (const pattern of check.patterns) {
      if (!text.includes(pattern)) {
        missing.push(`${check.file}: missing pattern -> ${pattern}`);
      }
    }
  }

  return {
    ok: missing.length === 0,
    missing,
    checked_files: checks.length,
    repo_root: repoRoot,
    skipped: false,
  };
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token) {
    const loginResp = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
      { 'X-Anonymous-Intent': '1' }
    );
    writeJson(path.join(outDir, 'login.log'), loginResp);
    assertIntentEnvelope(loginResp, 'login');
    token = (((loginResp.body || {}).data) || {}).token || '';
    assert(Boolean(token), 'login response missing token');
  }

  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };

  const initResp = await requestJson(intentUrl, { intent: 'app.init', params: { scene: 'web', with_preload: false } }, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  assertIntentEnvelope(initResp, 'app.init');

  const initData = (initResp.body || {}).data || {};
  const scenes = Array.isArray(initData.scenes) ? initData.scenes : [];
  const nav = Array.isArray(initData.nav) ? initData.nav : [];
  const sceneVersion = initData.scene_version || initData.sceneVersion;
  const sceneWithTarget = Array.isArray(scenes)
    ? scenes.find((scene) => {
        if (!scene || typeof scene !== 'object') return false;
        const target = scene.target;
        if (!target || typeof target !== 'object') return false;
        return Boolean(target.route || target.action_id || target.menu_id);
      })
    : null;
  const navSceneKeys = collectSceneKeys(nav);
  const sceneKeysFromScenes = Array.isArray(scenes)
    ? scenes
        .map((scene) => (scene && typeof scene === 'object' ? scene.scene_key : ''))
        .filter((sceneKey) => typeof sceneKey === 'string' && sceneKey)
    : [];
  const totalSceneKeys = [...new Set([...navSceneKeys, ...sceneKeysFromScenes])];

  assert(scenes.length > 0 || nav.length > 0, 'app.init missing scenes/nav contract');
  if (scenes.length) {
    assert(Boolean(sceneVersion), 'app.init missing scene_version while scenes are present');
    assert(Boolean(sceneWithTarget), 'app.init scenes missing target contract');
  }
  assert(totalSceneKeys.length > 0, 'app.init missing resolvable scene keys');

  const myWorkResp = await requestJson(
    intentUrl,
    {
      intent: 'my.work.summary',
      params: {
        limit: 20,
        limit_each: 10,
        page: 1,
        page_size: 10,
        section: 'all',
        source: 'all',
        reason_code: 'all',
        search: '',
      },
    },
    authHeader
  );
  writeJson(path.join(outDir, 'my_work_summary.log'), myWorkResp);
  if (myWorkResp.status >= 400 || !myWorkResp.body.ok) {
    const errMsg = String((((myWorkResp.body || {}).error) || {}).message || '');
    if (errMsg.includes('Unknown intent: my.work.summary') && ALLOW_SKIP_UNKNOWN_INTENT) {
      summary.push('status: SKIP');
      summary.push('reason: my.work.summary intent not registered in current DB');
      summary.push(`db: ${DB_NAME}`);
      summary.push(`scene_keys_detected: ${totalSceneKeys.length}`);
      writeSummary(summary);
      log('SKIP cross-stack smoke (my.work.summary not registered)');
      log(`artifacts: ${outDir}`);
      return;
    }
    throw new Error(`my.work.summary failed: status=${myWorkResp.status} message=${errMsg || '-'}`);
  }
  assertIntentEnvelope(myWorkResp, 'my.work.summary');

  const summaryData = (myWorkResp.body || {}).data || {};
  const statusState = (((summaryData || {}).status) || {}).state;
  const items = Array.isArray(summaryData.items) ? summaryData.items : [];
  const filters = summaryData.filters && typeof summaryData.filters === 'object' ? summaryData.filters : {};

  assert(typeof statusState === 'string' && statusState.length > 0, 'my.work.summary missing status.state');
  assert(typeof filters === 'object', 'my.work.summary missing filters object');

  const frontendContract = verifyFrontendContracts();
  writeJson(path.join(outDir, 'frontend_contract_probe.log'), frontendContract);
  assert(frontendContract.ok, `frontend contract probe failed: ${frontendContract.missing.join(' | ')}`);

  summary.push(`db: ${DB_NAME}`);
  summary.push(`scene_version: ${sceneVersion}`);
  summary.push(`scenes_count: ${scenes.length}`);
  summary.push(`nav_count: ${nav.length}`);
  summary.push(`scene_keys_detected: ${totalSceneKeys.length}`);
  summary.push(`my_work_status: ${statusState}`);
  summary.push(`my_work_items: ${items.length}`);
  summary.push(`frontend_contract_files: ${frontendContract.checked_files}`);
  summary.push(`frontend_contract_skipped: ${frontendContract.skipped ? 'yes' : 'no'}`);
  writeSummary(summary);

  log('PASS cross-stack contract smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_cross_stack_contract_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
