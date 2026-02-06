#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.E2E_DB || process.env.DB_NAME || process.env.DB || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const ADMIN_PASSWD = process.env.ADMIN_PASSWD || 'admin';

const now = new Date();
const ts = now.toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'portal-scene-governance-action-v10_4', ts);

function log(msg) {
  console.log(`[fe_portal_scene_governance_action_smoke] ${msg}`);
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

async function login(intentUrl, traceId) {
  const resp = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: 'admin', password: ADMIN_PASSWD } },
    { 'X-Anonymous-Intent': '1', 'X-Trace-Id': traceId }
  );
  if (resp.status >= 400 || !resp.body.ok) {
    throw new Error(`login failed: status=${resp.status}`);
  }
  const token = (resp.body.data || {}).token || '';
  if (!token) throw new Error('login token missing');
  return token;
}

function logQueryPayload(traceId) {
  return {
    intent: 'api.data',
    params: {
      op: 'list',
      model: 'sc.scene.governance.log',
      fields: ['id', 'action', 'trace_id', 'created_at'],
      domain: [['trace_id', '=', traceId], ['action', 'in', ['switch_channel', 'rollback']]],
      limit: 20,
      order: 'id desc',
    },
  };
}

async function main() {
  if (!DB_NAME) throw new Error('DB_NAME is required');
  const intentUrl = `${BASE_URL}/api/v1/intent`;
  const traceId = `scene_gov_action_${Date.now()}`;
  const summary = [];
  const token = await login(intentUrl, traceId);
  const auth = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME, 'X-Trace-Id': traceId };

  // ensure rollback flags do not force stable channel before set_channel assertion
  const resetConfigPayload = {
    intent: 'api.data',
    params: {
      op: 'list',
      model: 'ir.config_parameter',
      fields: ['id', 'key', 'value'],
      domain: [['key', 'in', ['sc.scene.rollback', 'sc.scene.use_pinned']]],
      limit: 20,
    },
  };
  const resetList = await requestJson(intentUrl, resetConfigPayload, auth);
  if (resetList.status < 400 && resetList.body.ok) {
    const cfgRows = (((resetList.body || {}).data) || {}).records || [];
    for (const row of cfgRows) {
      await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'write',
            model: 'ir.config_parameter',
            ids: [row.id],
            vals: { value: '0' },
          },
        },
        auth
      );
    }
  }

  const healthBefore = await requestJson(intentUrl, { intent: 'scene.health', params: { mode: 'summary' } }, auth);
  if (healthBefore.status >= 400 || !healthBefore.body.ok) {
    throw new Error(`scene.health before failed: ${healthBefore.status}`);
  }
  const beforeData = healthBefore.body.data || {};
  const companyId = beforeData.company_id;
  const beforeChannel = beforeData.scene_channel || 'stable';
  const targetChannel = beforeChannel === 'stable' ? 'beta' : 'stable';

  const setResp = await requestJson(
    intentUrl,
    {
      intent: 'scene.governance.set_channel',
      params: { company_id: companyId, channel: targetChannel, reason: 'phase10.4 smoke set channel' },
    },
    auth
  );
  writeJson(path.join(outDir, 'set_channel.log'), setResp);
  if (setResp.status >= 400 || !setResp.body.ok) {
    throw new Error(`set_channel failed: ${setResp.status}`);
  }
  const setData = setResp.body.data || {};
  if (setData.action !== 'set_channel') throw new Error('set_channel action mismatch');
  if (String(setData.to_channel || '') !== targetChannel) throw new Error('set_channel to_channel mismatch');

  const healthAfterSet = await requestJson(
    intentUrl,
    { intent: 'scene.health', params: { mode: 'summary', company_id: companyId } },
    auth
  );
  writeJson(path.join(outDir, 'health_after_set.log'), healthAfterSet);
  if (healthAfterSet.status >= 400 || !healthAfterSet.body.ok) {
    throw new Error(`scene.health after set failed: ${healthAfterSet.status}`);
  }
  if (String((healthAfterSet.body.data || {}).scene_channel || '') !== targetChannel) {
    throw new Error('scene_channel not updated after set_channel');
  }

  const rollbackResp = await requestJson(
    intentUrl,
    { intent: 'scene.governance.rollback', params: { reason: 'phase10.4 smoke rollback' } },
    auth
  );
  writeJson(path.join(outDir, 'rollback.log'), rollbackResp);
  if (rollbackResp.status >= 400 || !rollbackResp.body.ok) {
    throw new Error(`rollback failed: ${rollbackResp.status}`);
  }

  const healthAfterRollback = await requestJson(
    intentUrl,
    { intent: 'scene.health', params: { mode: 'summary', company_id: companyId } },
    auth
  );
  writeJson(path.join(outDir, 'health_after_rollback.log'), healthAfterRollback);
  if (healthAfterRollback.status >= 400 || !healthAfterRollback.body.ok) {
    throw new Error(`scene.health after rollback failed: ${healthAfterRollback.status}`);
  }
  const afterRollbackData = healthAfterRollback.body.data || {};
  if (!afterRollbackData.rollback_active) {
    throw new Error('rollback_active=false after rollback action');
  }

  let logsResp = await requestJson(intentUrl, logQueryPayload(traceId), auth);
  if (logsResp.status < 400 && !logsResp.body.ok) {
    const errMsg = String(((logsResp.body || {}).error || {}).message || '');
    if (errMsg.indexOf('未知模型: sc.scene.governance.log') >= 0) {
      logsResp = await requestJson(
        intentUrl,
        {
          intent: 'api.data',
          params: {
            op: 'list',
            model: 'sc.audit.log',
            fields: ['id', 'event_code', 'trace_id', 'action', 'ts'],
            domain: [['trace_id', '=', traceId], ['event_code', '=', 'SCENE_GOVERNANCE_ACTION']],
            limit: 20,
          },
        },
        auth
      );
    }
  }
  writeJson(path.join(outDir, 'governance_logs.log'), logsResp);
  if (logsResp.status >= 400 || !logsResp.body.ok) {
    throw new Error(`governance log query failed: ${logsResp.status}`);
  }
  const records = (((logsResp.body || {}).data || {}).records) || [];
  if (!Array.isArray(records)) throw new Error('governance records invalid');

  summary.push(`trace_id: ${traceId}`);
  summary.push(`company_id: ${companyId}`);
  summary.push(`channel_before: ${beforeChannel}`);
  summary.push(`channel_after_set: ${targetChannel}`);
  summary.push(`rollback_active_after: ${Boolean(afterRollbackData.rollback_active)}`);
  summary.push(`governance_log_records: ${records.length}`);
  writeSummary(summary);

  log('PASS governance action smoke');
  log(`artifacts: ${outDir}`);
}

main().catch((err) => {
  console.error(`[fe_portal_scene_governance_action_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
