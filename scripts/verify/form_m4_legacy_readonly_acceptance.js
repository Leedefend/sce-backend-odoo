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

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5174';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'sc.legacy.receipt.income.fact';
const RECORD_ID = Number(process.env.RECORD_ID || 7220);
const ACTION_ID = Number(process.env.ACTION_ID || 561);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const EXPECTED_FIELD_LABELS = [
  '单据日期',
  '单据编号',
  '来源类别',
  '收支方向',
  '旧库状态',
  '收入类别',
  '项目',
  '往来单位',
  '原始金额',
  '旧库项目',
  '旧库项目名称',
  '旧库往来单位',
  '旧库往来单位名称',
  '旧库来源表',
  '旧库记录',
  '旧库序号',
  '导入批次',
  '备注',
];
const ENGLISH_FIELD_LABEL_RE = /\b(Document Date|Document No|Source Family|Direction|Legacy State|Income Category|Source Amount|Legacy Project|Legacy Partner|Import Batch|Note)\b/;
const READONLY_MUTATION_REASON = 'READONLY_PROJECTION_MUTATION_DENIED';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m4-legacy-readonly', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') page.__consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: bearer ? `Bearer ${bearer}` : '',
        'X-Trace-Id': `form-m4-readonly-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
      meta: body.meta || {},
    };
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

async function readRecord(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: MODEL,
    ids: [RECORD_ID],
    fields: [
      'id',
      'document_no',
      'document_date',
      'source_family',
      'direction',
      'income_category',
      'project_id',
      'legacy_project_name',
      'legacy_partner_name',
      'source_amount',
      'import_batch',
    ],
    context: {},
  });
  if (!resp.ok) throw new Error(`read ${MODEL} failed: ${JSON.stringify(resp.error || resp.data)}`);
  const records = Array.isArray(resp.data?.records) ? resp.data.records : [];
  return records[0] || null;
}

async function loadContract(page, renderProfile = 'edit') {
  const resp = await intentRequest(page, 'ui.contract', {
    op: 'action_open',
    action_id: ACTION_ID,
    record_id: RECORD_ID,
    render_profile: renderProfile,
    contract_surface: 'user',
  });
  if (!resp.ok) throw new Error(`ui.contract failed: ${JSON.stringify(resp.error || resp.data)}`);
  return resp.data || {};
}

async function openForm(page, idPart = RECORD_ID) {
  const route = idPart === 'new' ? 'f' : 'r';
  await page.goto(`${FRONTEND_URL}/${route}/${encodeURIComponent(MODEL)}/${idPart}?action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function domSnapshot(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const shell = document.querySelector('.template-layout-shell');
    const controls = Array.from(document.querySelectorAll('.template-layout-shell input, .template-layout-shell textarea, .template-layout-shell select'));
    const enabledControls = controls.filter((node) => !node.disabled && !node.readOnly);
    const primaryButtons = Array.from(document.querySelectorAll('.template-page-header-actions button.primary'));
    const enabledPrimaryButtons = primaryButtons.filter((node) => !node.disabled).map((node) => clean(node.textContent));
    return {
      url: window.location.href,
      title: clean(document.querySelector('.template-page-title, h1, .title')?.textContent || ''),
      labels: Array.from(document.querySelectorAll('.field .label')).map((node) => clean(node.textContent)).filter(Boolean),
      input_count: controls.length,
      enabled_input_count: enabledControls.length,
      readonly_count: document.querySelectorAll('.readonly-value, .readonly-field, .form-readonly, .native-readonly').length,
      enabled_primary_buttons: enabledPrimaryButtons,
      visible_error: clean(document.querySelector('.status-panel.error, .validation-error, .submission-feedback--error')?.textContent || ''),
      text_sample: clean(shell?.textContent || '').slice(0, 1200),
    };
  });
}

