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
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-auto-degrade-v10_3', ts);

function log(msg) {
  console.log(`[fe_scene_auto_degrade_smoke] ${msg}`);
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

async function main() {
  if (!DB_NAME) {
    throw new Error('DB_NAME is required (set DB_NAME or E2E_DB)');
  }
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `scene_auto_degrade_${Date.now()}`;
  const summary = [];

  let token = AUTH_TOKEN;
  if (!token && BOOTSTRAP_SECRET) {
    log('bootstrap: session.bootstrap');
    const bootstrapPayload = { intent: 'bootstrap', params: { db: DB_NAME, login: BOOTSTRAP_LOGIN } };
    const bootstrapResp = await requestJson(intentUrl, bootstrapPayload, {
      'X-Bootstrap-Secret': BOOTSTRAP_SECRET,
      'X-Anonymous-Intent': '1',
      'X-Trace-Id': traceId,
    });
    if (bootstrapResp.status >= 400 || !bootstrapResp.body.ok) {
      writeJson(path.join(outDir, 'bootstrap.log'), bootstrapResp);
      throw new Error(`bootstrap failed: status=${bootstrapResp.status}`);
    }
    token = (bootstrapResp.body.data || {}).token || '';
  }
  if (!token) {
    const candidates = [
      { login: process.env.SCENE_LOGIN || '', password: process.env.SCENE_PASSWORD || '' },
      { login: process.env.E2E_LOGIN || '', password: process.env.E2E_PASSWORD || '' },
      { login: 'admin', password: process.env.ADMIN_PASSWD || 'admin' },
      { login: LOGIN, password: PASSWORD },
    ].filter((c) => c.login && c.password);

    let lastLoginResp = null;
    for (const candidate of candidates) {
      log(`login: ${candidate.login} db=${DB_NAME}`);
      const loginPayload = {
        intent: 'login',
        params: { db: DB_NAME, login: candidate.login, password: candidate.password },
      };
      const loginResp = await requestJson(intentUrl, loginPayload, {
        'X-Anonymous-Intent': '1',
        'X-Trace-Id': traceId,
      });
      lastLoginResp = loginResp;
      if (loginResp.status < 400 && loginResp.body.ok) {
        token = (loginResp.body.data || {}).token || '';
        if (token) break;
      }
    }
    if (!token) {
      writeJson(path.join(outDir, 'login.log'), lastLoginResp || {});
      throw new Error('login failed: no usable credentials');
    }
  }

  const authHeader = {
    Authorization: `Bearer ${token}`,
    'X-Odoo-DB': DB_NAME,
    'X-Trace-Id': traceId,
  };

  log('ensure auto-degrade policy enabled');
  const policyItems = [
    ['sc.scene.auto_degrade.enabled', '1'],
    ['sc.scene.auto_degrade.critical_threshold.resolve_errors', '1'],
    ['sc.scene.auto_degrade.critical_threshold.drift_warn', '1'],
    ['sc.scene.auto_degrade.action', 'rollback_pinned'],
  ];
  for (const [key, value] of policyItems) {
    const listResp = await requestJson(
      intentUrl,
      {
        intent: 'api.data',
        params: {
          op: 'list',
          model: 'ir.config_parameter',
          fields: ['id', 'key', 'value'],
          domain: [['key', '=', key]],
          limit: 1,
        },
      },
      authHeader
    );
    if (listResp.status >= 400 || !listResp.body.ok) {
      throw new Error(`read config failed: ${key}`);
    }
    const records = (listResp.body && listResp.body.data && listResp.body.data.records) || [];
    if (Array.isArray(records) && records.length) {
      const writeResp = await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'write',
            model: 'ir.config_parameter',
            ids: [records[0].id],
            vals: { value: value },
          },
        },
        authHeader
      );
      if (writeResp.status >= 400 || !writeResp.body.ok) {
        throw new Error(`write config failed: ${key}`);
      }
    } else {
      const createResp = await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'create',
            model: 'ir.config_parameter',
            vals: { key: key, value: value },
          },
        },
        authHeader
      );
      if (createResp.status >= 400 || !createResp.body.ok) {
        throw new Error(`create config failed: ${key}`);
      }
    }
  }

  log('scene.health (inject critical error)');
  const healthResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.health',
      params: {
        scene_inject_critical_error: 1,
      },
    },
    authHeader
  );
  writeJson(path.join(outDir, 'scene_health_auto_degrade.log'), healthResp);
  if (healthResp.status >= 400 || !healthResp.body.ok) {
    throw new Error(`scene.health failed: status=${healthResp.status}`);
  }
  const health = (healthResp.body && healthResp.body.data) || {};
  const autoDegrade = health.auto_degrade || {};
  if (!autoDegrade.triggered) {
    throw new Error('auto_degrade.triggered=false');
  }
  if (!autoDegrade.action_taken || autoDegrade.action_taken === 'none') {
    throw new Error('auto_degrade.action_taken missing');
  }
  if (!health.rollback_active) {
    throw new Error('rollback_active=false');
  }
  const pre = autoDegrade.pre_counts || {};
  if ((pre.critical_resolve_errors_count || 0) < 1) {
    throw new Error('auto_degrade.pre_counts.critical_resolve_errors_count < 1');
  }

  log('query governance log');
  let logsResp = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'sc.scene.governance.log',
        fields: ['id', 'action', 'trace_id', 'created_at'],
        domain: [['action', '=', 'auto_degrade_triggered'], ['trace_id', '=', traceId]],
        limit: 5,
        order: 'id desc',
      },
    },
    authHeader
  );
  let records = (logsResp.body && logsResp.body.data && logsResp.body.data.records) || [];

  if (logsResp.status < 400 && !logsResp.body.ok) {
    const errMsg = String(((logsResp.body || {}).error || {}).message || '');
    if (errMsg.indexOf('未知模型: sc.scene.governance.log') >= 0) {
      log('fallback query sc.audit.log');
      logsResp = await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'list',
            model: 'sc.audit.log',
            fields: ['id', 'event_code', 'trace_id', 'ts'],
            domain: [['event_code', '=', 'SCENE_AUTO_DEGRADE_TRIGGERED'], ['trace_id', '=', traceId]],
            limit: 5,
            order: 'id desc',
          },
        },
        authHeader
      );
      records = (logsResp.body && logsResp.body.data && logsResp.body.data.records) || [];
    }
  }
  writeJson(path.join(outDir, 'governance_log.log'), logsResp);
  if (logsResp.status >= 400 || !logsResp.body.ok) {
    throw new Error(`api.data log query failed: status=${logsResp.status}`);
  }
  if (!Array.isArray(records) || records.length < 1) {
    throw new Error('governance log missing auto_degrade_triggered entry');
  }

  summary.push(`auto_degrade.triggered: ${Boolean(autoDegrade.triggered)}`);
  summary.push(`auto_degrade.action_taken: ${autoDegrade.action_taken}`);
  summary.push(`auto_degrade.reason_codes: ${(autoDegrade.reason_codes || []).join(',') || '-'}`);
  summary.push(`rollback_active: ${Boolean(health.rollback_active)}`);
  summary.push(`trace_id: ${health.trace_id || traceId}`);
  summary.push(`governance_log_records: ${records.length}`);
  writeSummary(summary);

  log('PASS auto degrade');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_auto_degrade_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
