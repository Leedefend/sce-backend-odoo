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

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const SOURCE_DOCUMENT = '/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const OUT_DIR = path.join(
  ARTIFACTS_DIR,
  'browser',
  'scbs55-full-visible-data-coverage',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);
const PAGE_LIMIT = Number(process.env.PAGE_LIMIT || 500);
const ALLOW_ZERO = new Set([13, 130]);

function normalize(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function aliasField(label) {
  return 'p1_visible_' + crypto.createHash('sha1').update(label, 'utf8').digest('hex').slice(0, 12);
}

function hasTechnicalKey(value) {
  return /online_old_scbs:|legacy-file:\/\/|legacy-file-id:\/\//.test(value);
}

function hasRawHash(label, value) {
  if (!value || value.match(/^\d+$/) || /(账号|账户|卡号|税号|信用代码)/.test(label)) return false;
  if (/^[0-9a-fA-F]{24,64}$/.test(value)) return true;
  if (/附件/.test(label)) {
    return value.split(/[\s,;|]+/).some((item) => /^[0-9a-fA-F]{24,64}(\.[A-Za-z0-9]{1,8})?$/.test(item));
  }
  return false;
}

function hasRawDocumentStateCode(label, value) {
  return /^(单据状态|状态)$/.test(label) && /^-?\d+$/.test(value);
}

function parseDomain(raw) {
  const text = normalize(raw || '[]');
  if (!text || text === '[]') return [];
  const jsonish = text
    .replace(/\(/g, '[')
    .replace(/\)/g, ']')
    .replace(/\bFalse\b/g, 'false')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bNone\b/g, 'null')
    .replace(/'/g, '"');
  return JSON.parse(jsonish);
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
  return page.evaluate((db) => sessionStorage.getItem(`sc_auth_token:${db}`) || '', DB_NAME);
}

async function apiData(page, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ db, token: bearer, params: requestParams }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(db)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
      },
      body: JSON.stringify({ intent: 'api.data', params: requestParams }),
    });
    const body = await response.json().catch((error) => ({ ok: false, error: { message: String(error) } }));
    if (!response.ok || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `api.data ${response.status}`);
    }
    return body.data || {};
  }, { db: DB_NAME, token, params });
}

async function tableHeaders(page) {
  return page.evaluate(() => {
    function text(node) {
      const clone = node.cloneNode(true);
      for (const child of Array.from(
        clone.querySelectorAll('svg,.sort-indicator,.column-resize-handle,[aria-hidden="true"]'),
      )) {
        child.remove();
      }
      return String(clone.textContent || '').replace(/\s+/g, ' ').trim();
    }
    const helper = new Set(['', '序号', '操作', 'Actions', '列']);
    const tables = Array.from(document.querySelectorAll('table.flat-table, table.group-table, .table table, table'))
      .filter((table) => {
        const rect = table.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });
    tables.sort((left, right) => right.querySelectorAll('thead th').length - left.querySelectorAll('thead th').length);
    const table = tables[0];
    if (!table) return { headers: [], row_count: 0, first_rows_text: [] };
    return {
      headers: Array.from(table.querySelectorAll('thead th')).map(text).filter((item) => !helper.has(item)),
      row_count: table.querySelectorAll('tbody tr').length,
      first_rows_text: Array.from(table.querySelectorAll('tbody tr')).slice(0, 3).map(text),
    };
  });
}

