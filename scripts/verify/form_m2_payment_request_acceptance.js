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
const APPROVER_LOGIN = process.env.APPROVER_LOGIN || 'chenshuai';
const APPROVER_PASSWORD = process.env.APPROVER_PASSWORD || '123456';
const RECORD_ID = Number(process.env.PAYMENT_REQUEST_ID || 28489);
const ACTION_ID = Number(process.env.ACTION_ID || 585);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-m2-payment-request', ts);

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
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

async function login(page, loginName = LOGIN, password = PASSWORD) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(password);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
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
        'X-Trace-Id': `form-m2-payment-${Date.now()}`,
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

async function domFacts(page) {
  return page.evaluate(() => {
    const text = (node) => String(node?.textContent || '').replace(/\s+/g, ' ').trim();
    return {
      url: window.location.href,
      statusbar_steps: Array.from(document.querySelectorAll('.native-statusbar-step')).map((node) => ({
        label: text(node),
        active: node.classList.contains('native-statusbar-step--active'),
      })),
      button_texts: Array.from(document.querySelectorAll('.template-layout-shell button')).map(text).filter(Boolean),
      visible_error: text(document.querySelector('.submission-feedback--warn, .status-panel.error, .validation-error')),
      text_sample: text(document.querySelector('.template-layout-shell')).slice(0, 800),
    };
  });
}

async function uploadAttachmentViaBrowser(page) {
  const fileName = `M2 payment request attachment acceptance ${Date.now()}.txt`;
  const fileContent = `M2 payment request attachment acceptance ${new Date().toISOString()}\n`;
  const filePath = path.join(outDir, fileName);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(filePath, fileContent, 'utf8');

  const chatter = page.locator('.native-chatter-block').first();
  await chatter.waitFor({ timeout: 15000 });
  const input = chatter.locator('.native-attachment-upload input[type="file"]').first();
  await input.waitFor({ state: 'attached', timeout: 15000 });
  await input.setInputFiles(filePath);
  await page.getByText(fileName, { exact: false }).waitFor({ timeout: 20000 });
  const entry = page.locator('li.native-chatter-entry').filter({ hasText: fileName }).first();
  const downloadButton = entry.locator('button.native-attachment-download').first();
  await downloadButton.waitFor({ timeout: 15000 });
  const downloadPromise = page.waitForEvent('download');
  await downloadButton.click();
  const download = await downloadPromise;
  const downloadedPath = path.join(outDir, `downloaded-${download.suggestedFilename() || fileName}`);
  await download.saveAs(downloadedPath);
  const downloadedContent = fs.readFileSync(downloadedPath, 'utf8');
  return {
    file_name: fileName,
    suggested_filename: download.suggestedFilename(),
    content_matched: downloadedContent === fileContent,
  };
}

function collectBusinessActions(contract) {
  const form = contract?.views?.form || {};
  const rows = Array.isArray(form.business_actions) ? form.business_actions : [];
  const buttons = Array.isArray(form.header_buttons) ? form.header_buttons : [];
  const submit = buttons.find((row) => row && (row.key === 'payment_submit' || row.name === 'action_submit')) || {};
  const approve = buttons.find((row) => row && (row.key === 'payment_approve' || row.name === 'validate_tier' || row.name === 'action_approval_decision')) || {};
  return {
    count: rows.length,
    actions: rows.map((row) => ({
      key: normalize(row.key),
      action_key: normalize(row.action_key),
      method: normalize(row.method),
      allowed: row.allowed === true,
      reason_code: normalize(row.reason_code),
      intent: normalize(row.intent),
      has_mutation: Boolean(row.mutation && typeof row.mutation === 'object'),
      suggested_action: normalize(row.suggested_action),
      handoff_required: row.handoff_required === true,
      warning_message: normalize(row.warning_message),
      advisory_reason_codes: Array.isArray(row.advisory_reason_codes)
        ? row.advisory_reason_codes.map(normalize).filter(Boolean)
        : [],
      force_block_available: row.force_block_available === true,
    })),
    submit_button: {
      key: normalize(submit.key),
      name: normalize(submit.name),
      allowed: submit.allowed === true,
      reason_code: normalize(submit.reason_code),
      suggested_action: normalize(submit.suggested_action),
      has_business_action: Boolean(submit.business_action),
      has_mutation: Boolean(submit.mutation && typeof submit.mutation === 'object'),
      warning_message: normalize(submit.warning_message),
      advisory_reason_codes: Array.isArray(submit.advisory_reason_codes)
        ? submit.advisory_reason_codes.map(normalize).filter(Boolean)
        : [],
      force_block_available: submit.force_block_available === true,
    },
    approve_button: {
      key: normalize(approve.key),
      name: normalize(approve.name),
      allowed: approve.allowed === true,
      reason_code: normalize(approve.reason_code),
      suggested_action: normalize(approve.suggested_action),
      has_business_action: Boolean(approve.business_action),
      has_mutation: Boolean(approve.mutation && typeof approve.mutation === 'object'),
      warning_message: normalize(approve.warning_message),
      advisory_reason_codes: Array.isArray(approve.advisory_reason_codes)
        ? approve.advisory_reason_codes.map(normalize).filter(Boolean)
        : [],
      force_block_available: approve.force_block_available === true,
    },
  };
}

