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
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const CASES = [
  {
    id: 'P26-M1',
    login: 'wutao',
    model: 'project.project',
    recordId: 771,
    actionId: 506,
    expectedStatusbar: ['草稿', '在建', '停工', '竣工', '结算中', '保修期', '关闭'],
  },
  {
    id: 'P26-M2',
    login: 'wutao',
    model: 'payment.request',
    recordId: 28489,
    actionId: 585,
    expectedStatusbar: ['草稿', '提交', '审批中', '已批准', '已驳回', '已完成', '已取消'],
  },
  {
    id: 'P26-M3',
    login: 'caisiqi',
    model: 'purchase.order',
    recordId: 9,
    actionId: 549,
    expectedStatusbar: ['询价', '发送询价', '待批准', '采购订单', '已锁定', '已取消'],
  },
  {
    id: 'P26-M4',
    login: 'wutao',
    model: 'sc.legacy.receipt.income.fact',
    recordId: 7220,
    actionId: 561,
    expectedFieldLabels: ['单据日期', '单据编号', '来源类别', '收支方向', '旧库状态', '收入类别', '项目', '往来单位', '原始金额', '旧库项目', '旧库项目名称', '旧库往来单位', '旧库往来单位名称', '旧库来源表', '旧库记录', '旧库序号', '导入批次', '备注'],
  },
];

const ENGLISH_LEAK_RE = /\b(RFQ|Sent|To Approve|Purchase Order|Locked|Cancelled|Draft|Approved|Rejected|Done|Cancel|Document Date|Document No|Source Family|Legacy State|Income Category|Source Amount|Legacy Project|Legacy Partner|Import Batch)\b/;
const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-localization', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function sameLabels(actual, expected) {
  return expected.every((label) => actual.includes(label));
}

async function login(page, loginName) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
}

async function intentRequest(page, intent, params) {
  const token = await page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
  return page.evaluate(async ({ dbName, authToken, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: authToken ? `Bearer ${authToken}` : '',
        'X-Trace-Id': `form-localization-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
    };
  }, { dbName: DB_NAME, authToken: token, intentName: intent, payload: params });
}

async function runCase(browser, spec) {
  const context = await browser.newContext({ locale: 'zh-CN', viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));

  try {
    await login(page, spec.login);
    const contractResp = await intentRequest(page, 'ui.contract', {
      op: 'model',
      model: spec.model,
      view_type: 'form',
      action_id: spec.actionId,
      record_id: spec.recordId,
      render_profile: 'edit',
      force_refresh: true,
    });
    const statusbar = contractResp.data?.views?.form?.statusbar || {};
    const contractLabels = Array.isArray(statusbar.states)
      ? statusbar.states.map((row) => normalize(row.label)).filter(Boolean)
      : [];
    const statusField = normalize(statusbar.field);
    const selection = statusField ? contractResp.data?.fields?.[statusField]?.selection : [];
    const selectionLabels = Array.isArray(selection)
      ? selection.map((row) => normalize(Array.isArray(row) ? row[1] : '')).filter(Boolean)
      : [];

    await page.goto(`${FRONTEND_URL}/r/${spec.model}/${spec.recordId}?action_id=${spec.actionId}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
    await page.waitForFunction((needsStatusbar) => {
      const shellText = String(document.querySelector('.template-layout-shell')?.textContent || '');
      if (shellText.includes('页面加载失败') || shellText.includes('页面渲染失败')) return true;
      if (shellText.includes('正在加载页面')) return false;
      if (!needsStatusbar) return shellText.length > 0;
      return document.querySelectorAll('.native-statusbar-step').length > 0;
    }, Boolean(spec.expectedStatusbar), { timeout: 30000 });
    const domLabels = await page.locator('.native-statusbar-step').evaluateAll((nodes) =>
      nodes.map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim()).filter(Boolean),
    );
    const domFieldLabels = await page.locator('.field .label').evaluateAll((nodes) =>
      nodes.map((node) => String(node.textContent || '').replace(/\s+/g, ' ').trim()).filter(Boolean),
    );
    const fieldLabels = contractResp.data?.fields && typeof contractResp.data.fields === 'object'
      ? Object.values(contractResp.data.fields)
        .map((row) => normalize(row && typeof row === 'object' ? row.string || row.label : ''))
        .filter(Boolean)
      : [];
    const expectedStatusbar = Array.isArray(spec.expectedStatusbar) ? spec.expectedStatusbar : [];
    const expectedFieldLabels = Array.isArray(spec.expectedFieldLabels) ? spec.expectedFieldLabels : [];
    const joined = expectedStatusbar.length
      ? [...contractLabels, ...selectionLabels, ...domLabels].join(' ')
      : [...domFieldLabels, ...fieldLabels.filter((label) => expectedFieldLabels.includes(label))].join(' ');
    const contractLocalized = expectedStatusbar.length
      ? (sameLabels(contractLabels, expectedStatusbar) || sameLabels(selectionLabels, expectedStatusbar))
      : sameLabels(fieldLabels, expectedFieldLabels);
    const domLocalized = expectedStatusbar.length
      ? sameLabels(domLabels, expectedStatusbar)
      : sameLabels(domFieldLabels, expectedFieldLabels);
    const pass = contractResp.ok
      && contractLocalized
      && domLocalized
      && !ENGLISH_LEAK_RE.test(joined)
      && consoleErrors.length === 0;
    return {
      id: spec.id,
      login: spec.login,
      model: spec.model,
      record_id: spec.recordId,
      action_id: spec.actionId,
      status: pass ? 'pass' : 'fail',
      expected_statusbar: expectedStatusbar,
      expected_field_labels: expectedFieldLabels,
      contract_statusbar_labels: contractLabels,
      field_state_selection_labels: selectionLabels,
      dom_statusbar_labels: domLabels,
      contract_field_labels: fieldLabels,
      dom_field_labels: domFieldLabels,
      english_leak: ENGLISH_LEAK_RE.test(joined),
      console_errors: consoleErrors,
    };
  } finally {
    await context.close();
  }
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const summary = {
    pass: false,
    db: DB_NAME,
    frontend_url: FRONTEND_URL,
    artifact_dir: outDir,
    paths: [],
  };
  try {
    for (const spec of CASES) {
      summary.paths.push(await runCase(browser, spec));
    }
    summary.pass = summary.paths.every((row) => row.status === 'pass');
    writeJson('summary.json', summary);
    console.log(JSON.stringify(summary, null, 2));
    process.exit(summary.pass ? 0 : 1);
  } catch (err) {
    summary.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', summary);
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
