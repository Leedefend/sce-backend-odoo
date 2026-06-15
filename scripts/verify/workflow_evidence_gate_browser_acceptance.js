#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

const repoRoot = path.resolve(__dirname, '..', '..');
const requireFromWeb = createRequire(path.join(repoRoot, 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || process.env.DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || process.env.LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || process.env.PASSWORD || '123456';
const MODEL = process.env.MODEL || 'sc.expense.claim';
const RECORD_ID = Number(process.env.RECORD_ID || 0);
const ACTION_ID = Number(process.env.ACTION_ID || 0);
const MENU_ID = Number(process.env.MENU_ID || 0);
const EXPECTED_TEXT = process.env.EXPECTED_TEXT || '扣款登记必须填写至少一条扣款单明细后才能提交、批准或完成。';
const EXPECTED_REASON_CODES = (process.env.EXPECTED_REASON_CODE || process.env.EXPECTED_REASON_CODES || '')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);
const TARGET_BUTTON_PATTERN = process.env.TARGET_BUTTON_PATTERN || '提交|提交审批';
const TARGET_BUTTON_LABEL = process.env.TARGET_BUTTON_LABEL || TARGET_BUTTON_PATTERN;
const FORBIDDEN_BUTTON_PATTERN = process.env.FORBIDDEN_BUTTON_PATTERN || '';
const UNIQUE_BUTTON_PATTERN = process.env.UNIQUE_BUTTON_PATTERN || '';
const EXPECT_EVIDENCE_BLOCK = process.env.EXPECT_EVIDENCE_BLOCK !== '0';
const EXPECT_WORKFLOW_CONTRACT = process.env.EXPECT_WORKFLOW_CONTRACT !== '0';
const CLICK_BUTTON_PATTERN = process.env.CLICK_BUTTON_PATTERN || '';
const EXPECT_EXECUTE_METHOD = process.env.EXPECT_EXECUTE_METHOD || '';
const WORKFLOW_BUTTON_LABELS = (process.env.WORKFLOW_BUTTON_LABELS || '提交审批,审批通过,审批驳回,批准,完成,已付款,已收款,已登记,对账完成,开始执行,重置为草稿')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts/workflow-evidence-gate-browser';

function outPath(name) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  return path.join(ARTIFACTS_DIR, name);
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.locator('input').nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator('input').count() >= 3) {
    const dbInput = page.locator('input').nth(2);
    if (await dbInput.isEnabled().catch(() => false)) {
      await dbInput.fill(DB_NAME);
    }
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 60000 });
}

