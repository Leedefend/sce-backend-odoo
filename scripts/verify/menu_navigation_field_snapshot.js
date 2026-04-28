#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { requestGet, requestJson } = require('./http_smoke_utils');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

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
const REQUIRED_FIELDS = [
  'scene_key',
  'native_action_id',
  'native_model',
  'native_view_mode',
  'confidence',
  'compatibility_used',
];

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'menu-navigation-field-snapshot', ts);

function log(msg) {
  console.log(`[menu_navigation_field_snapshot] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function flattenTree(nodes) {
  const out = [];
  const visit = (items) => {
    for (const item of items || []) {
      if (!item || typeof item !== 'object') continue;
      out.push(item);
      if (Array.isArray(item.children)) visit(item.children);
    }
  };
  visit(nodes);
  return out;
}

async function waitReady(url, retries = 20, delayMs = 1500) {
  let lastErr = null;
  for (let i = 0; i < retries; i += 1) {
    try {
      const resp = await requestGet(url);
      if (resp.status) return resp.status;
    } catch (err) {
      lastErr = err;
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw lastErr || new Error('service not ready');
}

function summarizeNavigation(navResp) {
  const nav = (navResp.body || {}).nav_explained || {};
  const flat = Array.isArray(nav.flat) ? nav.flat : [];
  const treeNodes = flattenTree(Array.isArray(nav.tree) ? nav.tree : []);
  const all = [...flat, ...treeNodes];
  const missing = [];
  const invalid = [];
  const targetCounts = {};
  const confidenceCounts = {};
  const compatCounts = { true: 0, false: 0 };
  let sceneNodeCount = 0;

  all.forEach((node, index) => {
    const missingKeys = REQUIRED_FIELDS.filter((key) => !(key in node));
    if (missingKeys.length) {
      missing.push({ index, menu_id: node.menu_id, key: node.key, missing: missingKeys });
    }

    const targetType = String(node.target_type || '');
    targetCounts[targetType] = (targetCounts[targetType] || 0) + 1;

    const confidence = String(node.confidence || '');
    confidenceCounts[confidence] = (confidenceCounts[confidence] || 0) + 1;

    if (node.compatibility_used) compatCounts.true += 1;
    else compatCounts.false += 1;

    if (targetType === 'scene') {
      sceneNodeCount += 1;
      if (!node.scene_key) {
        invalid.push({ menu_id: node.menu_id, key: node.key, reason: 'scene_without_scene_key' });
      }
      if (node.compatibility_used !== false) {
        invalid.push({ menu_id: node.menu_id, key: node.key, reason: 'scene_compatibility_used_not_false' });
      }
    }

    if (['action', 'native', 'url'].includes(targetType) && node.compatibility_used !== true) {
      invalid.push({ menu_id: node.menu_id, key: node.key, reason: 'compat_target_without_compatibility_used' });
    }
  });

  const summary = {
    ok: missing.length === 0 && invalid.length === 0,
    db: DB_NAME,
    login: LOGIN,
    base_url: BASE_URL,
    status: navResp.status,
    flat_count: flat.length,
    tree_node_count: treeNodes.length,
    checked_node_count: all.length,
    scene_node_count: sceneNodeCount,
    target_type_counts: targetCounts,
    compatibility_used_counts: compatCounts,
    confidence_counts: confidenceCounts,
    missing_count: missing.length,
    invalid_count: invalid.length,
    trace_id: (((navResp.body || {}).meta || {}).trace_id || ''),
    delivery_convergence: (((navResp.body || {}).meta || {}).delivery_convergence || {}),
  };

  return { summary, missing, invalid, nav_explained: nav };
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');

  log(`api_base: ${BASE_URL}`);
  const preflight = await waitReady(BASE_URL);
  log(`preflight: ${preflight}`);

  const intentUrl = `${BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  log(`login: ${LOGIN} db=${DB_NAME}`);
  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
    { 'X-Anonymous-Intent': '1', 'X-Odoo-DB': DB_NAME }
  );
  try {
    assertIntentEnvelope(loginResp, 'login');
  } catch (_err) {
    writeJson(path.join(outDir, 'login_error.json'), { status: loginResp.status, body: loginResp.body });
    throw new Error(`login failed: status=${loginResp.status || 0}`);
  }

  const token = (((loginResp.body || {}).data || {}).token || '').toString();
  if (!token) throw new Error('login token missing');

  const navResp = await requestJson(
    `${BASE_URL}/api/menu/navigation?db=${encodeURIComponent(DB_NAME)}`,
    {},
    { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME }
  );
  if (navResp.status !== 200 || !(navResp.body || {}).ok) {
    writeJson(path.join(outDir, 'navigation_error.json'), { status: navResp.status, body: navResp.body });
    throw new Error(`navigation request failed: status=${navResp.status || 0}`);
  }

  const result = summarizeNavigation(navResp);
  result.summary.preflight_status = preflight;
  writeJson(path.join(outDir, 'summary.json'), result.summary);
  writeJson(path.join(outDir, 'nav_explained.json'), result);

  if (!result.summary.ok) {
    console.error('[menu_navigation_field_snapshot] missing:', JSON.stringify(result.missing.slice(0, 10)));
    console.error('[menu_navigation_field_snapshot] invalid:', JSON.stringify(result.invalid.slice(0, 10)));
    throw new Error(`navigation field snapshot failed: missing=${result.summary.missing_count} invalid=${result.summary.invalid_count}`);
  }

  log(`PASS checked=${result.summary.checked_node_count} scenes=${result.summary.scene_node_count} trace=${result.summary.trace_id || '-'}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[menu_navigation_field_snapshot] FAIL: ${err.message}`);
  process.exit(1);
});
