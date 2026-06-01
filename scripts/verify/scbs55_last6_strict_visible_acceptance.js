#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');

const ROOT = process.cwd();
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MANIFEST_PATH = process.env.SCBS55_ACCEPTANCE_MANIFEST
  || path.join(ROOT, 'docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json');
const EVIDENCE_LOCK_PATH = process.env.SCBS55_ACCEPTANCE_EVIDENCE_LOCK
  || path.join(ROOT, 'docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json');
const OLD_ROWS_DIR = process.env.SCBS55_OLD_ROWS_DIR || '/tmp/scbs55_old_pages_20260530';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT, 'artifacts/migration');
const OUT_JSON = path.join(ARTIFACTS_DIR, 'scbs55_last6_strict_visible_acceptance_v1.json');
const OUT_MD = path.join(ARTIFACTS_DIR, 'scbs55_last6_strict_visible_acceptance_v1.md');
const SUPPLIER_ATTACHMENT_DISPLAY_LOCK = process.env.SCBS55_SUPPLIER_ATTACHMENT_DISPLAY_LOCK
  || path.join(ARTIFACTS_DIR, 'scbs55_supplier_contract_attachment_display_lock_v1.json');
const TARGET_KEYS = new Set([
  'self_guarantee',
  'self_guarantee_refund',
  'self_funding_income',
  'self_funding_refund',
  'engineering_progress_receipt',
  'supplier_contract',
]);
const HELPER_HEADERS = new Set(['', '序号', '列', '操作', 'Actions']);
const SUPPLIER_CONTRACT_VALUE_FIELDS = [
  'document_state_label',
  'contract_no',
  'project_name',
  'document_no',
  'partner_name',
  'settlement_amount',
  'original_contract_holder',
  'pricing_method_text',
  'contract_type_text',
  'title',
  'amount_total',
  'paid_amount',
  'unpaid_amount',
  'attachment_text',
  'creator_name',
  'sign_date',
];
const SUPPLIER_CONTRACT_OLD_VALUE_MAP = [
  ['单据状态', 'DJZT', 'document_state_label', 'state'],
  ['合同编号', 'f_HTBH', 'contract_no', 'text'],
  ['项目名称', 'ProjectName', 'project_name', 'text'],
  ['自编合同号', 'DJBH', 'document_no', 'text'],
  ['供应商', 'f_GYSName', 'partner_name', 'text'],
  ['结算金额', 'HTJSJE', 'settlement_amount', 'number'],
  ['合同原件', 'D_SCBSJS_HTYJSZD', 'original_contract_holder', 'text'],
  ['计价方式', 'JJFSTEXT', 'pricing_method_text', 'text'],
  ['合同类型', 'HTLX_New', 'contract_type_text', 'text'],
  ['标题', 'BT', 'title', 'text'],
  ['总金额', 'ZJE', 'amount_total', 'number'],
  ['已付款金额', 'YFKJE', 'paid_amount', 'number'],
  ['未付款金额', 'WFKJE', 'unpaid_amount', 'number'],
  ['附件', 'f_FJ_FJ', 'attachment_text', 'text'],
  ['录入人', 'f_LRR', 'creator_name', 'text'],
  ['签约日期', 'f_QYRQ', 'sign_date', 'date'],
];
const VALUE_COMPARE_SKIP_LABELS = new Set(['新系统承载模型']);
const NEW_VISIBLE_FIELD_MAP = {
  self_funding_income: {
    单据状态: 'document_state_label',
    单据编号: 'document_no',
    推送结果: 'push_result',
    金蝶单据编号: 'kingdee_document_no',
    单据日期: 'document_date',
    项目名称: 'project_name',
    往来单位: 'partner_name',
    自筹收入金额: 'self_funding_amount',
    收入类别: 'income_category',
    账户: 'account_name',
    自筹退回金额: 'refund_amount',
    自筹未退金额: 'unreturned_amount',
    标题: 'title',
    是否需要退回: 'need_refund',
    附件: 'attachment_text',
    录入人: 'entry_user',
    录入时间: 'entry_time',
  },
  self_funding_refund: {
    单据状态: 'document_state_label',
    推送结果: 'push_result',
    单据日期: 'document_date',
    单据编号: 'document_no',
    项目名称: 'project_name',
    自筹退回金额: 'refund_amount',
    往来单位: 'partner_name',
    备注: 'note',
    附件: 'attachment_text',
    录入人: 'entry_user',
    录入时间: 'entry_time',
  },
  engineering_progress_receipt: {
    申请日期: 'document_date',
    单据编号: 'document_no',
    项目: 'project_name',
    历史项目名称: 'project_name',
    往来单位: 'partner_name',
    历史往来单位: 'partner_name',
    收款金额: 'amount',
    收款类型: 'receipt_type',
    收入类别: 'income_category',
    状态: 'state_label',
    历史录入人: 'creator_name',
    历史录入时间: 'created_time',
    旧库记录: 'legacy_record_id',
  },
  supplier_contract: {
    单据状态: 'document_state_label',
    合同编号: 'contract_no',
    项目名称: 'project_name',
    自编合同号: 'document_no',
    供应商: 'partner_name',
    结算金额: 'settlement_amount',
    合同原件: 'original_contract_holder',
    计价方式: 'pricing_method_text',
    合同类型: 'contract_type_text',
    标题: 'title',
    总金额: 'amount_total',
    已付款金额: 'paid_amount',
    未付款金额: 'unpaid_amount',
    附件: 'attachment_text',
    录入人: 'creator_name',
    签约日期: 'sign_date',
  },
};

