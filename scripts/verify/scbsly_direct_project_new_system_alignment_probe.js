#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const ROOT = path.resolve(__dirname, '..', '..');
const MANIFEST = path.join(ROOT, 'docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json');
const OLD_EVIDENCE = path.join(ROOT, 'artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json');
const BASE_URL = process.env.FRONTEND_URL || process.env.BASE_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const AUTH_TOKEN = process.env.AUTH_TOKEN || '';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT, 'artifacts');
const OUTPUT = path.join(ARTIFACTS_DIR, 'migration', 'scbsly_direct_project_new_system_alignment_probe_v1.json');
const OUTPUT_MD = path.join(ARTIFACTS_DIR, 'migration', 'scbsly_direct_project_new_system_alignment_probe_v1.md');

const MENU_ALIASES = {
  '入库': ['入库单'],
  '材料结算单': ['材料结算'],
  '劳务结算': ['劳务结算'],
  '分包结算单': ['分包结算'],
  '机械结算单': ['设备结算', '租赁结算'],
  '租赁结算单': ['租赁结算'],
  '项目费用报销单': ['项目费用报销单', '费用报销单'],
  '管理人员工资表': ['工资登记', '工资统计表'],
  '工程结算单': ['结算单', '收入合同结算'],
  '进项上报': ['进项税额上报', '进项发票明细表'],
  '总包进项上报': ['进项税额上报', '销项发票登记'],
  '成本统计表（数据）': ['成本统计表（综合）'],
  '施工日志（新）': ['施工日志'],
};

