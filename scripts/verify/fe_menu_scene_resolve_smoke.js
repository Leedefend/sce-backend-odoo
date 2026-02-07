#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.API_BASE || process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'svc_e2e_smoke';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const EXEMPTIONS_FILE =
  process.env.MENU_SCENE_EXEMPTIONS || path.resolve(__dirname, '../../docs/ops/verify/menu_scene_exemptions.yml');

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-menu-scene-resolve', ts);

function log(msg) {
  console.log(`[fe_menu_scene_resolve_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function loadExemptions(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return { items: [], map: new Map() };
  }
  const lines = fs.readFileSync(filePath, 'utf-8').split(/\r?\n/);
  const items = [];
  let current = null;
  const pushCurrent = () => {
    if (current && current.xmlid) {
      items.push(current);
    }
    current = null;
  };
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    if (line.startsWith('- ')) {
      pushCurrent();
      current = {};
      const rest = line.slice(2).trim();
      if (rest.startsWith('xmlid:')) {
        current.xmlid = rest.slice('xmlid:'.length).trim().replace(/^['"]|['"]$/g, '');
      }
      continue;
    }
    if (line.startsWith('xmlid:')) {
      if (!current) current = {};
      current.xmlid = line.slice('xmlid:'.length).trim().replace(/^['"]|['"]$/g, '');
      continue;
    }
    if (line.startsWith('reason:')) {
      if (!current) current = {};
      current.reason = line.slice('reason:'.length).trim();
    }
  }
  pushCurrent();
  const map = new Map();
  for (const item of items) {
    map.set(item.xmlid, item.reason || '');
  }
  return { items, map };
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

function flattenNav(nodes) {
  const out = [];
  const walk = (items) => {
    for (const item of items || []) {
      out.push(item);
      if (item.children && item.children.length) {
        walk(item.children);
      }
    }
  };
  walk(nodes);
  return out;
}

function hasAction(meta) {
  if (!meta || typeof meta !== 'object') return false;
  return Boolean(meta.action_id || meta.action_xmlid || meta.action_type || meta.action_tag);
}

function preflightUrl(url) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const opts = {
      method: 'GET',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname || '/',
    };
    const client = u.protocol === 'https:' ? https : http;
    const req = client.request(opts, (res) => {
      res.resume();
      resolve(res.statusCode || 0);
    });
    req.on('error', reject);
    req.end();
  });
}

async function preflightWithRetry(url, retries = 8, delayMs = 2000) {
  let lastErr = null;
  for (let i = 0; i < retries; i += 1) {
    try {
      const status = await preflightUrl(url);
      return status;
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastErr;
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');

  log(`api_base: ${BASE_URL}`);
  try {
    const status = await preflightWithRetry(BASE_URL);
    log(`preflight: ${status}`);
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    console.error(`[fe_menu_scene_resolve_smoke] PRECHECK FAIL: ${msg}`);
    console.error('[fe_menu_scene_resolve_smoke] HINT: verify API base URL and service reachability.');
    console.error('[fe_menu_scene_resolve_smoke] HINT: host mode uses http://localhost:8070; container mode should use http://localhost:8069 or service name.');
    process.exit(1);
  }

  const intentUrl = `${BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, {
    'X-Anonymous-Intent': '1',
    'X-Odoo-DB': DB_NAME,
  });
  if (loginResp.status >= 400 || !loginResp.body.ok) {
    console.error('[fe_menu_scene_resolve_smoke] login error body:', JSON.stringify(loginResp.body));
    throw new Error(`login failed: status=${loginResp.status}`);
  }
  const token = (loginResp.body.data || {}).token || '';
  if (!token) throw new Error('login token missing');

  const appInitResp = await requestJson(
    intentUrl,
    { intent: 'app.init', params: { scene: 'web', with_preload: false } },
    { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME }
  );
  if (appInitResp.status >= 400 || !appInitResp.body.ok) {
    console.error('[fe_menu_scene_resolve_smoke] app.init error body:', JSON.stringify(appInitResp.body));
    throw new Error(`app.init failed: ${appInitResp.status}`);
  }

  const nav = ((appInitResp.body || {}).data || {}).nav || [];
  const all = flattenNav(nav);
  const failures = [];
  const exempt = [];
  const exemptions = loadExemptions(EXEMPTIONS_FILE);
  if (exemptions.items.length) {
    log(`exemptions: ${exemptions.items.length} from ${EXEMPTIONS_FILE}`);
  }
  let total = 0;

  for (const node of all) {
    const meta = node.meta || {};
    if (!hasAction(meta)) {
      continue;
    }
    total += 1;
    const sceneKey = node.scene_key || meta.scene_key || meta.sceneKey || node.sceneKey;
    if (!sceneKey) {
      const xmlid = node.xmlid || meta.menu_xmlid;
      if (xmlid && exemptions.map.has(xmlid)) {
        exempt.push({
          name: node.name,
          menu_id: node.menu_id || node.id,
          xmlid,
          reason: exemptions.map.get(xmlid),
          action_type: meta.action_type || meta.actionType,
          action_id: meta.action_id || null,
        });
      } else {
        failures.push({
          name: node.name,
          menu_id: node.menu_id || node.id,
          xmlid,
          action_type: meta.action_type || meta.actionType,
          action_id: meta.action_id || null,
          menu_xmlid: meta.menu_xmlid || null,
          scene_key: node.scene_key || null,
          meta_scene_key: meta.scene_key || null,
        });
      }
    }
  }

  const resolved = total - failures.length - exempt.length;
  const effectiveTotal = Math.max(total - exempt.length, 0);
  const coverage = effectiveTotal ? Number(((resolved / effectiveTotal) * 100).toFixed(2)) : 100;
  const summary = {
    total,
    resolved,
    failures: failures.length,
    exempt: exempt.length,
    effective_total: effectiveTotal,
    coverage,
  };
  writeJson(path.join(outDir, 'menu_scene_resolve.json'), { summary, failures, exempt });

  if (failures.length) {
    console.error('[fe_menu_scene_resolve_smoke] unresolved menus:');
    for (const item of failures) {
      console.error(`- ${item.name || 'N/A'} menu_id=${item.menu_id || 'N/A'} xmlid=${item.xmlid || 'N/A'} action_type=${item.action_type || 'N/A'} action_id=${item.action_id || 'N/A'}`);
    }
    throw new Error(`menu scene resolve failures: ${failures.length}`);
  }

  log(`PASS menu scene resolve (coverage ${coverage}%)`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_menu_scene_resolve_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