function aliasFieldName(label) {
  return `p1_visible_${crypto.createHash('sha1').update(label).digest('hex').slice(0, 12)}`;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function loadSupplierAttachmentDisplayById() {
  if (!fs.existsSync(SUPPLIER_ATTACHMENT_DISPLAY_LOCK)) return new Map();
  const payload = readJson(SUPPLIER_ATTACHMENT_DISPLAY_LOCK);
  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  return new Map(rows
    .map((row) => [normalize(row?.Id), normalize(row?.f_FJ_FJ)])
    .filter(([id]) => id));
}

function normalize(value) {
  if (value === null || value === undefined || value === false) return '';
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function sha256File(filePath) {
  const digest = crypto.createHash('sha256');
  digest.update(fs.readFileSync(filePath));
  return digest.digest('hex');
}

function identityValue(row, fieldName) {
  if (!row || typeof row !== 'object') return '';
  if (Object.prototype.hasOwnProperty.call(row, fieldName)) return normalize(row[fieldName]);
  const wanted = String(fieldName || '').toLowerCase();
  const key = Object.keys(row).find((candidate) => candidate.toLowerCase() === wanted);
  return key ? normalize(row[key]) : '';
}

function normalizeNumber(value) {
  const text = normalize(value).replace(/,/g, '');
  if (!text) return '0.00';
  const parsed = Number(text);
  if (!Number.isFinite(parsed)) return text;
  return parsed.toFixed(2);
}

function normalizeDate(value) {
  const text = normalize(value);
  return text ? text.slice(0, 10) : '';
}

function stateLabel(value) {
  const text = normalize(value);
  return {
    0: '未审核',
    1: '审核中',
    2: '已审核',
    '-1': '已驳回',
  }[text] || text;
}

function auditStateLabel(value) {
  const text = normalize(value);
  return {
    '-1': '已作废',
    0: '未审核',
    1: '审核中',
    2: '审核通过',
    3: '已驳回',
    4: '已作废',
  }[text] || text;
}

function firstValue(row, fields) {
  for (const field of fields) {
    const value = identityValue(row, field);
    if (value) return value;
  }
  return '';
}

function oldAmountText(value) {
  const text = normalize(value).replace(/,/g, '');
  if (!text) return '';
  const parsed = Number(text);
  if (!Number.isFinite(parsed)) return text;
  return String(parsed);
}

function attachmentText(row) {
  return firstValue(row, ['f_FJ', 'FJ', 'f_FJ_FJ']);
}

function selfFundingIncomeUnreturned(row) {
  const selfAmount = Number(normalize(row.f_JE).replace(/,/g, '')) || 0;
  const refundAmount = Number(normalize(row.THJE || row.CZJE).replace(/,/g, '')) || 0;
  const receivable = normalize(row.YSJE);
  if (receivable) {
    const base = Number(receivable.replace(/,/g, '')) || 0;
    return oldAmountText(base - refundAmount);
  }
  return oldAmountText(selfAmount - refundAmount);
}

function oldVisibleValue(surfaceKey, label, row, attachmentDisplayById = new Map()) {
  if (surfaceKey === 'self_guarantee') {
    const values = {
      状态: auditStateLabel(row.DJZT),
      单据编号: identityValue(row, 'DJBH'),
      投标项目名称: identityValue(row, 'TBXMMC'),
      项目名称: identityValue(row, 'XMMC'),
      所属公司: identityValue(row, 'SSGS'),
      金额: oldAmountText(row.JE),
      已退保证金金额: oldAmountText(row.YTBZJJE),
      转款单位: identityValue(row, 'DW'),
      汇款方式: identityValue(row, 'HKFS'),
      保证金类型: firstValue(row, ['BZJLX', 'Y_BZJLX']),
      收款账户: identityValue(row, 'SKZH'),
      收款账户名称: identityValue(row, 'SKZHMC'),
      备注: firstValue(row, ['BZ', 'Y_BZ', 'SM']),
      附件: attachmentText(row),
      录入人: identityValue(row, 'LRR'),
      录入时间: identityValue(row, 'LRSJ'),
    };
    return values[label] ?? '';
  }
  if (surfaceKey === 'self_guarantee_refund') {
    const values = {
      状态: auditStateLabel(row.DJZT),
      收保证金单号: identityValue(row, 'SBZJDH'),
      单据编号: identityValue(row, 'DJBH'),
      项目名称: identityValue(row, 'XMMC'),
      投标项目名称: identityValue(row, 'TBXMMC'),
      退还金额: oldAmountText(row.THJE),
      备注: firstValue(row, ['BZ', 'Y_BZ', 'SM']),
      退还账号: identityValue(row, 'THKHHZH'),
      退还开户行: identityValue(row, 'THKHH'),
      单位: identityValue(row, 'DW'),
      收款开户行: identityValue(row, 'SKKHH'),
      收款账号: identityValue(row, 'SKZH'),
      录入人: identityValue(row, 'LRR'),
      录入时间: identityValue(row, 'LRSJ'),
      附件: attachmentText(row),
    };
    return values[label] ?? '';
  }
  if (surfaceKey === 'self_funding_income') {
    const values = {
      单据状态: stateLabel(row.DJZTText || row.DJZT),
      单据编号: identityValue(row, 'DJBH'),
      推送结果: firstValue(row, ['TSJG', 'D_SCBSJS_IsPush']),
      金蝶单据编号: identityValue(row, 'OTHER_SYSTEM_CODE'),
      单据日期: identityValue(row, 'f_RQ'),
      项目名称: identityValue(row, 'XMMC'),
      往来单位: identityValue(row, 'WLDWMC'),
      自筹收入金额: oldAmountText(row.f_JE),
      收入类别: identityValue(row, 'f_SRLBName'),
      账户: identityValue(row, 'SKZH'),
      自筹退回金额: oldAmountText(row.THJE || row.CZJE),
      自筹未退金额: selfFundingIncomeUnreturned(row),
      标题: identityValue(row, 'BT'),
      是否需要退回: firstValue(row, ['SFTH', 'SFXYTHID']),
      附件: attachmentText(row),
      录入人: identityValue(row, 'LRR'),
      录入时间: identityValue(row, 'LRSJ'),
    };
    return values[label] ?? '';
  }
  if (surfaceKey === 'self_funding_refund') {
    const values = {
      单据状态: stateLabel(row.DJZTText || row.DJZT),
      推送结果: firstValue(row, ['TSJG', 'D_SCBSJS_IsPush']),
      单据日期: firstValue(row, ['DJRQ', 'f_RQ']),
      单据编号: identityValue(row, 'DJBH'),
      项目名称: identityValue(row, 'XMMC'),
      自筹退回金额: oldAmountText(row.THJE || row.f_JE),
      往来单位: firstValue(row, ['WLDWFKDW', 'XMJLMC', 'WLDWMC']),
      备注: firstValue(row, ['BZ', 'f_BZ']),
      附件: attachmentText(row),
      录入人: identityValue(row, 'LRR'),
      录入时间: identityValue(row, 'LRSJ'),
    };
    return values[label] ?? '';
  }
  if (surfaceKey === 'engineering_progress_receipt') {
    const values = {
      申请日期: identityValue(row, 'f_RQ'),
      单据编号: identityValue(row, 'DJBH'),
      项目: identityValue(row, 'XMMC'),
      历史项目名称: identityValue(row, 'XMMC'),
      往来单位: identityValue(row, 'WLDWMC'),
      历史往来单位: identityValue(row, 'WLDWMC'),
      收款金额: oldAmountText(row.f_JE),
      收款类型: identityValue(row, 'type'),
      收入类别: identityValue(row, 'f_SRLBName'),
      状态: stateLabel(row.DJZTText || row.DJZT),
      历史录入人: identityValue(row, 'LRR'),
      历史录入时间: identityValue(row, 'LRSJ'),
      旧库记录: identityValue(row, 'Id'),
    };
    return values[label] ?? '';
  }
  if (surfaceKey === 'supplier_contract') {
    const spec = SUPPLIER_CONTRACT_OLD_VALUE_MAP.find(([mappedLabel]) => mappedLabel === label);
    if (!spec) return '';
    return oldComparableValue(row, spec[1], spec[3], attachmentDisplayById);
  }
  return '';
}

function comparableVisibleValue(value, label) {
  if (/金额|合计|收款|退回|未退/.test(label)) return normalizeNumber(value);
  if (/日期|时间/.test(label)) return normalizeDate(value);
  return normalize(value);
}

async function compareSurfaceVisibleValues(page, surface, oldRows, attachmentDisplayById = new Map()) {
  const old = surface.old || {};
  const newer = surface.new || {};
  const labels = (newer.expected_headers || [])
    .map(normalize)
    .filter((label) => label && !VALUE_COMPARE_SKIP_LABELS.has(label));
  const fieldMap = NEW_VISIBLE_FIELD_MAP[surface.key] || {};
  const fields = Array.from(new Set([
    newer.identity_field,
    ...labels.map((label) => fieldMap[label] || aliasFieldName(label)),
  ]));
  const newRecords = await fetchRecords(
    page,
    newer.model,
    domainFromManifest(surface),
    fields,
    Math.max(Number(newer.expected_count || old.expected_count || 0), oldRows.length),
  );
  const newByIdentity = new Map(newRecords.map((record) => [normalize(record[newer.identity_field]), record]));
  const mismatches = [];
  for (const oldRow of oldRows) {
    const identity = identityValue(oldRow, old.identity_field);
    const newRow = newByIdentity.get(identity);
    if (!newRow) {
      mismatches.push({ legacy_id: identity, field: '__record__', old: 'present', new: 'missing' });
      continue;
    }
    for (const label of labels) {
      const aliasField = aliasFieldName(label);
      const newField = fieldMap[label] || aliasField;
      const oldRaw = oldVisibleValue(surface.key, label, oldRow, attachmentDisplayById);
      if (normalize(oldRaw).includes('�')) continue;
      const newRaw = newRow[newField];
      const oldValue = comparableVisibleValue(oldRaw, label);
      const newValue = comparableVisibleValue(newRaw, label);
      if (oldValue !== newValue) {
        mismatches.push({ legacy_id: identity, label, new_field: newField, old: oldValue, new: newValue });
      }
      if (mismatches.length >= 50) break;
    }
    if (mismatches.length >= 50) break;
  }
  return mismatches;
}

function oldComparableValue(row, fieldName, kind, attachmentDisplayById = new Map()) {
  if (kind === 'state') return stateLabel(row.DJZT);
  if (kind === 'number') return normalizeNumber(row[fieldName]);
  if (kind === 'date') return normalizeDate(row[fieldName]);
  if (fieldName === 'f_FJ_FJ') {
    const legacyId = normalize(row.Id);
    return attachmentDisplayById.has(legacyId)
      ? normalize(attachmentDisplayById.get(legacyId))
      : normalize(row.f_FJ_FJ || row.f_FJ);
  }
  return normalize(row[fieldName]);
}

function newComparableValue(row, fieldName, kind) {
  if (kind === 'number') return normalizeNumber(row[fieldName]);
  if (kind === 'date') return normalizeDate(row[fieldName]);
  return normalize(row[fieldName]);
}

function setDiff(left, right, limit = 20) {
  const out = [];
  for (const value of left) {
    if (!right.has(value)) out.push(value);
    if (out.length >= limit) break;
  }
  return out;
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if (await inputs.nth(2).isEditable().catch(() => false)) {
    await inputs.nth(2).fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intent(page, intentName, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ dbName, tokenValue, intentName, params }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: tokenValue ? `Bearer ${tokenValue}` : '',
        'X-Trace-Id': `scbs55-last6-strict-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return body.data || {};
  }, { dbName: DB_NAME, tokenValue: token, intentName, params });
}

async function actionInfo(page, actionId) {
  const data = await intent(page, 'api.data', {
    op: 'read',
    model: 'ir.actions.act_window',
    ids: [actionId],
    fields: ['id', 'name', 'res_model', 'domain', 'context', 'views'],
    context: { active_test: false },
  });
  const record = Array.isArray(data.records) ? data.records[0] : null;
  if (!record) throw new Error(`action ${actionId} not readable`);
  return record;
}

function domainFromManifest(surface) {
  const raw = normalize(surface?.new?.domain);
  if (!raw) return '[]';
  if (raw.startsWith('[')) return raw;
  if (surface.key === 'engineering_progress_receipt') {
    return "[('operation_strategy', '=', 'joint')]";
  }
  return '[]';
}

async function countRecords(page, model, domain) {
  const data = await intent(page, 'api.data', {
    op: 'count',
    model,
    domain,
    context: { active_test: false },
  });
  return Number(data.total || 0);
}

async function fetchIdentities(page, model, domain, identityField, expectedCount) {
  const identities = [];
  const pageSize = 1000;
  for (let offset = 0; offset < expectedCount + pageSize; offset += pageSize) {
    const data = await intent(page, 'api.data', {
      op: 'list',
      model,
      domain,
      fields: [identityField],
      limit: pageSize,
      offset,
      order: 'id',
      context: { active_test: false },
    });
    const records = Array.isArray(data.records) ? data.records : [];
    for (const record of records) {
      identities.push(normalize(record[identityField]));
    }
    if (records.length < pageSize) break;
  }
  return identities;
}

async function fetchRecords(page, model, domain, fields, expectedCount) {
  const records = [];
  const pageSize = 1000;
  for (let offset = 0; offset < expectedCount + pageSize; offset += pageSize) {
    const data = await intent(page, 'api.data', {
      op: 'list',
      model,
      domain,
      fields,
      limit: pageSize,
      offset,
      order: 'id',
      context: { active_test: false },
    });
    const pageRecords = Array.isArray(data.records) ? data.records : [];
    records.push(...pageRecords);
    if (pageRecords.length < pageSize) break;
  }
  return records;
}

async function waitForList(page) {
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|INTERNAL_ERROR/.test(text)) return true;
    if (/没有匹配记录|暂无数据|0 条/.test(text)) return true;
    return Boolean(document.querySelector('table.flat-table thead, table.group-table thead, .table table thead, table thead'));
  }, null, { timeout: 45000 });
  await page.waitForTimeout(500);
  const bodyText = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
  if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|INTERNAL_ERROR/.test(bodyText)) {
    throw new Error(bodyText.slice(0, 500));
  }
}

async function tableHeaders(page) {
  return page.evaluate((helperHeaders) => {
    function normalizeText(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }
    function headerText(node) {
      const clone = node.cloneNode(true);
      for (const child of Array.from(clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'))) {
        child.remove();
      }
      return normalizeText(clone.textContent);
    }
    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    const candidates = tables.map((table) => Array.from(table.querySelectorAll('thead th'))
      .map(headerText)
      .filter((text) => !helperHeaders.includes(text)));
    candidates.sort((left, right) => right.length - left.length);
    return candidates[0] || [];
  }, Array.from(HELPER_HEADERS));
}

async function visibleRowCount(page) {
  return page.evaluate(() => Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
    .filter((table) => {
      const rect = table.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    })
    .reduce((total, table) => total + table.querySelectorAll('tbody tr').length, 0));
}

function writeMarkdown(report) {
  const lines = [
    '# SCBS55 Last 6 Strict Visible Acceptance v1',
    '',
    `- status: ${report.status}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- login: ${report.login}`,
    `- checked_count: ${report.checked_count}`,
    `- failure_count: ${report.failure_count}`,
    '',
    '| key | name | action | expected | new count | headers | identities | status |',
    '| --- | --- | ---: | ---: | ---: | --- | --- | --- |',
  ];
  for (const row of report.rows) {
    lines.push(`| ${row.key} | ${row.name} | ${row.new_action_id} | ${row.expected_count} | ${row.new_count} | ${row.header_status} | ${row.identity_status} | ${row.status} |`);
  }
  lines.push('', '## Failures', '', '```json', JSON.stringify(report.failures, null, 2), '```', '');
  fs.writeFileSync(OUT_MD, lines.join('\n'), 'utf8');
}

async function main() {
  ensureDir(ARTIFACTS_DIR);
  const manifest = readJson(MANIFEST_PATH);
  const evidenceLock = readJson(EVIDENCE_LOCK_PATH);
  const lockedByKey = new Map((evidenceLock.surfaces || []).map((row) => [row.key, row]));
  const surfaces = (manifest.surfaces || []).filter((surface) => TARGET_KEYS.has(surface.key));
  if (surfaces.length !== TARGET_KEYS.size) {
    throw new Error(`target surface count mismatch: ${surfaces.length} != ${TARGET_KEYS.size}`);
  }

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));

  const rows = [];
  try {
    await login(page);
    for (const surface of surfaces) {
      const old = surface.old || {};
      const newer = surface.new || {};
      const locked = lockedByKey.get(surface.key) || {};
      const expectedHeaders = (newer.expected_headers || []).map(normalize);
      const expectedCount = Number(newer.expected_count || old.expected_count || 0);
      const oldRowFile = path.join(OLD_ROWS_DIR, old.row_dump_file || '');
      const result = {
        key: surface.key,
        name: surface.name,
        old_row_file: oldRowFile,
        old_row_dump_sha256: '',
        old_row_dump_sha256_expected: locked.old_row_dump_sha256 || '',
        old_count: 0,
        old_identity_field: old.identity_field,
        old_identity_count: 0,
        old_identity_unique_count: 0,
        old_identity_missing_count: 0,
        new_menu_id: newer.menu_id,
        new_action_id: newer.action_id,
        new_model: newer.model,
        new_identity_field: newer.identity_field,
        expected_count: expectedCount,
        action_domain: '',
        new_count: 0,
        new_identity_count: 0,
        new_identity_unique_count: 0,
        new_identity_missing_count: 0,
        value_status: 'SKIP',
        value_mismatch_count: 0,
        value_mismatch_sample: [],
        actual_headers: [],
        expected_headers: expectedHeaders,
        browser_visible_row_count: 0,
        header_status: 'FAIL',
        identity_status: 'FAIL',
        count_status: 'FAIL',
        evidence_status: 'FAIL',
        missing_new_identities_sample: [],
        extra_new_identities_sample: [],
        notes: [],
        errors: [],
        status: 'FAIL',
      };
      try {
        if (!fs.existsSync(oldRowFile)) throw new Error(`missing old row dump: ${oldRowFile}`);
        result.old_row_dump_sha256 = sha256File(oldRowFile);
        if (result.old_row_dump_sha256 !== result.old_row_dump_sha256_expected) {
          result.errors.push('old_row_dump_sha256_mismatch');
        }
        const oldPayload = readJson(oldRowFile);
        const oldRows = Array.isArray(oldPayload.rows) ? oldPayload.rows : [];
        const oldIdentities = oldRows.map((row) => identityValue(row, old.identity_field)).filter(Boolean);
        const oldSet = new Set(oldIdentities);
        result.old_count = oldRows.length;
        result.old_identity_count = oldIdentities.length;
        result.old_identity_unique_count = oldSet.size;
        result.old_identity_missing_count = oldRows.length - oldIdentities.length;
        if (result.old_count !== expectedCount) result.errors.push(`old_count_mismatch:${result.old_count}`);
        if (result.old_identity_count !== expectedCount) result.errors.push(`old_identity_count_mismatch:${result.old_identity_count}`);
        if (result.old_identity_unique_count !== expectedCount) result.errors.push(`old_identity_unique_mismatch:${result.old_identity_unique_count}`);
        if (result.old_identity_missing_count) result.errors.push(`old_identity_missing:${result.old_identity_missing_count}`);

        let action = {};
        try {
          action = await actionInfo(page, Number(newer.action_id));
        } catch (err) {
          result.notes.push(`action_metadata_unreadable_for_login:${err?.message || String(err)}`);
        }
        if (action.res_model && normalize(action.res_model) !== normalize(newer.model)) {
          result.errors.push(`action_model_mismatch:${action.res_model}`);
        }
        result.action_domain = action.domain || domainFromManifest(surface);
        result.new_count = await countRecords(page, newer.model, result.action_domain || '[]');
        result.count_status = result.new_count === expectedCount ? 'PASS' : 'FAIL';
        if (result.count_status !== 'PASS') result.errors.push(`new_count_mismatch:${result.new_count}`);

        const newIdentities = await fetchIdentities(
          page,
          newer.model,
          result.action_domain || '[]',
          newer.identity_field,
          Math.max(expectedCount, result.new_count),
        );
        const newSet = new Set(newIdentities.filter(Boolean));
        result.new_identity_count = newIdentities.filter(Boolean).length;
        result.new_identity_unique_count = newSet.size;
        result.new_identity_missing_count = newIdentities.length - result.new_identity_count;
        result.missing_new_identities_sample = setDiff(oldSet, newSet);
        result.extra_new_identities_sample = setDiff(newSet, oldSet);
        result.identity_status = (
          result.old_identity_unique_count === expectedCount
          && result.new_identity_unique_count === expectedCount
          && result.new_identity_missing_count === 0
          && result.missing_new_identities_sample.length === 0
          && result.extra_new_identities_sample.length === 0
        ) ? 'PASS' : 'FAIL';
        if (result.identity_status !== 'PASS') result.errors.push('identity_set_mismatch');

        const attachmentDisplayById = surface.key === 'supplier_contract'
          ? loadSupplierAttachmentDisplayById()
          : new Map();
        if (surface.key === 'supplier_contract') {
          result.attachment_display_lock = SUPPLIER_ATTACHMENT_DISPLAY_LOCK;
          result.attachment_display_locked_rows = attachmentDisplayById.size;
          if (attachmentDisplayById.size !== expectedCount) {
            result.errors.push(`attachment_display_lock_count_mismatch:${attachmentDisplayById.size}`);
          }
        }
        const visibleValueMismatches = await compareSurfaceVisibleValues(page, surface, oldRows, attachmentDisplayById);
        result.value_mismatch_count = visibleValueMismatches.length;
        result.value_mismatch_sample = visibleValueMismatches.slice(0, 20);
        result.value_status = visibleValueMismatches.length ? 'FAIL' : 'PASS';
        if (result.value_status !== 'PASS') result.errors.push(`visible_value_mismatch:${visibleValueMismatches.length}`);

        if (surface.key === 'supplier_contract') {
          const newRecords = await fetchRecords(
            page,
            newer.model,
            result.action_domain || '[]',
            ['legacy_contract_id', ...SUPPLIER_CONTRACT_VALUE_FIELDS],
            expectedCount,
          );
          const newByLegacyId = new Map(newRecords.map((record) => [normalize(record.legacy_contract_id), record]));
          const mismatches = [];
          for (const oldRow of oldRows) {
            const legacyId = identityValue(oldRow, old.identity_field);
            const newRow = newByLegacyId.get(legacyId);
            if (!newRow) {
              mismatches.push({ legacy_id: legacyId, field: '__record__', old: 'present', new: 'missing' });
              continue;
            }
            for (const [label, oldField, newField, kind] of SUPPLIER_CONTRACT_OLD_VALUE_MAP) {
              const oldValue = oldComparableValue(oldRow, oldField, kind, attachmentDisplayById);
              const newValue = newComparableValue(newRow, newField, kind);
              if (oldValue !== newValue) {
                mismatches.push({ legacy_id: legacyId, label, old_field: oldField, new_field: newField, old: oldValue, new: newValue });
              }
              if (mismatches.length >= 50) break;
            }
            if (mismatches.length >= 50) break;
          }
          result.supplier_raw_value_mismatch_count = mismatches.length;
          result.supplier_raw_value_mismatch_sample = mismatches.slice(0, 20);
          result.supplier_raw_value_status = mismatches.length ? 'FAIL' : 'PASS';
          if (result.supplier_raw_value_status !== 'PASS') result.errors.push(`supplier_raw_value_mismatch:${mismatches.length}`);
        }

        await page.goto(`${FRONTEND_URL}/a/${newer.action_id}?db=${encodeURIComponent(DB_NAME)}&scbs55_last6_strict=${Date.now()}`, {
          waitUntil: 'domcontentloaded',
          timeout: 45000,
        });
        await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => undefined);
        await waitForList(page);
        result.actual_headers = await tableHeaders(page);
        result.browser_visible_row_count = await visibleRowCount(page);
        const actualComparable = result.actual_headers.slice(0, expectedHeaders.length);
        const extraHeaders = result.actual_headers.slice(expectedHeaders.length).filter((header) => !HELPER_HEADERS.has(header));
        result.header_status = (
          JSON.stringify(actualComparable) === JSON.stringify(expectedHeaders)
          && extraHeaders.length === 0
        ) ? 'PASS' : 'FAIL';
        if (result.header_status !== 'PASS') {
          result.errors.push('browser_header_exact_mismatch');
          result.extra_headers = extraHeaders;
        }
        if (result.browser_visible_row_count < 1) result.errors.push('browser_no_rows_rendered');
        result.evidence_status = result.old_row_dump_sha256 === result.old_row_dump_sha256_expected ? 'PASS' : 'FAIL';
        result.status = result.errors.length ? 'FAIL' : 'PASS';
      } catch (err) {
        result.errors.push(err?.message || String(err));
      }
      rows.push(result);
      console.log(`[scbs55-last6-strict] ${result.status} ${result.name} old=${result.old_count} new=${result.new_count} headers=${result.header_status} identities=${result.identity_status}`);
    }
  } finally {
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
  }

  const meaningfulConsoleErrors = consoleErrors.filter((message) => {
    const text = normalize(message);
    return text && !/favicon\.ico/.test(text) && !/Failed to load resource: the server responded with a status of 404/.test(text);
  });
  const failures = rows.filter((row) => row.status !== 'PASS');
  const report = {
    status: failures.length || meaningfulConsoleErrors.length ? 'FAIL' : 'PASS',
    mode: 'scbs55_last6_strict_visible_acceptance',
    generated_at: new Date().toISOString(),
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    login: LOGIN,
    manifest: path.relative(ROOT, MANIFEST_PATH),
    evidence_lock: path.relative(ROOT, EVIDENCE_LOCK_PATH),
    old_rows_dir: OLD_ROWS_DIR,
    checked_count: rows.length,
    failure_count: failures.length,
    console_error_count: consoleErrors.length,
    fatal_console_error_count: meaningfulConsoleErrors.length,
    fatal_console_errors: meaningfulConsoleErrors,
    failures,
    rows,
  };
  fs.writeFileSync(OUT_JSON, JSON.stringify(report, null, 2) + '\n', 'utf8');
  writeMarkdown(report);
  console.log(`SCBS55_LAST6_STRICT_VISIBLE_ACCEPTANCE=${report.status} output=${OUT_JSON}`);
  if (report.status !== 'PASS') process.exitCode = 1;
}

main().catch((err) => {
  ensureDir(ARTIFACTS_DIR);
  fs.writeFileSync(OUT_JSON, JSON.stringify({ status: 'FAIL', error: err.message, stack: err.stack }, null, 2) + '\n', 'utf8');
  console.error(`SCBS55_LAST6_STRICT_VISIBLE_ACCEPTANCE=FAIL ${err.message}`);
  process.exit(1);
});