function collectWarningCodes(executeResp) {
  const actionResult = executeResp?.data?.action_result || {};
  const warnings = actionResult.warnings || executeResp?.data?.warnings || {};
  const rows = [];
  for (const value of Object.values(warnings)) {
    if (Array.isArray(value)) rows.push(...value);
  }
  return rows.map((row) => normalize(row && row.reason_code)).filter(Boolean);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  attachConsoleCapture(page);

  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'payment.request',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    artifact_dir: outDir,
    checks: [],
  };

  try {
    await login(page);

    const contractResp = await intentRequest(page, 'ui.contract', {
      action_id: ACTION_ID,
      record_id: RECORD_ID,
      render_profile: 'edit',
    });
    const business = collectBusinessActions(contractResp.data);
    const submit = business.submit_button;
    const contractCheck = {
      path_id: 'M2-P15-P20',
      name: 'payment request business actions contract',
      status: contractResp.ok
        && business.count > 0
        && submit.has_business_action
        && submit.has_mutation
        && submit.allowed === true
        && submit.reason_code === 'OK'
        && submit.advisory_reason_codes.includes('PAYMENT_ATTACHMENTS_REQUIRED')
        && submit.warning_message.includes('附件')
        ? 'pass'
        : 'fail',
      business,
    };
    summary.checks.push(contractCheck);

    const executeResp = await intentRequest(page, 'payment.request.execute', {
      id: RECORD_ID,
      action: 'submit',
    });
    const executeWarningCodes = collectWarningCodes(executeResp);
    const executeCheck = {
      path_id: 'M2-P20',
      name: 'submit allowed with backend advisory warnings',
      status: executeResp.ok === true
        && executeResp.status === 200
        && executeWarningCodes.includes('PAYMENT_ATTACHMENTS_REQUIRED')
        ? 'pass'
        : 'fail',
      execute: {
        status: executeResp.status,
        ok: executeResp.ok,
        reason_code: normalize(executeResp.error.reason_code || executeResp.data.reason_code),
        warning_reason_codes: executeWarningCodes,
        message: normalize(executeResp.error.message || executeResp.data.message),
      },
    };
    summary.checks.push(executeCheck);

    await page.goto(`${FRONTEND_URL}/r/payment.request/${RECORD_ID}?action_id=${ACTION_ID}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
    await page.waitForFunction(() => {
      const shell = document.querySelector('.template-layout-shell');
      const text = String(shell?.textContent || '');
      if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
      return !text.includes('正在加载页面');
    }, null, { timeout: 30000 });
    const dom = await domFacts(page);
    const renderCheck = {
      path_id: 'M2-P02-P15',
      name: 'payment request form renderable with statusbar/actions',
      status: dom.statusbar_steps.length > 0
        && dom.button_texts.some((text) => /提交|审批|批准|完成|取消/.test(text))
        ? 'pass'
        : 'fail',
      dom,
    };
    summary.checks.push(renderCheck);

    const approverPage = await browser.newPage({ viewport: { width: 1440, height: 980 } });
    attachConsoleCapture(approverPage);
    await login(approverPage, APPROVER_LOGIN, APPROVER_PASSWORD);
    const approverContractResp = await intentRequest(approverPage, 'ui.contract', {
      action_id: ACTION_ID,
      record_id: RECORD_ID,
      render_profile: 'edit',
    });
    const approverBusiness = collectBusinessActions(approverContractResp.data);
    const approve = approverBusiness.approve_button;
    const approverContractCheck = {
      path_id: 'M2-P21-P22',
      name: 'approver contract allows approval decision with advisory warnings',
      status: approverContractResp.ok
        && approve.allowed === true
        && approve.reason_code === 'OK'
        && approve.advisory_reason_codes.includes('P0_PAYMENT_SETTLEMENT_NOT_READY')
        && approve.advisory_reason_codes.includes('P0_PAYMENT_FUNDING_NOT_READY')
        ? 'pass'
        : 'fail',
      business: approverBusiness,
    };
    summary.checks.push(approverContractCheck);

    const approveResp = await intentRequest(approverPage, 'payment.request.execute', {
      id: RECORD_ID,
      action: 'approve',
    });
    const approveWarningCodes = collectWarningCodes(approveResp);
    const approveExecuteCheck = {
      path_id: 'M2-P21-P22',
      name: 'approval decision allowed with backend advisory warnings',
      status: approveResp.ok === true
        && approveResp.status === 200
        && approveWarningCodes.includes('P0_PAYMENT_SETTLEMENT_NOT_READY')
        && approveWarningCodes.includes('P0_PAYMENT_FUNDING_NOT_READY')
        ? 'pass'
        : 'fail',
      execute: {
        status: approveResp.status,
        ok: approveResp.ok,
        reason_code: normalize(approveResp.error.reason_code || approveResp.data.reason_code),
        payment_request_state: normalize(approveResp.data?.payment_request?.state),
        warning_reason_codes: approveWarningCodes,
        message: normalize(approveResp.error.message || approveResp.data.message),
      },
    };
    if (approveExecuteCheck.status === 'pass' && approveExecuteCheck.execute.payment_request_state !== 'approved') {
      approveExecuteCheck.status = 'fail';
    }
    summary.checks.push(approveExecuteCheck);

    const financeAfterApprovalResp = await intentRequest(page, 'ui.contract', {
      action_id: ACTION_ID,
      record_id: RECORD_ID,
      render_profile: 'edit',
    });
    const financeAfterApprovalBusiness = collectBusinessActions(financeAfterApprovalResp.data);
    const doneAction = financeAfterApprovalBusiness.actions.find((row) => row.action_key === 'done') || {};
    const doneContractCheck = {
      path_id: 'M2-P22',
      name: 'done action allowed with precise unpaid advisory after approval',
      status: financeAfterApprovalResp.ok
        && doneAction.allowed === true
        && doneAction.reason_code === 'OK'
        && doneAction.suggested_action === 'complete_payment_execution'
        && Array.isArray(doneAction.advisory_reason_codes)
        && doneAction.advisory_reason_codes.includes('P0_PAYMENT_NOT_FULLY_PAID')
        ? 'pass'
        : 'fail',
      business: {
        done_action: doneAction,
      },
    };
    summary.checks.push(doneContractCheck);

    const doneResp = await intentRequest(page, 'payment.request.execute', {
      id: RECORD_ID,
      action: 'done',
    });
    const doneWarningCodes = collectWarningCodes(doneResp);
    const doneExecuteCheck = {
      path_id: 'M2-P22',
      name: 'done action creates payment ledger and completes request',
      status: doneResp.ok === true
        && doneResp.status === 200
        && normalize(doneResp.data?.payment_request?.state) === 'done'
        && doneWarningCodes.includes('P0_PAYMENT_NOT_FULLY_PAID')
        ? 'pass'
        : 'fail',
      execute: {
        status: doneResp.status,
        ok: doneResp.ok,
        reason_code: normalize(doneResp.error.reason_code || doneResp.data.reason_code),
        payment_request_state: normalize(doneResp.data?.payment_request?.state),
        warning_reason_codes: doneWarningCodes,
        message: normalize(doneResp.error.message || doneResp.data.message),
      },
    };
    summary.checks.push(doneExecuteCheck);
    summary.console_errors_approver = approverPage.__consoleErrors || [];
    await approverPage.close();

    summary.cleanup = {
      model: 'payment.request',
      record_id: RECORD_ID,
      state_after_submit_expected: 'submit',
      restore_state: 'draft',
    };

    const consoleErrors = [...(page.__consoleErrors || []), ...(summary.console_errors_approver || [])];
    const unexpectedConsoleErrors = consoleErrors;
    summary.console_errors = consoleErrors;
    summary.expected_console_errors = [];
    summary.unexpected_console_errors = unexpectedConsoleErrors;
    summary.pass = summary.checks.every((row) => row.status === 'pass') && unexpectedConsoleErrors.length === 0;
    writeJson('summary.json', summary);
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify(summary, null, 2));
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
