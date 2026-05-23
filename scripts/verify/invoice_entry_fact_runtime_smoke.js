#!/usr/bin/env node
'use strict';

const http = require('http');
const https = require('https');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8070';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'demo_role_finance';
const PASSWORD = process.env.E2E_PASSWORD || 'demo';
const ACTION_ID = Number(process.env.INVOICE_LEDGER_ACTION_ID || 630);

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
    throw new Error(`${intent} failed status=${resp && resp.status}`);
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

  const contract = await requestJson(intentUrl, {
    intent: 'ui.contract.v2',
    params: {
      client_type: 'web_pc',
      delivery_profile: 'full',
      op: 'action_open',
      action_id: ACTION_ID,
    },
  }, auth);
  const contractData = unwrap(contract, 'ui.contract.v2');
  const dataContract = contractData.dataContract || {};
  const search = dataContract.search || contractData.searchContract || {};
  const groupFields = (search.group_by || []).map((row) => row && row.field).filter(Boolean);
  for (const field of ['source_kind', 'direction', 'invoice_type', 'tax_rate', 'cost_category_name']) {
    assert(groupFields.includes(field), `invoice contract group_by missing ${field}`);
  }
  const sourceKindGroup = (search.group_by || []).find((row) => row && row.field === 'source_kind');
  assert(sourceKindGroup && sourceKindGroup.default === true, 'invoice total ledger must default group by source_kind');

  const list = await requestJson(intentUrl, {
    intent: 'api.data',
    params: {
      op: 'list',
      model: 'sc.invoice.registration',
      fields: [
        'id',
        'name',
        'source_kind',
        'direction',
        'state',
        'invoice_no',
        'invoice_code',
        'invoice_type',
        'tax_rate',
        'amount_total',
        'tax_amount',
        'project_id',
        'partner_id',
        'legacy_source_model',
      ],
      domain: [],
      context_raw: "{'search_default_group_source_kind': 1}",
      group_by: 'source_kind',
      need_total: true,
      need_group_total: true,
      group_limit: 20,
      group_sample_limit: 3,
      group_page_size: 3,
      limit: 20,
      order: 'invoice_date desc, id desc',
    },
  }, auth);
  const listData = unwrap(list, 'api.data');
  const groups = listData.group_summary || [];
  const labels = new Set(groups.map((row) => String(row.label || '')));
  for (const label of ['发票登记', '进项税额', '销项税额', '预缴税']) {
    assert(labels.has(label), `source kind group missing ${label}`);
  }
  assert(Number(listData.total || 0) > 0, 'invoice ledger should return records');
  assert((listData.grouped_rows || []).every((row) => (row.sample_rows || []).length > 0), 'each invoice source group should expose sample rows');

  console.log('[verify.invoice_entry_fact.runtime_smoke] PASS');
  console.log(JSON.stringify({
    total: listData.total,
    groups: groups.map((row) => ({ label: row.label, count: row.count })),
  }));
}

main().catch((err) => {
  console.error(`[verify.invoice_entry_fact.runtime_smoke] FAIL: ${err.message}`);
  process.exit(1);
});
