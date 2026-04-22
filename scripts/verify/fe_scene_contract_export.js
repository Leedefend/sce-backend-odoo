#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { canonicalizeScenes } = require('./lib/scene_snapshot');
const { loadProfiles, normalizeVersion } = require('./lib/scene_schema_loader');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'admin';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'ChangeMe_123!';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const CHANNELS = new Set(['stable', 'beta', 'dev']);

function normalizeChannel(value) {
  const raw = String(value || '').trim().toLowerCase();
  return CHANNELS.has(raw) ? raw : 'stable';
}

const SCENE_CHANNEL = normalizeChannel(process.env.SCENE_CHANNEL || 'stable');
const DEFAULT_CONTRACT_OUT = `docs/contract/exports/scenes/${SCENE_CHANNEL}/LATEST.json`;
const CONTRACT_OUT = process.env.CONTRACT_OUT || DEFAULT_CONTRACT_OUT;
const CONTRACT_LATEST = process.env.CONTRACT_LATEST || DEFAULT_CONTRACT_OUT;
const INCLUDE_GENERATED_AT = process.env.INCLUDE_GENERATED_AT === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v10_0', ts);

function log(msg) {
  console.log(`[fe_scene_contract_export] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function toStringList(items) {
  if (!Array.isArray(items)) return [];
  return [...new Set(items.map((item) => String(item || '').trim()).filter(Boolean))].sort();
}

function normalizeSceneReadyTarget(entry) {
  const metaTarget = entry && entry.meta && typeof entry.meta.target === 'object' ? entry.meta.target : {};
  const page = entry && typeof entry.page === 'object' ? entry.page : {};
  const route = String(metaTarget.route || page.route || '').trim();
  const out = {};
  if (route) out.route = route;
  if (metaTarget.menu_id !== undefined && metaTarget.menu_id !== null) out.menu_id = metaTarget.menu_id;
  if (metaTarget.action_id !== undefined && metaTarget.action_id !== null) out.action_id = metaTarget.action_id;
  if (metaTarget.model !== undefined && metaTarget.model !== null) out.model = metaTarget.model;
  if (metaTarget.view_mode !== undefined && metaTarget.view_mode !== null) out.view_mode = metaTarget.view_mode;
  return out;
}

function normalizeDefaultSort(value) {
  if (typeof value === 'string') return value;
  return '';
}

function projectSceneReadyEntry(entry) {
  if (!entry || typeof entry !== 'object') return null;
  const scene = entry.scene && typeof entry.scene === 'object' ? entry.scene : {};
  const sceneKey = String(scene.key || '').trim();
  if (!sceneKey) return null;
  const listSurface = entry.list_surface && typeof entry.list_surface === 'object' ? entry.list_surface : {};
  const profile = listSurface.list_profile && typeof listSurface.list_profile === 'object' ? listSurface.list_profile : {};
  const searchSurface = entry.search_surface && typeof entry.search_surface === 'object' ? entry.search_surface : {};
  const actionSurface = entry.action_surface && typeof entry.action_surface === 'object' ? entry.action_surface : {};
  const permissionSurface = entry.permission_surface && typeof entry.permission_surface === 'object' ? entry.permission_surface : {};
  const access = {
    visible: permissionSurface.visible !== false,
    allowed: permissionSurface.allowed !== false,
    reason_code: String(permissionSurface.reason_code || (permissionSurface.allowed === false ? 'PERMISSION_DENIED' : 'OK')),
    suggested_action: String(permissionSurface.suggested_action || ''),
    required_capabilities: toStringList(permissionSurface.required_capabilities || []),
  };
  return {
    code: sceneKey,
    name: String(scene.title || scene.label || scene.name || sceneKey),
    layout: scene.layout && typeof scene.layout === 'object' ? scene.layout : {},
    access,
    target: normalizeSceneReadyTarget(entry),
    list_profile: {
      columns: Array.isArray(profile.columns) ? profile.columns : [],
      hidden_columns: Array.isArray(profile.hidden_columns) ? profile.hidden_columns : [],
      column_labels: profile.column_labels && typeof profile.column_labels === 'object' ? profile.column_labels : {},
      row_primary: String(profile.row_primary || ''),
      row_secondary: String(profile.row_secondary || ''),
    },
    default_sort: normalizeDefaultSort(listSurface.default_sort),
    filters: Array.isArray(searchSurface.filters) ? searchSurface.filters : [],
    tiles: Array.isArray(actionSurface.tiles) ? actionSurface.tiles : [],
  };
}

function resolveRuntimeScenes(data) {
  const directScenes = Array.isArray(data.scenes) ? data.scenes : [];
  if (directScenes.length > 0) {
    return { scenes: directScenes, source: 'data.scenes' };
  }
  const readyScenes = (((data.scene_ready_contract_v1 || {}).scenes) || [])
    .map(projectSceneReadyEntry)
    .filter(Boolean);
  return { scenes: readyScenes, source: 'scene_ready_contract_v1.scenes' };
}

function moveAsideIfExists(file) {
  if (!file || !fs.existsSync(file)) return null;
  const backup = `${file}.codex-export-recovery.bak`;
  if (fs.existsSync(backup)) {
    fs.unlinkSync(backup);
  }
  fs.renameSync(file, backup);
  return backup;
}

function restoreBackup(backupPath, targetPath) {
  if (!backupPath || !fs.existsSync(backupPath)) return;
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  if (fs.existsSync(targetPath)) {
    fs.unlinkSync(targetPath);
  }
  fs.renameSync(backupPath, targetPath);
}

function discardBackup(backupPath) {
  if (backupPath && fs.existsSync(backupPath)) {
    fs.unlinkSync(backupPath);
  }
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload);
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

function resolveWritePath(relPath) {
  if (path.isAbsolute(relPath)) return relPath;
  const root =
    process.env.CONTRACT_ROOT ||
    process.env.SNAPSHOT_ROOT ||
    process.cwd() ||
    '/mnt/extra-addons';
  return path.join(root, relPath);
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];
  const outPath = resolveWritePath(CONTRACT_OUT);
  const latestPath = resolveWritePath(CONTRACT_LATEST);
  const activeLatestPath = latestPath || outPath;
  let backupPath = null;

  try {
    backupPath = moveAsideIfExists(activeLatestPath);
    if (backupPath) {
      summary.push(`recovery_backup: ${backupPath}`);
    }

    let token = AUTH_TOKEN;
    if (!token && BOOTSTRAP_SECRET) {
      log('bootstrap: session.bootstrap');
      const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
      const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
        'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
        'X-Anonymous-Intent': '1',
      });
      try {
        assertIntentEnvelope(bootstrapResp, 'bootstrap', { allowMetaIntentAliases: ['session.bootstrap'] });
      } catch (_err) {
        writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
        throw new Error(`bootstrap failed: status=${bootstrapResp.status || 0}`);
      }
      token = (bootstrapResp.body.data || {}).token || '';
    }
    if (!token) {
      log(`login: ${LOGIN} db=${DB_NAME}`);
      const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
      const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
      try {
        assertIntentEnvelope(loginResp, 'login');
      } catch (_err) {
        writeJson(path.join(outDir, 'login.log'), loginResp);
        throw new Error(`login failed: status=${loginResp.status || 0}`);
      }
      token = (loginResp.body.data || {}).token || '';
      if (!token) {
        throw new Error('login response missing token');
      }
    }

    const authHeader = {
      Authorization: `Bearer ${token}`,
      'X-Odoo-DB': DB_NAME,
    };

    log('app.init');
    const initParams = { scene: 'web', with_preload: false };
    if (SCENE_CHANNEL) initParams.scene_channel = SCENE_CHANNEL;
    const initPayload = { intent: 'app.init', params: initParams };
    const initResp = await requestJson(intentUrl, initPayload, authHeader);
    writeJson(path.join(outDir, 'app_init.log'), initResp);
    assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });

    const data = initResp.body.data || {};
    const runtimeScenes = resolveRuntimeScenes(data);
    const canonical = canonicalizeScenes(runtimeScenes.scenes);
    const schemaVersion = normalizeVersion(data.schema_version || 'v1', 'v1');
    const profiles = loadProfiles(schemaVersion);

    const contract = {
      schema_version: data.schema_version || schemaVersion,
      scene_version: data.scene_version || '',
      profiles_version: profiles.version || '',
      scenes: canonical,
    };
    if (INCLUDE_GENERATED_AT) {
      contract.generated_at = new Date().toISOString();
    }

    writeJson(outPath, contract);
    if (CONTRACT_LATEST) {
      writeJson(latestPath, contract);
    }
    discardBackup(backupPath);
    backupPath = null;

    summary.push(`contract_out: ${outPath}`);
    summary.push(`contract_latest: ${latestPath}`);
    summary.push(`scene_channel: ${SCENE_CHANNEL}`);
    summary.push(`scene_source: ${runtimeScenes.source}`);
    summary.push(`scene_count: ${canonical.length}`);
    summary.push(`schema_version: ${contract.schema_version}`);
    summary.push(`scene_version: ${contract.scene_version}`);
    summary.push(`profiles_version: ${contract.profiles_version}`);
    writeSummary(summary);

    log('PASS contract export');
    log(`artifacts: ${outDir}`);
  } catch (err) {
    restoreBackup(backupPath, activeLatestPath);
    throw err;
  }
}

main().catch((err) => {
  console.error(`[fe_scene_contract_export] FAIL: ${err.message}`);
  process.exit(1);
});
