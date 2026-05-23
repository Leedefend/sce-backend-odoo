#!/usr/bin/env node
'use strict';

const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_finance';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ACTION_ID = Number(process.env.INVOICE_OUTPUT_ACTION_ID || 755);

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(payload);
    const req = (u.protocol === 'https:' ? https : http).request({
      method: 'POST',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'https:' ? 443 : 80),
      path: u.pathname + u.search,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'X-Odoo-DB': DB_NAME,
        ...headers,
      },
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode || 0, body: JSON.parse(data || '{}') });
        } catch (_err) {
          resolve({ status: res.statusCode || 0, body: { raw: data } });
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function unwrap(resp, intent) {
  if (!resp || resp.status >= 400 || !resp.body || resp.body.ok !== true) {
    throw new Error(`${intent} failed status=${resp && resp.status} body=${JSON.stringify(resp && resp.body)}`);
  }
  return resp.body.data || {};
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const intentUrl = `${BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  const login = await requestJson(
    intentUrl,
    { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
    { 'X-Anonymous-Intent': '1' },
  );
  const token = unwrap(login, 'login').token;
  assert(token, 'login response missing token');
  const auth = { Authorization: `Bearer ${token}` };

  const contract = unwrap(await requestJson(intentUrl, {
    intent: 'ui.contract.v2',
    params: {
      client_type: 'web_pc',
      delivery_profile: 'full',
      op: 'action_open',
      action_id: ACTION_ID,
    },
  }, auth), 'ui.contract.v2');
  const model = contract.model
    || contract.res_model
    || (contract.action && contract.action.res_model)
    || (contract.params && contract.params.model)
    || (contract.dataContract && contract.dataContract.model);
  if (model) {
    assert(model === 'sc.receipt.invoice.line', `output invoice action model drifted: ${model}`);
  }

  const list = unwrap(await requestJson(intentUrl, {
    intent: 'api.data',
    params: {
      op: 'list',
      model: 'sc.receipt.invoice.line',
      fields: [
        'id',
        'invoice_date',
        'invoice_no',
        'invoice_issue_company',
        'invoice_party_name',
        'invoice_document_no',
        'invoice_amount',
        'surcharge_amount',
        'project_id',
        'partner_id',
      ],
      domain: [],
      context_raw: "{'search_default_group_by_project_id': 1}",
      need_total: true,
      limit: 20,
      order: 'invoice_date desc, id desc',
    },
  }, auth), 'api.data');

  assert(Number(list.total || 0) === 4454, `output invoice detail total expected 4454, got ${list.total}`);
  const rows = list.rows || list.records || [];
  assert(rows.length > 0, 'output invoice detail list returned no rows');
  for (const field of ['invoice_no', 'invoice_issue_company', 'invoice_amount']) {
    assert(rows.every((row) => row[field] !== undefined && row[field] !== null && row[field] !== ''), `visible row missing ${field}`);
  }

  console.log('[verify.invoice_output_detail.runtime_smoke] PASS');
  console.log(JSON.stringify({ action_id: ACTION_ID, total: list.total, sample_count: rows.length }));
}

main().catch((err) => {
  console.error(`[verify.invoice_output_detail.runtime_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
