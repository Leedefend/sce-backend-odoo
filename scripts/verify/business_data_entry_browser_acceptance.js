#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const requireBase = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? path.join(process.cwd(), 'frontend/apps/web/package.json')
  : path.join(process.cwd(), 'package.json');
const requireFromRoot = createRequire(requireBase);
const { chromium } = requireFromRoot('playwright');
const ROOT_DIR = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? process.cwd()
  : path.resolve(process.cwd(), '../../..');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT_DIR, 'artifacts');

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'business-data-entry-browser', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachPageGuards(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
  page.on('dialog', async (dialog) => {
    await dialog.accept();
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  const dbEditable = await dbInput.isEditable().catch(() => false);
  if (dbEditable) {
    await dbInput.fill(DB_NAME);
  } else {
    const currentDb = normalize(await dbInput.inputValue().catch(() => ''));
    if (currentDb && currentDb !== DB_NAME) {
      throw new Error(`login db input is locked to ${currentDb}, expected ${DB_NAME}`);
    }
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params, options = {}) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload, allowError }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `business-data-entry-browser-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!allowError && (!response.ok || body.ok === false)) {
      throw new Error(body?.error?.message || body?.message || `${intentName} failed`);
    }
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
      meta: body.meta || {},
    };
  }, {
    dbName: DB_NAME,
    authToken,
    intentName: intent,
    payload: params,
    allowError: Boolean(options.allowError),
  });
}

async function listOne(page, model, domain, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'list',
    model,
    domain,
    fields,
    limit: 1,
    context: {},
  });
  const records = Array.isArray(resp.data?.records) ? resp.data.records : [];
  if (!records.length) throw new Error(`fixture missing: ${model} ${JSON.stringify(domain || [])}`);
  return records[0];
}

async function createRecord(page, model, vals, context = {}) {
  const resp = await intentRequest(page, 'api.data', { op: 'create', model, vals, context });
  const id = Number(resp.data?.id || 0);
  if (!id) throw new Error(`create ${model} returned no id: ${JSON.stringify(resp)}`);
  return id;
}

async function readRecord(page, model, id, fields) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model,
    ids: [id],
    fields,
    context: {},
  });
  const rows = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return rows[0] || {};
}

async function resolveRuntimeMenuRefs(page, xmlIds) {
  const resp = await intentRequest(page, 'system.init', {});
  const byXmlId = {};
  const seen = new Set();
  const visit = (value) => {
    if (!value || typeof value !== 'object' || seen.has(value)) return;
    seen.add(value);
    const meta = value.meta && typeof value.meta === 'object' ? value.meta : {};
    const menuXmlId = String(meta.menu_xmlid || '');
    if (xmlIds.includes(menuXmlId)) {
      byXmlId[menuXmlId] = {
        menuId: Number(meta.menu_id || value.menu_id || 0),
        actionId: Number(meta.action_id || 0),
        model: String(meta.model || ''),
      };
    }
    for (const child of Object.values(value)) visit(child);
  };
  visit(resp.data || {});
  for (const xmlId of xmlIds) {
    const ref = byXmlId[xmlId];
    if (!ref || !ref.menuId || !ref.actionId) throw new Error(`runtime menu ref not resolved: ${xmlId}`);
  }
  return byXmlId;
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
  const text = normalize(await page.locator('.template-layout-shell').textContent());
  if (text.includes('页面加载失败') || text.includes('页面渲染失败') || text.includes('System exception')) {
    throw new Error(`form render failed: ${text.slice(0, 300)}`);
  }
  return text;
}

async function openCreateForm(page, scenario) {
  await page.goto(`${FRONTEND_URL}/f/${scenario.model}/new?menu_id=${scenario.menuId}&action_id=${scenario.actionId}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  return waitForFormReady(page);
}

async function openRecord(page, scenario, id) {
  await page.goto(`${FRONTEND_URL}/r/${scenario.model}/${id}?menu_id=${scenario.menuId}&action_id=${scenario.actionId}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  return waitForFormReady(page);
}

async function setFieldByLabel(page, label, value) {
  const labels = Array.isArray(label) ? label : [label];
  const ok = await page.evaluate(({ labelTexts, fieldValue }) => {
    const clean = (val) => String(val || '').replace(/\s+/g, ' ').trim().replace(/\*$/, '');
    const fields = Array.from(document.querySelectorAll('.field'));
    const wanted = labelTexts.map((item) => clean(item));
    const target = fields.find((field) => wanted.includes(clean(field.querySelector('.label')?.textContent || '')));
    if (!target) return false;
    const input = target.querySelector('input.input, textarea.input, select.input');
    if (!input) return false;
    input.value = String(fieldValue);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }, { labelTexts: labels, fieldValue: value });
  if (!ok) throw new Error(`field not found or not editable: ${labels.join('|')}`);
}

async function saveForm(page, scenario) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 15000 });
  const writeResponse = page.waitForResponse(async (response) => {
    if (!response.url().includes('/api/v1/intent')) return false;
    const request = response.request();
    let payload = {};
    try {
      payload = JSON.parse(request.postData() || '{}');
    } catch {
      return false;
    }
    const params = payload.params || {};
    return payload.intent === 'api.data' && params.op === 'write' && params.model === scenario.model;
  }, { timeout: 25000 }).catch(() => null);
  await save.click();
  const response = await writeResponse;
  if (response) {
    const body = await response.json().catch(() => ({}));
    if (!response.ok() || body.ok === false) {
      throw new Error(body?.error?.message || body?.message || `save failed for ${scenario.model}`);
    }
  } else {
    await page.waitForTimeout(1500);
  }
}

async function clickNativeButtonIfPresent(page, label) {
  const button = page.locator('button.native-action-btn').filter({ hasText: new RegExp(`^${label}$`) }).first();
  if (!await button.count()) return false;
  await button.click();
  await page.waitForTimeout(900);
  return true;
}

async function buildFixtures(page, marker) {
  const project = await listOne(page, 'project.project', [], ['id', 'name']);
  const partner = await listOne(page, 'res.partner', [], ['id', 'name']);
  const uom = await listOne(page, 'uom.uom', [], ['id', 'name']);
  const costCode = await listOne(page, 'project.cost.code', [], ['id', 'name']);
  const tenderBidId = await createRecord(page, 'tender.bid', {
    project_id: Number(project.id),
    owner_id: Number(partner.id),
    tender_name: `浏览器投标夹具 ${marker}`,
    bid_amount: 10000,
  });
  const budgetId = await createRecord(page, 'project.budget', {
    name: `浏览器预算夹具 ${marker}`,
    project_id: Number(project.id),
    amount_revenue_target: 10000,
    amount_cost_target: 8000,
  });
  const budgetLineId = await createRecord(page, 'project.budget.boq.line', {
    budget_id: budgetId,
    name: `浏览器预算清单夹具 ${marker}`,
    uom_id: Number(uom.id),
    qty_bidded: 10,
    price_bidded: 20,
  });
  return { project, partner, uom, costCode, tenderBidId, budgetId, budgetLineId };
}

function scenarios(fixtures, marker, refs) {
  return [
    {
      key: 'tender_opening',
      label: '投标管理/开标记录',
      model: 'tender.opening',
      actionId: refs['smart_construction_core.menu_sc_tender_opening'].actionId,
      menuId: refs['smart_construction_core.menu_sc_tender_opening'].menuId,
      createText: ['开标记录'],
      vals: { bid_id: fixtures.tenderBidId, open_time: '2026-05-02 10:00:00', result: 'pending', win_price: 9000, remark: `browser-entry ${marker}` },
      edit: async (page) => {
        await setFieldByLabel(page, ['Result', '开标结果', '结果'], 'won');
        await setFieldByLabel(page, '中标价', '9100');
      },
      readFields: ['id', 'result', 'win_price'],
      assert: (row) => row.result === 'won' && Number(row.win_price) === 9100,
    },
    {
      key: 'tender_guarantee',
      label: '投标管理/投标保证金',
      model: 'tender.guarantee',
      actionId: refs['smart_construction_core.menu_sc_tender_guarantee'].actionId,
      menuId: refs['smart_construction_core.menu_sc_tender_guarantee'].menuId,
      createText: ['投标保证金'],
      vals: { bid_id: fixtures.tenderBidId, type: 'out', amount: 3000, remark: `browser-entry ${marker}` },
      edit: async (page) => {
        await setFieldByLabel(page, '金额', '3200');
      },
      readFields: ['id', 'amount'],
      assert: (row) => Number(row.amount) === 3200,
    },
    {
      key: 'project_boq_line',
      label: '项目预算/预算清单',
      model: 'project.boq.line',
      actionId: 522,
      menuId: 356,
      createText: ['工程量清单'],
      vals: {
        project_id: Number(fixtures.project.id),
        code: `BOQ-BROWSER-${marker}`,
        name: `浏览器预算清单 ${marker}`,
        uom_id: Number(fixtures.uom.id),
        quantity: 10,
        price: 20,
        section_type: 'other',
      },
      edit: async (page) => {
        await setFieldByLabel(page, '工程量', '12');
        await setFieldByLabel(page, '单价', '25');
      },
      readFields: ['id', 'quantity', 'price', 'amount'],
      assert: (row) => Number(row.quantity) === 12 && Number(row.price) === 25 && Number(row.amount) === 300,
    },
    {
      key: 'project_budget',
      label: '成本中心/目标成本',
      model: 'project.budget',
      actionId: 507,
      menuId: 368,
      createText: ['项目预算'],
      vals: {
        name: `浏览器目标成本 ${marker}`,
        project_id: Number(fixtures.project.id),
        amount_revenue_target: 10000,
        amount_cost_target: 8000,
      },
      edit: async (page) => {
        await setFieldByLabel(page, '目标成本', '8800');
      },
      afterSave: async (page) => {
        await clickNativeButtonIfPresent(page, '停用');
        await clickNativeButtonIfPresent(page, '设为当前');
      },
      readFields: ['id', 'amount_cost_target', 'is_active'],
      assert: (row) => Number(row.amount_cost_target) === 8800 && row.is_active === true,
    },
    {
      key: 'project_budget_cost_alloc',
      label: '成本中心/预算清单分摊',
      model: 'project.budget.cost.alloc',
      actionId: 513,
      menuId: 369,
      createText: ['预算清单分摊'],
      vals: {
        budget_boq_line_id: fixtures.budgetLineId,
        cost_code_id: Number(fixtures.costCode.id),
        ratio: 0.5,
        amount_budget: 100,
        note: `browser-entry ${marker}`,
      },
      edit: async (page) => {
        await setFieldByLabel(page, '分摊比例(0-1)', '0.6');
        await setFieldByLabel(page, '对应预算金额', '120');
      },
      readFields: ['id', 'ratio', 'amount_budget'],
      assert: (row) => Number(row.ratio) === 0.6 && Number(row.amount_budget) === 120,
    },
  ];
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, locale: 'zh-CN' });
  attachPageGuards(page);

  const marker = Date.now();
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    artifact_dir: outDir,
    marker,
    checks: [],
    created: {},
    cleanup: {},
  };

  try {
    await login(page);
    const refs = await resolveRuntimeMenuRefs(page, [
      'smart_construction_core.menu_sc_tender_opening',
      'smart_construction_core.menu_sc_tender_guarantee',
    ]);
    summary.resolved_refs = refs;
    const fixtures = await buildFixtures(page, marker);
    summary.created.fixture_tender_bid = { model: 'tender.bid', ids: [fixtures.tenderBidId] };
    summary.created.fixture_budget = { model: 'project.budget', ids: [fixtures.budgetId] };
    summary.created.fixture_budget_line = { model: 'project.budget.boq.line', ids: [fixtures.budgetLineId] };

    for (const scenario of scenarios(fixtures, marker, refs)) {
      const check = { scenario: scenario.key, label: scenario.label, status: 'fail' };
      try {
        const createText = await openCreateForm(page, scenario);
        check.create_form_ok = scenario.createText.every((text) => createText.includes(text));
        const id = await createRecord(page, scenario.model, scenario.vals, {});
        summary.created[scenario.key] = { model: scenario.model, ids: [id] };
        await openRecord(page, scenario, id);
        await scenario.edit(page);
        await saveForm(page, scenario);
        if (scenario.afterSave) {
          await scenario.afterSave(page);
        }
        const row = await readRecord(page, scenario.model, id, scenario.readFields);
        check.final_record = row;
        check.status = check.create_form_ok && scenario.assert(row) ? 'pass' : 'fail';
        await page.screenshot({ path: path.join(outDir, `${scenario.key}.png`), fullPage: true });
      } catch (err) {
        check.error = err instanceof Error ? err.stack || err.message : String(err);
      }
      summary.checks.push(check);
    }
    summary.console_errors = page.__consoleErrors || [];
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
    summary.console_errors = page.__consoleErrors || [];
  } finally {
    for (const [key, value] of Object.entries(summary.created)) {
      summary.cleanup[key] = {
        ok: true,
        mode: 'manual_odoo_shell_required',
        model: value.model,
        ids: value.ids,
      };
    }
    await browser.close().catch(() => {});
  }

  summary.pass = !summary.error
    && summary.checks.length === 5
    && summary.checks.every((row) => row.status === 'pass')
    && (summary.console_errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[business_data_entry_browser_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((row) => ({ scenario: row.scenario, status: row.status })),
    console_errors: (summary.console_errors || []).length,
    error: summary.error || null,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[business_data_entry_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