const PREFERRED_MENU_IDS = {
  '施工合同': 655,
  '供货合同': 730,
  '库存统计表（新）': 715,
  '支付申请': 692,
  '工程进度收款': 671,
  '往来单位付款': 695,
  '进项上报': 710,
  '成本统计表（数据）': 717,
};

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, payload) {
  ensureDir(filePath);
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function requestJson(url, payload, headers = {}) {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const body = JSON.stringify(payload);
    const transport = target.protocol === 'https:' ? https : http;
    const req = transport.request({
      method: 'POST',
      hostname: target.hostname,
      port: target.port || (target.protocol === 'https:' ? 443 : 80),
      path: `${target.pathname}${target.search}`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
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

function okEnvelope(resp) {
  return resp.status >= 200 && resp.status < 300 && resp.body && resp.body.ok !== false;
}

function errorOf(resp) {
  const error = (resp.body || {}).error || {};
  return {
    status: resp.status,
    code: error.code || '',
    message: error.message || (resp.body || {}).message || '',
    reason_code: error.reason_code || (error.details || {}).reason_code || '',
  };
}

function flattenTree(nodes, parents = []) {
  const out = [];
  function visit(items) {
    for (const item of items || []) {
      if (!item || typeof item !== 'object') continue;
      const label = nodeLabel(item);
      const pathParts = label ? [...parents, label] : [...parents];
      out.push({ ...item, __path: pathParts.join('/') });
      if (Array.isArray(item.children)) flattenTree(item.children, pathParts).forEach((child) => out.push(child));
    }
  }
  visit(nodes);
  return out;
}

function labelsFromManifest() {
  const payload = readJson(MANIFEST);
  const group = (payload.user_acceptance_groups || []).find((item) => item.group_id === 'scbsly_direct_project_business_menus');
  if (!group) throw new Error('missing scbsly_direct_project_business_menus in manifest');
  const rows = [];
  for (const category of group.categories || []) {
    for (const label of category.items || []) {
      rows.push({ category: normalize(category.name), label: normalize(label) });
    }
  }
  return rows;
}

function oldEvidenceByLabel() {
  if (!fs.existsSync(OLD_EVIDENCE)) return {};
  const payload = readJson(OLD_EVIDENCE);
  const out = {};
  for (const row of payload.rows || []) {
    const label = normalize(row.label);
    out[label] = row;
  }
  return out;
}

function candidateLabels(label) {
  return [label, ...(MENU_ALIASES[label] || [])].map(normalize).filter(Boolean);
}

function nodeLabel(node) {
  return normalize(node.name || node.label || node.title);
}

function scoreNode(originalLabel, candidateLabel, node) {
  const label = nodeLabel(node);
  const pathText = normalize(node.__path);
  let score = 0;
  if (pathText.includes('用户验收') && pathText.includes('直营项目系统菜单')) score += 5000;
  if (node.menu_id === PREFERRED_MENU_IDS[originalLabel]) score += 1000;
  if (label === originalLabel) score += 200;
  if (label === candidateLabel) score += 160;
  if (label.includes(candidateLabel)) score += 40;
  if (node.is_clickable) score += 30;
  if (node.native_action_id) score += 20;
  if (node.target_type === 'action' || node.target_type === 'native') score += 10;
  return score;
}

function findNode(label, flat) {
  const labels = candidateLabels(label);
  const hits = [];
  labels.forEach((candidateLabel, index) => {
    for (const node of flat) {
      const text = nodeLabel(node);
      if (text === candidateLabel || text.includes(candidateLabel)) {
        hits.push({
          node,
          match_mode: index === 0 && text === label ? 'exact' : index === 0 ? 'contains' : 'alias',
          candidate_label: candidateLabel,
          score: scoreNode(label, candidateLabel, node),
        });
      }
    }
  });
  hits.sort((left, right) => right.score - left.score);
  return hits[0] || null;
}

function columnsFromContract(data) {
  const tree = (((data || {}).views || {}).tree || {});
  const schema = Array.isArray(tree.columns_schema) ? tree.columns_schema : [];
  const fields = Array.isArray(tree.columns) ? tree.columns.map(String) : [];
  const labels = schema.map((col) => normalize(col.label || col.string || col.name)).filter(Boolean);
  return { tree, fields, labels };
}

function hasVisibleData(records, fields) {
  return (records || []).some((record) => fields.some((field) => normalize(record[field])));
}

async function main() {
  const intentUrl = `${BASE_URL}/api/v1/intent?db=${encodeURIComponent(DB_NAME)}`;
  let token = AUTH_TOKEN;
  if (!token) {
    const loginResp = await requestJson(
      intentUrl,
      { intent: 'login', params: { db: DB_NAME, login: LOGIN, password: PASSWORD } },
      { 'X-Anonymous-Intent': '1', 'X-Odoo-DB': DB_NAME },
    );
    if (!okEnvelope(loginResp) || !(((loginResp.body || {}).data || {}).token)) {
      writeJson(OUTPUT, { status: 'FAIL', step: 'login', login: LOGIN, response: loginResp });
      throw new Error(`new system login failed: ${JSON.stringify(errorOf(loginResp))}`);
    }
    token = loginResp.body.data.token;
  }
  const headers = { Authorization: `Bearer ${token}`, 'X-Odoo-DB': DB_NAME };
  const navResp = await requestJson(`${BASE_URL}/api/menu/navigation?db=${encodeURIComponent(DB_NAME)}`, {}, headers);
  if (!okEnvelope(navResp)) {
    writeJson(OUTPUT, { status: 'FAIL', step: 'navigation', response: navResp });
    throw new Error(`new system navigation failed: ${JSON.stringify(errorOf(navResp))}`);
  }
  const nav = (navResp.body || {}).nav_explained || {};
  const flat = [
    ...(Array.isArray(nav.flat) ? nav.flat : []),
    ...flattenTree(Array.isArray(nav.tree) ? nav.tree : []),
  ];
  const oldByLabel = oldEvidenceByLabel();
  const rows = [];
  const failures = [];
  for (const item of labelsFromManifest()) {
    const match = findNode(item.label, flat);
    const old = oldByLabel[item.label] || {};
    const oldCount = old.count_probe && old.count_probe.status === 'PASS'
      ? Number(old.count_probe.data_count)
      : null;
    const row = {
      category: item.category,
      label: item.label,
      old_count: Number.isFinite(oldCount) ? oldCount : null,
      status: 'FAIL',
      failures: [],
      match_mode: match ? match.match_mode : 'missing',
      matched_label: match ? nodeLabel(match.node) : '',
      menu_id: match ? match.node.menu_id : null,
      action_id: match ? Number(match.node.native_action_id || 0) : 0,
      model: match ? normalize(match.node.native_model) : '',
      target_type: match ? normalize(match.node.target_type) : '',
      route: match ? normalize(match.node.route) : '',
      field_count: 0,
      fields: [],
      headers: [],
      new_count: null,
      sample_count: 0,
      sample_has_visible_data: false,
    };
    if (!match) {
      row.failures.push('new_menu_missing');
      rows.push(row);
      failures.push(row);
      console.log(`[scbsly-new-align] FAIL ${item.label} missing`);
      continue;
    }
    if (!row.action_id) {
      row.failures.push('new_action_or_model_missing');
      rows.push(row);
      failures.push(row);
      console.log(`[scbsly-new-align] FAIL ${item.label} no_action_or_model`);
      continue;
    }
    const contractResp = await requestJson(intentUrl, {
      intent: 'ui.contract',
      params: {
        op: 'action_open',
        action_id: row.action_id,
        menu_id: row.menu_id,
        source_mode: 'backend_internal',
      },
    }, headers);
    if (!okEnvelope(contractResp)) {
      row.failures.push(`ui_contract_failed:${JSON.stringify(errorOf(contractResp))}`);
      rows.push(row);
      failures.push(row);
      console.log(`[scbsly-new-align] FAIL ${item.label} contract`);
      continue;
    }
    const data = contractResp.body.data || {};
    const head = data.head || {};
    const resolvedModel = normalize(head.model || row.model);
    row.model = resolvedModel;
    const domain = Array.isArray(head.domain) ? head.domain : [];
    const { fields, labels } = columnsFromContract(data);
    row.model = resolvedModel || row.model;
    row.fields = fields;
    row.headers = labels;
    row.field_count = labels.length;
    if (!((head.permissions || {}).read)) row.failures.push('read_permission_false');
    if (!labels.length) row.failures.push('no_visible_list_headers');

    const countResp = await requestJson(intentUrl, {
      intent: 'api.data',
      params: { op: 'count', model: row.model, domain },
    }, headers);
    if (!okEnvelope(countResp)) {
      row.failures.push(`count_failed:${JSON.stringify(errorOf(countResp))}`);
    } else {
      row.new_count = Number((((countResp.body || {}).data || {}).total) || 0);
    }
    const dataFields = ['id', ...fields.slice(0, Math.min(fields.length, 12))];
    const listResp = await requestJson(intentUrl, {
      intent: 'api.data',
      params: { op: 'list', model: row.model, fields: dataFields, domain, limit: 3 },
    }, headers);
    if (!okEnvelope(listResp)) {
      row.failures.push(`list_failed:${JSON.stringify(errorOf(listResp))}`);
    } else {
      const records = (((listResp.body || {}).data || {}).records || []).filter(Boolean);
      row.sample_count = records.length;
      row.sample_has_visible_data = hasVisibleData(records, dataFields.filter((field) => field !== 'id'));
      if (row.new_count > 0 && !row.sample_has_visible_data) row.failures.push('sample_has_no_visible_data');
    }
    if (row.old_count !== null && row.new_count !== null && row.old_count !== row.new_count) {
      row.failures.push(`count_mismatch:${row.new_count}!=${row.old_count}`);
    }
    row.status = row.failures.length ? 'FAIL' : 'PASS';
    rows.push(row);
    if (row.status !== 'PASS') failures.push(row);
    console.log(
      `[scbsly-new-align] ${row.status} ${item.label} menu=${row.menu_id || '-'} action=${row.action_id || '-'} old=${row.old_count ?? '-'} new=${row.new_count ?? '-'} fields=${row.field_count}`,
    );
  }

  const payload = {
    status: failures.length ? 'FAIL' : 'PASS',
    generated_at: new Date().toISOString(),
    frontend_url: BASE_URL,
    db_name: DB_NAME,
    login: LOGIN,
    manifest: path.relative(ROOT, MANIFEST),
    old_evidence: fs.existsSync(OLD_EVIDENCE) ? path.relative(ROOT, OLD_EVIDENCE) : '',
    checked_count: rows.length,
    pass_count: rows.filter((row) => row.status === 'PASS').length,
    failure_count: failures.length,
    missing_menu_count: rows.filter((row) => row.failures.includes('new_menu_missing')).length,
    count_mismatch_count: rows.filter((row) => row.failures.some((failure) => failure.startsWith('count_mismatch:'))).length,
    field_failure_count: rows.filter((row) => row.failures.includes('no_visible_list_headers')).length,
    failures,
    rows,
  };
  writeJson(OUTPUT, payload);
  const lines = [
    '# SCBSLY Direct Project New System Alignment Probe v1',
    '',
    `Status: \`${payload.status}\``,
    `Frontend: \`${BASE_URL}\``,
    `DB: \`${DB_NAME}\``,
    `Generated: \`${payload.generated_at}\``,
    '',
    '| 分类 | 菜单 | 匹配菜单 | menu | action | model | 旧数 | 新数 | 字段 | 状态 |',
    '| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |',
  ];
  for (const row of rows) {
    lines.push(`| ${row.category} | ${row.label} | ${row.matched_label} | ${row.menu_id || ''} | ${row.action_id || ''} | ${row.model} | ${row.old_count ?? ''} | ${row.new_count ?? ''} | ${row.field_count} | ${row.status} |`);
  }
  lines.push('', '## Failures', '', '```json', JSON.stringify(failures, null, 2), '```', '');
  ensureDir(OUTPUT_MD);
  fs.writeFileSync(OUTPUT_MD, lines.join('\n'), 'utf8');
  console.log(`SCBSLY_DIRECT_PROJECT_NEW_SYSTEM_ALIGNMENT=${payload.status} output=${OUTPUT}`);
  if (failures.length) process.exitCode = 2;
}

main().catch((err) => {
  console.error(`[scbsly-new-align] FAIL: ${err.message}`);
  process.exit(1);
});
