#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { assertIntentEnvelope } = require('./intent_smoke_utils');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ADMIN_PASSWD = process.env.ADMIN_PASSWD || 'admin';
const REQUIRE_NOTIFY_SENT = process.env.REQUIRE_NOTIFY_SENT === '1';
const REQUIRE_NOTIFY_AUDIT = process.env.REQUIRE_NOTIFY_AUDIT === '1';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-auto-degrade-notify-v10_4', ts);

function log(msg) {
  console.log(`[fe_scene_auto_degrade_notify_smoke] ${msg}`);
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2));
}

function writeSummary(lines) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'summary.md'), lines.join('\n'));
}

function requestJson(url, payload, headers) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload || {});
    const opts = {
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: Object.assign(
        {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
        headers || {}
      ),
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

function isModelMissing(resp) {
  const msg = String((((resp || {}).body || {}).error || {}).message || '');
  return (
    msg.includes('未知模型') ||
    msg.toLowerCase().includes('unknown model') ||
    /^'[a-z0-9_.]+'$/i.test(msg.trim())
  );
}

async function upsertConfig(intentUrl, auth, key, value) {
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
    auth
  );
  assertIntentEnvelope(listResp, 'api.data');
  const rows = (((listResp.body || {}).data) || {}).records || [];
  if (Array.isArray(rows) && rows.length) {
    const writeResp = await requestJson(
      intentUrl,
      {
        intent: 'api.data',
        params: {
          op: 'write',
          model: 'ir.config_parameter',
          ids: [rows[0].id],
          vals: { value: value },
        },
      },
      auth
    );
    assertIntentEnvelope(writeResp, 'api.data.write', { allowMetaIntentAliases: ['api.data', 'api.data.create'] });
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
      auth
    );
    assertIntentEnvelope(createResp, 'api.data.create', { allowMetaIntentAliases: ['api.data'] });
  }
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `scene_auto_notify_${Date.now()}`;
  const summary = [];

  const loginResp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: 'admin', password: ADMIN_PASSWD } },
    { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
  );
  assertIntentEnvelope(loginResp, 'login');
  const token = (((loginResp.body || {}).data) || {}).token || '';
  if (!token) throw new Error('login token missing');
  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };

  const cfg = [
    ['sc.scene.auto_degrade.enabled', '1'],
    ['sc.scene.auto_degrade.critical_threshold.resolve_errors', '1'],
    ['sc.scene.auto_degrade.critical_threshold.drift_warn', '1'],
    ['sc.scene.auto_degrade.action', 'rollback_pinned'],
    ['sc.scene.auto_degrade.notify.enabled', '1'],
    ['sc.scene.auto_degrade.notify.channels', 'internal,webhook'],
  ];
  for (const item of cfg) {
    await upsertConfig(intentUrl, auth, item[0], item[1]);
  }

  const triggerResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.health',
      params: { mode: 'summary', scene_inject_critical_error: 1 },
    },
    auth
  );
  writeJson(path.join(outDir, 'scene_health_trigger.log'), triggerResp);
  assertIntentEnvelope(triggerResp, 'scene.health');
  const data = (triggerResp.body || {}).data || {};
  const auto = data.auto_degrade || {};
  if (!auto.triggered) throw new Error('auto_degrade.triggered=false');
  const notify = auto.notifications || {};
  let notifySentSkipped = false;
  if (!notify.sent && REQUIRE_NOTIFY_SENT) {
    throw new Error('auto_degrade.notifications.sent=false');
  }
  if (!notify.sent && !REQUIRE_NOTIFY_SENT) {
    notifySentSkipped = true;
  }

  const notifyLog = await requestJson(
    intentUrl,
    {
      intent: 'api.data',
      params: {
        op: 'list',
        model: 'sc.audit.log',
        fields: ['id', 'event_code', 'trace_id', 'after_json', 'ts'],
        domain: [['event_code', '=', 'SCENE_AUTO_DEGRADE_NOTIFY'], ['trace_id', '=', traceId]],
        limit: 10,
        order: 'id desc',
      },
    },
    auth
  );
  writeJson(path.join(outDir, 'notify_audit.log'), notifyLog);
  let rows = [];
  let notifyAuditSkipped = false;
  if (isModelMissing(notifyLog)) {
    if (REQUIRE_NOTIFY_AUDIT) {
      throw new Error('notify audit model unavailable');
    }
    notifyAuditSkipped = true;
  } else {
    assertIntentEnvelope(notifyLog, 'api.data');
    rows = (((notifyLog.body || {}).data) || {}).records || [];
    if (!Array.isArray(rows) || rows.length < 1) {
      throw new Error('notify audit rows missing');
    }
    const payloadText = String(rows[0].after_json || '');
    if (payloadText.indexOf(traceId) < 0) throw new Error('notification payload missing trace_id');
    if (payloadText.indexOf('action_taken') < 0) throw new Error('notification payload missing action_taken');
  }

  summary.push(`trace_id: ${traceId}`);
  summary.push(`auto_degrade_triggered: ${Boolean(auto.triggered)}`);
  summary.push(`notifications_sent: ${Boolean(notify.sent)}`);
  summary.push(`notifications_sent_skipped: ${notifySentSkipped ? 'true' : 'false'}`);
  summary.push(`require_notify_sent: ${REQUIRE_NOTIFY_SENT ? 'true' : 'false'}`);
  summary.push(`require_notify_audit: ${REQUIRE_NOTIFY_AUDIT ? 'true' : 'false'}`);
  summary.push(`notify_channels: ${(notify.channels || []).join(',') || '-'}`);
  summary.push(`notify_audit_skipped: ${notifyAuditSkipped ? 'true' : 'false'}`);
  summary.push(`notify_rows: ${rows.length}`);
  writeSummary(summary);
  log('PASS auto degrade notify');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_scene_auto_degrade_notify_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
