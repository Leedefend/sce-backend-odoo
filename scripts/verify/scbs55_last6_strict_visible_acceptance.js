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
const TARGET_KEYS = new Set([
  'self_guarantee',
  'self_guarantee_refund',
  'self_funding_income',
  'self_funding_refund',
  'engineering_progress_receipt',
  'supplier_contract',
]);
const HELPER_HEADERS = new Set(['', '序号', '列', '操作', 'Actions']);

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function normalize(value) {
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
