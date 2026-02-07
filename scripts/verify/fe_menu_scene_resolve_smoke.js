#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.API_BASE || process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'demo_pm';
const PASSWORD =
  process.env.SCENE_PASSWORD ||
  process.env.SVC_PASSWORD ||
  process.env.E2E_PASSWORD ||
  process.env.ADMIN_PASSWD ||
  'demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

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

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
  if (loginResp.status >= 400 || !loginResp.body.ok) throw new Error(`login failed: status=${loginResp.status}`);
  const token = (loginResp.body.data || {}).token || '';
  if (!token) throw new Error('login token missing');

  const appInitResp = await requestJson(
    intentUrl,
    { intent: 'app.init', params: { scene: 'web', with_preload: false } },
    { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME }
  );
  if (appInitResp.status >= 400 || !appInitResp.body.ok) throw new Error(`app.init failed: ${appInitResp.status}`);

  const nav = ((appInitResp.body || {}).data || {}).nav || [];
  const all = flattenNav(nav);
  const failures = [];

  for (const node of all) {
    const meta = node.meta || {};
    if (!hasAction(meta)) {
      continue;
    }
    const sceneKey = node.scene_key || meta.scene_key || meta.sceneKey || node.sceneKey;
    if (!sceneKey) {
      failures.push({
        name: node.name,
        menu_id: node.menu_id || node.id,
        xmlid: node.xmlid || meta.menu_xmlid,
        action_type: meta.action_type || meta.actionType,
        action_id: meta.action_id || null,
        menu_xmlid: meta.menu_xmlid || null,
        scene_key: node.scene_key || null,
        meta_scene_key: meta.scene_key || null,
      });
    }
  }

  writeJson(path.join(outDir, 'menu_scene_resolve.json'), { total: all.length, failures });

  if (failures.length) {
    console.error('[fe_menu_scene_resolve_smoke] unresolved menus:');
    for (const item of failures) {
      console.error(`- ${item.name || 'N/A'} menu_id=${item.menu_id || 'N/A'} xmlid=${item.xmlid || 'N/A'} action_type=${item.action_type || 'N/A'} action_id=${item.action_id || 'N/A'}`);
    }
    throw new Error(`menu scene resolve failures: ${failures.length}`);
  }

  log('PASS menu scene resolve');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_menu_scene_resolve_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