async function main() {
  if (!RECORD_ID) {
    throw new Error('RECORD_ID is required');
  }
  const browser = await launchBrowser();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  const intentResponses = [];
  const intentRequests = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));
  page.on('request', (request) => {
    const url = request.url();
    if (!url.includes('/api/v1/intent')) return;
    try {
      const payload = request.postDataJSON();
      if (!payload || typeof payload !== 'object') return;
      const params = payload.params && typeof payload.params === 'object' && !Array.isArray(payload.params)
        ? payload.params
        : {};
      const context = params.context && typeof params.context === 'object' && !Array.isArray(params.context)
        ? params.context
        : {};
      intentRequests.push({
        intent: payload.intent || '',
        actionId: params.action_id || params.actionId || '',
        model: params.model || '',
        viewType: params.view_type || params.viewType || '',
        recordId: params.record_id || params.recordId || '',
        buttonName: params.button && typeof params.button === 'object' ? params.button.name || '' : '',
        buttonType: params.button && typeof params.button === 'object' ? params.button.type || '' : '',
        renderProfile: params.render_profile || params.renderProfile || '',
        contextKeys: Object.keys(context).sort(),
      });
    } catch (_err) {
      intentRequests.push({ parseError: true });
    }
  });
  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/api/v1/intent')) return;
    try {
      const body = await response.json();
      const data = body && body.data && typeof body.data === 'object' ? body.data : {};
      const rawV2 = data.__unified_page_contract_v2 && typeof data.__unified_page_contract_v2 === 'object'
        ? data.__unified_page_contract_v2
        : {};
      const workflow = data.workflowContract
        || (data.runtimeContract && data.runtimeContract.workflowContract)
        || rawV2.workflowContract
        || (rawV2.runtimeContract && rawV2.runtimeContract.workflowContract)
        || null;
      const pageInfo = data.pageInfo && typeof data.pageInfo === 'object'
        ? data.pageInfo
        : rawV2.pageInfo && typeof rawV2.pageInfo === 'object'
          ? rawV2.pageInfo
          : {};
      intentResponses.push({
        status: response.status(),
        intent: body && body.meta ? body.meta.intent : '',
        source: body && body.meta ? body.meta.source_intent || body.meta.source_kind || '' : '',
        model: data.model || pageInfo.model || (workflow && workflow.model) || '',
        viewType: data.view_type || pageInfo.viewType || '',
        recordId: data.record_id || pageInfo.recordId || pageInfo.record_id || (workflow && workflow.record_id) || '',
        workflowModel: workflow && workflow.model || '',
        workflowRecordId: workflow && workflow.record_id || '',
        dataKeys: Object.keys(data).slice(0, 30),
        rawV2Keys: Object.keys(rawV2).slice(0, 30),
        hasDataWorkflowContract: Boolean(data.workflowContract),
        hasDataRuntimeWorkflowContract: Boolean(data.runtimeContract && data.runtimeContract.workflowContract),
        hasRawWorkflowContract: Boolean(rawV2.workflowContract),
        hasRawRuntimeWorkflowContract: Boolean(rawV2.runtimeContract && rawV2.runtimeContract.workflowContract),
        hasWorkflowContract: Boolean(workflow),
        evidenceCount: workflow && Array.isArray(workflow.evidenceGate) ? workflow.evidenceGate.length : 0,
        evidenceReasonCodes: workflow && Array.isArray(workflow.evidenceGate)
          ? workflow.evidenceGate.map((item) => item && (item.reasonCode || item.reason_code)).filter(Boolean)
          : [],
        availableActionKeys: workflow && Array.isArray(workflow.availableActions)
          ? workflow.availableActions.map((item) => item && item.key).filter(Boolean)
          : [],
      });
    } catch (_err) {
      intentResponses.push({ status: response.status(), parseError: true });
    }
  });
  try {
    await login(page);
    const params = new URLSearchParams({ db: DB_NAME, t: String(Date.now()) });
    if (ACTION_ID) params.set('action_id', String(ACTION_ID));
    if (MENU_ID) params.set('menu_id', String(MENU_ID));
    await page.goto(`${FRONTEND_URL}/r/${encodeURIComponent(MODEL)}/${RECORD_ID}?${params.toString()}`, {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    if (EXPECT_EVIDENCE_BLOCK) {
      await page.getByText('办理前置条件', { exact: false }).waitFor({ timeout: 60000 });
      await page.getByText(EXPECTED_TEXT, { exact: false }).waitFor({ timeout: 60000 });
    }
    const targetButtonRegex = new RegExp(TARGET_BUTTON_PATTERN);
    const targetButtons = await page.locator('button', { hasText: targetButtonRegex }).evaluateAll((buttons) => (
      buttons.map((button) => ({
        text: button.textContent.trim(),
        disabled: button.disabled,
        title: button.getAttribute('title') || '',
      }))
    ));
    if (EXPECT_EVIDENCE_BLOCK) {
      const actionableTargetButtons = targetButtons.filter((button) => !button.text.startsWith('已'));
      if (!actionableTargetButtons.length) {
        throw new Error(`missing actionable target button: ${TARGET_BUTTON_LABEL}`);
      }
      const enabledTarget = actionableTargetButtons.find((button) => !button.disabled);
      if (enabledTarget) {
        throw new Error(`target button should be disabled by workflow gate: ${enabledTarget.text}`);
      }
      const targetMissingTitle = actionableTargetButtons.find((button) => !button.title.includes(EXPECTED_TEXT));
      if (targetMissingTitle) {
        throw new Error(`target button missing blocked title: ${targetMissingTitle.text}`);
      }
    }
    const uniqueButtonRegex = UNIQUE_BUTTON_PATTERN ? new RegExp(UNIQUE_BUTTON_PATTERN) : null;
    const uniqueButtons = uniqueButtonRegex
      ? await page.locator('button', { hasText: uniqueButtonRegex }).evaluateAll((buttons) => (
        buttons.map((button) => ({
          text: button.textContent.trim().replace(/\s+/g, ' '),
          disabled: button.disabled,
          title: button.getAttribute('title') || '',
        }))
      ))
      : [];
    if (uniqueButtonRegex && uniqueButtons.length !== 1) {
      throw new Error(`expected exactly one button matching ${UNIQUE_BUTTON_PATTERN}, got ${uniqueButtons.length}: ${uniqueButtons.map((button) => button.text).join(', ')}`);
    }
    const forbiddenButtonRegex = FORBIDDEN_BUTTON_PATTERN ? new RegExp(FORBIDDEN_BUTTON_PATTERN) : null;
    const forbiddenButtons = forbiddenButtonRegex
      ? await page.locator('button', { hasText: forbiddenButtonRegex }).evaluateAll((buttons) => (
        buttons.map((button) => ({
          text: button.textContent.trim().replace(/\s+/g, ' '),
          disabled: button.disabled,
          title: button.getAttribute('title') || '',
        }))
      ))
      : [];
    if (forbiddenButtons.length) {
      throw new Error(`forbidden workflow buttons should be hidden: ${forbiddenButtons.map((button) => button.text).join(', ')}`);
    }
    const workflowButtons = await page.locator('button.native-action-btn').evaluateAll((buttons, labels) => (
      buttons
        .map((button) => ({
          text: button.textContent.trim().replace(/\s+/g, ' '),
          disabled: button.disabled,
          title: button.getAttribute('title') || '',
        }))
        .filter((button) => labels.includes(button.text))
    ), WORKFLOW_BUTTON_LABELS);
    const targetWorkflowButtons = workflowButtons.filter((button) => targetButtonRegex.test(button.text));
    if (EXPECT_EVIDENCE_BLOCK) {
      const enabledBlockedWorkflowButton = targetWorkflowButtons.find((button) => !button.disabled);
      if (enabledBlockedWorkflowButton) {
        throw new Error(`workflow button should be disabled by evidence gate: ${enabledBlockedWorkflowButton.text}`);
      }
      const missingTitleButton = targetWorkflowButtons.find((button) => !button.title.includes(EXPECTED_TEXT));
      if (missingTitleButton) {
        throw new Error(`workflow button missing blocked title: ${missingTitleButton.text}`);
      }
    }
    const targetWorkflowResponses = intentResponses.filter((item) => (
      item
      && item.hasWorkflowContract
      && (item.model === MODEL || item.workflowModel === MODEL)
      && (
        String(item.recordId || '') === String(RECORD_ID)
        || String(item.workflowRecordId || '') === String(RECORD_ID)
      )
    ));
    if (EXPECT_WORKFLOW_CONTRACT && !targetWorkflowResponses.length) {
      const targetResponses = intentResponses.filter((item) => (
        item
        && item.model === MODEL
        && (
          String(item.recordId || '') === String(RECORD_ID)
          || String(item.workflowRecordId || '') === String(RECORD_ID)
        )
      ));
      throw new Error(
        `target ui contract response missing workflowContract for ${MODEL}#${RECORD_ID}; `
        + `targetResponses=${JSON.stringify(targetResponses.map((item) => ({
          status: item.status,
          intent: item.intent,
          source: item.source,
          viewType: item.viewType,
          dataKeys: item.dataKeys,
          rawV2Keys: item.rawV2Keys,
        })))}`
      );
    }
    const targetEvidenceReasonCodes = Array.from(new Set(
      targetWorkflowResponses.flatMap((item) => Array.isArray(item.evidenceReasonCodes) ? item.evidenceReasonCodes : [])
    )).sort();
    const missingReasonCodes = EXPECTED_REASON_CODES.filter((code) => !targetEvidenceReasonCodes.includes(code));
    if (missingReasonCodes.length) {
      throw new Error(
        `target workflow evidence missing reason codes: ${missingReasonCodes.join(', ')}; `
        + `actual=${targetEvidenceReasonCodes.join(', ')}`
      );
    }
    let clickedButton = null;
    let executeButtonRequest = null;
    let executeButtonResponse = null;
    if (CLICK_BUTTON_PATTERN) {
      const clickRegex = new RegExp(CLICK_BUTTON_PATTERN);
      const button = page.locator('button', { hasText: clickRegex }).and(page.locator('button:not([disabled])')).first();
      await button.waitFor({ timeout: 30000 });
      clickedButton = {
        text: (await button.textContent()).trim().replace(/\s+/g, ' '),
        title: await button.getAttribute('title') || '',
      };
      const requestPromise = page.waitForRequest((request) => {
        if (!request.url().includes('/api/v1/intent')) return false;
        try {
          const payload = request.postDataJSON();
          if (!payload || payload.intent !== 'execute_button') return false;
          const params = payload.params && typeof payload.params === 'object' && !Array.isArray(payload.params)
            ? payload.params
            : {};
          const buttonPayload = params.button && typeof params.button === 'object' && !Array.isArray(params.button)
            ? params.button
            : {};
          if (EXPECT_EXECUTE_METHOD && buttonPayload.name !== EXPECT_EXECUTE_METHOD) return false;
          return true;
        } catch (_err) {
          return false;
        }
      }, { timeout: 30000 });
      const responsePromise = page.waitForResponse((response) => {
        if (!response.url().includes('/api/v1/intent')) return false;
        try {
          const payload = response.request().postDataJSON();
          if (!payload || payload.intent !== 'execute_button') return false;
          const params = payload.params && typeof payload.params === 'object' && !Array.isArray(payload.params)
            ? payload.params
            : {};
          const buttonPayload = params.button && typeof params.button === 'object' && !Array.isArray(params.button)
            ? params.button
            : {};
          if (EXPECT_EXECUTE_METHOD && buttonPayload.name !== EXPECT_EXECUTE_METHOD) return false;
          return true;
        } catch (_err) {
          return false;
        }
      }, { timeout: 30000 });
      await button.click();
      const request = await requestPromise;
      const payload = request.postDataJSON();
      executeButtonRequest = {
        intent: payload.intent,
        model: payload.params && payload.params.model,
        resId: payload.params && payload.params.res_id,
        button: payload.params && payload.params.button,
      };
      const response = await responsePromise;
      let responseBody = {};
      try {
        responseBody = await response.json();
      } catch (_err) {
        responseBody = {};
      }
      executeButtonResponse = {
        status: response.status(),
        ok: response.status() < 400,
        reasonCode: responseBody && responseBody.data && responseBody.data.result && responseBody.data.result.reason_code,
        message: responseBody && responseBody.data && responseBody.data.result && responseBody.data.result.message,
      };
      if (response.status() >= 400) {
        throw new Error(`execute_button response failed: status=${response.status()} reason=${executeButtonResponse.reasonCode || ''} message=${executeButtonResponse.message || ''}`);
      }
    }
    await page.screenshot({ path: outPath('workflow-evidence-gate.png'), fullPage: true });
    const result = {
      ok: true,
      url: page.url(),
      recordId: RECORD_ID,
      expectedText: EXPECTED_TEXT,
      expectedReasonCodes: EXPECTED_REASON_CODES,
      targetEvidenceReasonCodes,
      expectEvidenceBlock: EXPECT_EVIDENCE_BLOCK,
      expectWorkflowContract: EXPECT_WORKFLOW_CONTRACT,
      targetButtonPattern: TARGET_BUTTON_PATTERN,
      targetButtons,
      uniqueButtonPattern: UNIQUE_BUTTON_PATTERN,
      uniqueButtons,
      forbiddenButtonPattern: FORBIDDEN_BUTTON_PATTERN,
      forbiddenButtons,
      clickButtonPattern: CLICK_BUTTON_PATTERN,
      clickedButton,
      expectExecuteMethod: EXPECT_EXECUTE_METHOD,
      executeButtonRequest,
      executeButtonResponse,
      workflowButtons,
      targetWorkflowResponses,
      intentRequests,
      intentResponses,
      consoleErrors,
      screenshot: outPath('workflow-evidence-gate.png'),
    };
    fs.writeFileSync(outPath('workflow-evidence-gate.json'), JSON.stringify(result, null, 2), 'utf8');
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    const failure = {
      ok: false,
      url: page.url(),
      title: await page.title().catch(() => ''),
      text: await page.locator('body').innerText({ timeout: 2000 }).catch(() => ''),
      intentRequests,
      intentResponses,
      consoleErrors,
      screenshot: outPath('workflow-evidence-gate-failure.png'),
    };
    await page.screenshot({ path: failure.screenshot, fullPage: true }).catch(() => {});
    fs.writeFileSync(outPath('workflow-evidence-gate-failure.json'), JSON.stringify(failure, null, 2), 'utf8');
    throw err;
  } finally {
    await browser.close();
  }
}

async function launchBrowser() {
  try {
    const runtime = await import(pathToFileUrl(path.join(repoRoot, 'scripts/verify/playwright_runtime.mjs')));
    if (runtime && typeof runtime.launchChromium === 'function') {
      return await runtime.launchChromium({ headless: true });
    }
  } catch (_err) {
    // Fall back to Playwright's default launcher below.
  }
  return chromium.launch({ headless: true });
}

function pathToFileUrl(filePath) {
  const resolved = path.resolve(filePath).replace(/\\/g, '/');
  return `file://${resolved.startsWith('/') ? '' : '/'}${resolved}`;
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
