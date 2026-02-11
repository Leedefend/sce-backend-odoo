#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { requestJson } = require('./http_smoke_utils');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-warnings', ts);

function log(msg) {
  console.log(`[act_url_missing_scene_report] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const intentUrl = `${BASE_URL}/api/v1/intent`;

  const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
  const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
  assertIntentEnvelope(loginResp, 'login');
  const token = (loginResp.body.data || {}).token || '';
  if (!token) throw new Error('login token missing');

  const authHeader = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const initPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  assertIntentEnvelope(initResp, 'app.init', { allowMetaIntentAliases: ['system.init'] });

  const diag = (initResp.body.data || {}).scene_diagnostics || {};
  const warnings = Array.isArray(diag.normalize_warnings) ? diag.normalize_warnings : [];
  const missing = warnings.filter((w) => w && w.code === 'ACT_URL_MISSING_SCENE');

  const report = missing.map((w) => ({
    menu_xmlid: w.menu_xmlid || '',
    action_xmlid: w.action_xmlid || '',
    scene_key: w.scene_key || '',
    reason: w.reason || '',
    message: w.message || '',
    fix_hint: 'Add menu/action mapping in smart_core.handlers.system_init._apply_scene_keys',
  }));

  writeJson(path.join(outDir, 'act_url_missing_scene_report.json'), report);
  log(`missing: ${report.length}`);
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[act_url_missing_scene_report] FAIL: ${err.message}`);
  process.exit(1);
});