async function fetchAll(page, model, domain, fields) {
  const rows = [];
  for (let offset = 0; ; offset += PAGE_LIMIT) {
    const data = await apiData(page, {
      op: 'list',
      model,
      domain,
      fields,
      limit: PAGE_LIMIT,
      offset,
      context: { active_test: true },
    });
    const batch = data.records || [];
    rows.push(...batch);
    if (batch.length < PAGE_LIMIT) break;
    if (rows.length > 300000) throw new Error(`too many rows for ${model}`);
  }
  return rows;
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, locale: 'zh-CN' });
  const page = await context.newPage();
  const result = {
    status: 'PASS',
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    rows: [],
    failures: [],
    totals: { entries: 0, records: 0, cells: 0 },
  };
  try {
    await login(page);
    const planData = await apiData(page, {
      op: 'list',
      model: 'sc.legacy.user.priority.menu.plan',
      domain: [['source_document', '=', SOURCE_DOCUMENT]],
      fields: ['priority_sequence', 'legacy_menu_name', 'target_action_id', 'target_model', 'list_field_contract'],
      order: 'priority_sequence',
      limit: 80,
      context: { active_test: false },
    });
    const plans = (planData.records || []).map((record) => {
      const action = Array.isArray(record.target_action_id)
        ? Number(record.target_action_id[0] || 0)
        : Number(record.target_action_id || 0);
      const labels = [];
      const seen = new Set();
      for (const item of (Array.isArray(record.list_field_contract) ? record.list_field_contract : [])) {
        const label = normalize(item?.legacy_label);
        if (!label || label === '操作' || seen.has(label)) continue;
        seen.add(label);
        labels.push(label);
      }
      const rawSeq = Number(record.priority_sequence || 0);
      return {
        seq: rawSeq >= 10 && rawSeq % 10 === 0 ? rawSeq / 10 : rawSeq,
        raw_seq: rawSeq,
        name: normalize(record.legacy_menu_name),
        model: normalize(record.target_model),
        action,
        labels,
      };
    });
    const actionIds = plans.map((plan) => plan.action).filter(Boolean);
    const actionData = await apiData(page, {
      op: 'list',
      model: 'ir.actions.act_window',
      domain: [['id', 'in', actionIds]],
      fields: ['id', 'name', 'res_model', 'domain'],
      limit: 100,
    });
    const actionById = new Map((actionData.records || []).map((action) => [Number(action.id), action]));

    for (const plan of plans) {
      console.log(`[browser-full] seq=${plan.seq} ${plan.name}`);
      const entry = {
        seq: plan.seq,
        name: plan.name,
        action: plan.action,
        model: plan.model,
        status: 'PASS',
        errors: [],
        page: {},
        data: { record_count: 0, cell_count: 0, anomaly_count: 0, anomalies: [] },
      };
      try {
        if (!plan.action) throw new Error('missing action');
        const action = actionById.get(plan.action);
        if (!action) throw new Error('missing action metadata');
        const domain = parseDomain(action.domain || '[]');
        await page.goto(`${FRONTEND_URL}/a/${plan.action}?db=${encodeURIComponent(DB_NAME)}&fullcov=${Date.now()}`, {
          waitUntil: 'domcontentloaded',
          timeout: 30000,
        });
        await page.waitForFunction(
          () => document.querySelector('table thead')
            || /页面加载失败|页面渲染失败|暂无数据|没有匹配记录|0 条/.test(document.body?.textContent || ''),
          null,
          { timeout: 45000 },
        ).catch(() => undefined);
        await page.waitForTimeout(250);
        const screenshot = path.join(
          OUT_DIR,
          `${String(plan.seq).padStart(3, '0')}_${plan.name.replace(/[\\/]/g, '_')}.png`,
        );
        await page.screenshot({ path: screenshot, fullPage: true }).catch(() => undefined);
        const table = await tableHeaders(page);
        entry.page = {
          url: page.url(),
          screenshot,
          headers: table.headers,
          row_count: table.row_count,
          first_rows_text: table.first_rows_text,
        };
        const body = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
        if (/页面加载失败|页面渲染失败|System exception|NAV_MENU_NO_ACTION|INTERNAL_ERROR|Traceback/.test(body)) {
          entry.errors.push('page_failure_text');
        }
        if (plan.labels.length && !ALLOW_ZERO.has(plan.seq)) {
          const actual = table.headers.slice(0, plan.labels.length);
          if (JSON.stringify(actual) !== JSON.stringify(plan.labels)) {
            entry.errors.push(`header_mismatch expected=${JSON.stringify(plan.labels)} actual=${JSON.stringify(actual)}`);
          }
        }
        const fields = ['id', ...plan.labels.map(aliasField)];
        let records = [];
        if (plan.model) {
          records = await fetchAll(page, plan.model, domain, fields);
        }
        entry.data.record_count = records.length;
        if (records.length === 0 && !ALLOW_ZERO.has(plan.seq)) {
          entry.errors.push('no_records_from_browser_api');
        }
        if (records.length > 0 && table.row_count < 1 && !ALLOW_ZERO.has(plan.seq)) {
          entry.errors.push('records_exist_but_no_rows_rendered');
        }
        for (const record of records) {
          for (const label of plan.labels) {
            const value = normalize(record[aliasField(label)]);
            entry.data.cell_count += 1;
            if (hasTechnicalKey(value) || hasRawHash(label, value) || hasRawDocumentStateCode(label, value)) {
              entry.data.anomaly_count += 1;
              if (entry.data.anomalies.length < 20) {
                entry.data.anomalies.push({ id: record.id, label, value: value.slice(0, 200) });
              }
            }
          }
        }
        if (entry.data.anomaly_count) {
          entry.errors.push(`visible_value_anomalies=${entry.data.anomaly_count}`);
        }
      } catch (error) {
        entry.errors.push(error.message || String(error));
      }
      if (entry.errors.length) {
        entry.status = 'FAIL';
        result.failures.push(entry);
      }
      result.rows.push(entry);
      result.totals.entries += 1;
      result.totals.records += entry.data.record_count || 0;
      result.totals.cells += entry.data.cell_count || 0;
    }
    if (result.failures.length) result.status = 'FAIL';
    fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify(result, null, 2), 'utf8');
    console.log(
      `[scbs55_browser_full_coverage] ${result.status} entries=${result.totals.entries}`
        + ` records=${result.totals.records} cells=${result.totals.cells}`
        + ` failures=${result.failures.length} artifacts=${OUT_DIR}`,
    );
    if (result.status !== 'PASS') process.exitCode = 1;
  } finally {
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