function contractFacts(contract) {
  const fields = contract.fields && typeof contract.fields === 'object' ? contract.fields : {};
  const form = contract.views?.form && typeof contract.views.form === 'object' ? contract.views.form : {};
  const rights = contract.permissions?.effective?.rights || {};
  return {
    render_profile: normalize(contract.render_profile || contract.head?.render_profile),
    rights,
    field_count: Object.keys(fields).length,
    has_form: Boolean(form),
    header_buttons: Array.isArray(form.header_buttons) ? form.header_buttons.length : 0,
    create: rights.create === true,
    write: rights.write === true,
    unlink: rights.unlink === true,
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  attachConsoleCapture(page);
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(page);
    const record = await readRecord(page);
    summary.record = record;
    const contract = await loadContract(page, 'edit');
    const facts = contractFacts(contract);
    summary.contract = facts;

    await openForm(page);
    const initial = await domSnapshot(page);
    await page.screenshot({ path: path.join(outDir, 'legacy_readonly_form.png'), fullPage: true }).catch(() => {});

    const expectedTexts = [
      record?.document_no,
      record?.legacy_project_name,
      record?.income_category,
      record?.import_batch,
      String(record?.source_amount || ''),
    ].map(normalize).filter(Boolean);

    summary.checks.push({
      path_id: 'M4-P02/P23',
      name: 'legacy projection form displays persisted business facts',
      status: expectedTexts.every((text) => initial.text_sample.includes(text)) && !initial.visible_error ? 'pass' : 'fail',
      expected_texts: expectedTexts,
      dom: initial,
    });

    summary.checks.push({
      path_id: 'M4-P04/P05',
      name: 'legacy projection form is read-only in custom renderer',
      status: initial.enabled_input_count === 0
        && !initial.enabled_primary_buttons.some((text) => /保存|创建|提交|确认/.test(text))
        ? 'pass'
        : 'fail',
      dom: initial,
      contract_rights: facts.rights,
    });

    const deniedCreate = await intentRequest(page, 'api.data', {
      op: 'create',
      model: MODEL,
      vals: {
        document_no: `readonly-create-probe-${Date.now()}`,
      },
      context: {},
    });
    const deniedWrite = await intentRequest(page, 'api.data', {
      op: 'write',
      model: MODEL,
      ids: [0],
      vals: {
        note: `readonly-write-probe-${Date.now()}`,
      },
      context: {},
    });
    summary.checks.push({
      path_id: 'M4-P04/P05/P20',
      name: 'api.data create/write is denied by backend readonly projection policy',
      status: !deniedCreate.ok
        && !deniedWrite.ok
        && deniedCreate.error?.reason_code === READONLY_MUTATION_REASON
        && deniedWrite.error?.reason_code === READONLY_MUTATION_REASON
        ? 'pass'
        : 'fail',
      create_response: deniedCreate,
      write_response: deniedWrite,
      expected_reason_code: READONLY_MUTATION_REASON,
    });

    summary.checks.push({
      path_id: 'M4-P26',
      name: 'legacy projection field labels are localized by backend contract',
      status: EXPECTED_FIELD_LABELS.every((label) => initial.labels.includes(label))
        && !ENGLISH_FIELD_LABEL_RE.test(initial.labels.join(' '))
        ? 'pass'
        : 'fail',
      expected_labels: EXPECTED_FIELD_LABELS,
      actual_labels: initial.labels,
      english_leak: ENGLISH_FIELD_LABEL_RE.test(initial.labels.join(' ')),
    });

    await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
    await openForm(page);
    const afterReload = await domSnapshot(page);
    await page.goto(`${FRONTEND_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await openForm(page);
    const afterDeepLink = await domSnapshot(page);
    summary.checks.push({
      path_id: 'M4-P25',
      name: 'legacy projection form survives reload and direct deep link recovery',
      status: !afterReload.visible_error
        && !afterDeepLink.visible_error
        && expectedTexts.every((text) => afterReload.text_sample.includes(text))
        && expectedTexts.every((text) => afterDeepLink.text_sample.includes(text))
        ? 'pass'
        : 'fail',
      after_reload: afterReload,
      after_deep_link: afterDeepLink,
    });

    await openForm(page, 'new');
    const createAttempt = await domSnapshot(page);
    summary.checks.push({
      path_id: 'M4-P03/P05',
      name: 'direct create route does not expose an enabled create workflow for legacy projection',
      status: createAttempt.visible_error
        || (
          createAttempt.enabled_input_count === 0
          && !createAttempt.enabled_primary_buttons.some((text) => /保存|创建|提交|确认/.test(text))
        )
        ? 'pass'
        : 'fail',
      create_attempt: createAttempt,
    });

    summary.console_errors = page.__consoleErrors || [];
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }

  summary.pass = summary.checks.every((row) => row.status === 'pass')
    && (summary.console_errors || []).length === 0;
  writeJson('summary.json', summary);
  console.log(`[form_m4_legacy_readonly_acceptance] artifacts=${outDir}`);
  console.log(JSON.stringify({
    pass: summary.pass,
    checks: summary.checks.map((row) => ({ name: row.name, status: row.status })),
    console_errors: (summary.console_errors || []).length,
  }, null, 2));
  if (!summary.pass) process.exit(1);
}

main().catch((err) => {
  const summary = {
    pass: false,
    error: err instanceof Error ? err.message : String(err),
    artifact_dir: outDir,
  };
  writeJson('summary.json', summary);
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
});
