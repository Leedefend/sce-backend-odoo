#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const LOGIN = process.env.SCENE_LOGIN || process.env.SVC_LOGIN || process.env.E2E_LOGIN || 'svc_project_ro';
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

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-shell-v0_9-6', ts);

function log(msg) {
  console.log(`[fe_scene_schema_smoke] ${msg}`);
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

function findSchemaPath(relPath) {
  const roots = [
    process.env.SCENE_SCHEMA_ROOT,
    '/mnt/odoo',
    '/mnt/extra-addons',
    '/mnt/addons_external',
    '/mnt/e/sc-backend-odoo',
  ].filter(Boolean);
  const stripped = relPath.startsWith('addons/') ? relPath.slice('addons/'.length) : relPath;
  const relPaths = [relPath, stripped];
  for (const root of roots) {
    for (const rel of relPaths) {
      const candidate = path.join(root, rel);
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  return '';
}

function loadJson(relPath) {
  const filePath = findSchemaPath(relPath);
  if (!filePath) {
    throw new Error(`schema file not found: ${relPath}`);
  }
  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function assertType(value, type) {
  if (type === 'array') return Array.isArray(value);
  if (type === 'object') return isObject(value);
  if (type === 'number') return typeof value === 'number' && !Number.isNaN(value);
  return typeof value === type;
}

function validateFields(obj, fields, prefix) {
  const errors = [];
  Object.entries(fields || {}).forEach(([key, spec]) => {
    const value = obj[key];
    const required = spec.required === true;
    if (value === undefined || value === null) {
      if (required) errors.push(`${prefix}${key} missing`);
      return;
    }
    if (spec.type && !assertType(value, spec.type)) {
      errors.push(`${prefix}${key} expected ${spec.type}`);
      return;
    }
    if (spec.fields && isObject(value)) {
      errors.push(...validateFields(value, spec.fields, `${prefix}${key}.`));
    }
    if (spec.item_fields && Array.isArray(value)) {
      value.forEach((item, idx) => {
        if (!isObject(item)) {
          errors.push(`${prefix}${key}[${idx}] expected object`);
          return;
        }
        errors.push(...validateFields(item, spec.item_fields, `${prefix}${key}[${idx}].`));
      });
    }
    if (spec.at_least_one && isObject(value)) {
      const ok = spec.at_least_one.some((field) => value[field] !== undefined && value[field] !== null);
      if (!ok) {
        errors.push(`${prefix}${key} missing any of ${spec.at_least_one.join(',')}`);
      }
    }
  });
  return errors;
}

function validateScene(scene, schema, profile) {
  const errors = [];
  const required = schema.required || [];
  required.forEach((key) => {
    if (scene[key] === undefined || scene[key] === null) {
      errors.push(`${key} missing`);
    }
  });
  errors.push(...validateFields(scene, schema.fields, ''));

  const profileRequired = (profile && profile.required) || [];
  profileRequired.forEach((key) => {
    if (scene[key] === undefined || scene[key] === null) {
      errors.push(`profile requires ${key}`);
    }
  });

  const lpProfile = (profile && profile.list_profile) || {};
  if (scene.list_profile && lpProfile.required) {
    lpProfile.required.forEach((key) => {
      if (scene.list_profile[key] === undefined || scene.list_profile[key] === null) {
        errors.push(`list_profile.${key} missing`);
      }
    });
  }
  if (scene.list_profile && Array.isArray(lpProfile.hidden_columns_must_include)) {
    const hidden = scene.list_profile.hidden_columns || [];
    lpProfile.hidden_columns_must_include.forEach((field) => {
      if (!hidden.includes(field)) {
        errors.push(`hidden_columns missing ${field}`);
      }
    });
  }

  return errors;
}

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }

  const schema = loadJson('addons/smart_construction_scene/schema/scene_schema_v1.json');
  const profiles = loadJson('addons/smart_construction_scene/schema/scene_profiles_v1.json');
  const profilesMap = (profiles || {}).scenes || {};

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

  log('app.init');
  const initPayload = { intent: 'app.init', params: { scene: 'web', with_preload: false } };
  const initResp = await requestJson(intentUrl, initPayload, authHeader);
  writeJson(path.join(outDir, 'app_init.log'), initResp);
  if (initResp.status >= 400 || !initResp.body.ok) {
    throw new Error(`app.init failed: status=${initResp.status}`);
  }

  const data = initResp.body.data || {};
  const scenes = Array.isArray(data.scenes) ? data.scenes : [];
  const getScene = (key) => scenes.find((item) => item && (item.code === key || item.key === key));

  const targets = ['projects.list', 'projects.ledger'];
  const errors = [];
  const profileErrors = [];

  for (const key of targets) {
    const scene = getScene(key);
    if (!scene) {
      errors.push(`scene ${key} missing`);
      continue;
    }
    const profile = profilesMap[key] || {};
    const sceneErrors = validateScene(scene, schema, profile);
    if (sceneErrors.length) {
      profileErrors.push(`${key}: ${sceneErrors.join('; ')}`);
    }
  }

  summary.push(`scene_count: ${scenes.length}`);
  summary.push(`schema_version: ${schema.version || '-'}`);
  summary.push(`profiles_version: ${profiles.version || '-'}`);
  summary.push(`errors: ${errors.length}`);
  summary.push(`profile_errors: ${profileErrors.length}`);
  writeSummary(summary);

  if (errors.length) {
    throw new Error(errors.join(' | '));
  }
  if (profileErrors.length) {
    throw new Error(profileErrors.join(' | '));
  }

  log('PASS schema');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_schema_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
