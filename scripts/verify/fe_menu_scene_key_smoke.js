#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.E2E_LOGIN || 'admin';
const PASSWORD = process.env.E2E_PASSWORD || process.env.ADMIN_PASSWD || 'admin';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const BOOTSTRAP_SECRET = process.env.BOOTSTRAP_SECRET || '';
const BOOTSTRAP_LOGIN = process.env.BOOTSTRAP_LOGIN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_8-6', ts);

const TARGETS = [
  { xmlid: 'smart_construction_demo.menu_sc_project_list_showcase', scene: 'projects.list' },
  { xmlid: 'smart_construction_core.menu_sc_project_initiation', scene: 'projects.intake' },
];

function log(msg) {
  console.log(`[fe_menu_scene_key_smoke] ${msg}`);
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

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
    });
    if (bootstrapResp.status >= 400 || !bootstrapResp.body.ok) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    log(`login: ${LOGIN} db=${DB_NAME}`);
    const loginPayload = { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } };
    const loginResp = await requestJson(intentUrl, loginPayload, { 'X-Anonymous-Intent': '1' });
    if (loginResp.status >= 400 || !loginResp.body.ok) {
      writeJson(path.join(outDir, 'login.log'), loginResp);
      throw new Error(`login failed: status=${loginResp.status}`);
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

  log('app.init (root_xmlid)');
  const initPayload = {
    intent: 'app.init',
    params: { scene: 'web', with_preload: false, root_xmlid: 'smart_construction_core.menu_sc_root' },
  };
  let initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init_root.log'), initResp);
  const initError = initResp.body && initResp.body.error ? initResp.body.error : null;
  const initMessage = initError && initError.message ? String(initError.message) : '';
  if (initResp.status === 404 && initMessage.includes('Root menu not found')) {
    log('root_xmlid not found, fallback app.init');
    const fallbackPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
    initResp = await requestJson(intentUrl, fallbackPayload, authHeader);
    writeJson(path.join(outDir, 'app_init.log'), initResp);
  }
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }

  const data = initResp.body && initResp.body.data ? initResp.body.data : {};
  const nav = data.nav || [];
  const flat = flattenNav(nav);

  const results = TARGETS.map((target) => {
    const node = flat.find((item) => {
      const meta = item && item.meta ? item.meta : {};
      return item.xmlid === target.xmlid || meta.menu_xmlid === target.xmlid;
    });
    if (!node) {
      return { target: target.xmlid, found: false, scene_key: null, xmlid: null };
    }
    return {
      target: target.xmlid,
      found: true,
      scene_key: node.scene_key || (node.meta && node.meta.scene_key) || null,
      xmlid: node.xmlid || (node.meta && node.meta.menu_xmlid) || null,
    };
  });

  results.forEach((row) => {
    summary.push(`${row.target}: found=${row.found} xmlid=${row.xmlid || '-'} scene_key=${row.scene_key || '-'}`);
  });
  writeSummary(summary);

  const missing = results.filter((row) => row.found && !row.scene_key);
  if (missing.length) {
    throw new Error(`scene_key missing for ${missing.map((row) => row.target).join(', ')}`);
  }
  const skipped = results.filter((row) => !row.found);
  if (skipped.length) {
    log(`SKIP missing menus: ${skipped.map((row) => row.target).join(', ')}`);
  }

  log('PASS menu scene_key');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_menu_scene_key_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
