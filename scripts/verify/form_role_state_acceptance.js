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
const MODEL = process.env.MVP_MODEL || 'project.project';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ROLE_LOGINS = (process.env.ROLE_LOGINS || 'wutao,chenshuai,caisiqi,zhaowei,yangdesheng')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);

const STATE_RECORDS = (process.env.STATE_RECORDS || 'draft:771,in_progress:755')
  .split(',')
  .map((item) => {
    const [state, id] = item.split(':');
    return { state: String(state || '').trim(), id: Number(id || 0) };
  })
  .filter((item) => item.state && Number.isFinite(item.id) && item.id > 0);

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-role-state', ts);

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

async function login(page, loginName) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(loginName);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function openForm(page, recordId) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${recordId}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'domcontentloaded', timeout: 45000 },
  );
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.locator('.native-statusbar-step, .template-layout-shell input.input').first().waitFor({ timeout: 30000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const headers = { 'Content-Type': 'application/json', 'X-Trace-Id': `form-role-state-${Date.now()}` };
    if (bearer) headers.Authorization = `Bearer ${bearer}`;
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) {
      const message = body?.error?.message || body?.message || `intent ${intentName} failed`;
      throw new Error(message);
    }
    return body.data || body;
  }, { dbName: DB_NAME, authToken, intentName: intent, payload: params });
}

function statusbarStates(contract) {
  const form = contract?.views?.form || {};
  const raw = form.statusbar || contract?.statusbar || {};
  const rows = Array.isArray(raw.states)
    ? raw.states
    : Array.isArray(raw.values)
      ? raw.values
      : [];
  const normalized = rows.map((row) => ({
    value: String(row?.value ?? row?.key ?? row?.id ?? '').trim(),
    label: normalize(row?.label || row?.string || row?.name || row?.value),
  })).filter((row) => row.value || row.label);
  if (normalized.length) return normalized;

  const fields = contract?.fields && typeof contract.fields === 'object' ? contract.fields : {};
  const fieldName = String(raw.field || raw.name || 'lifecycle_state').trim();
  const descriptor = fields[fieldName] || fields.lifecycle_state || fields.state || {};
  const selection = Array.isArray(descriptor.selection) ? descriptor.selection : [];
  return selection.map((row) => {
    if (Array.isArray(row)) {
      return { value: String(row[0] ?? '').trim(), label: normalize(row[1] ?? row[0]) };
    }
    return {
      value: String(row?.value ?? row?.key ?? '').trim(),
      label: normalize(row?.label || row?.string || row?.name || row?.value || row?.key),
    };
  }).filter((row) => row.value && row.label);
}

function contractSurface(contract) {
  const form = contract?.views?.form || {};
  return {
    tabs: Array.isArray(form.layout)
      ? JSON.stringify(form.layout).match(/"type":"page"/g)?.length || 0
      : 0,
    statusbar_states: statusbarStates(contract),
    smart_buttons: Array.isArray(form.button_box) ? form.button_box.length : 0,
    chatter_enabled: Boolean(form.chatter?.enabled),
    attachments_enabled: Boolean(form.attachments?.enabled),
    permissions: contract?.permissions || {},
  };
}

async function domSurface(page) {
  return page.evaluate(() => {
    const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      statusbar: Array.from(document.querySelectorAll('.native-statusbar-step')).map((node) => ({
        label: clean(node.textContent),
        active: node.classList.contains('native-statusbar-step--active'),
        disabled: node.hasAttribute('disabled'),
      })),
      tabs: Array.from(document.querySelectorAll('button.native-tab')).map((node) => clean(node.textContent)).filter(Boolean),
      smart_buttons: Array.from(document.querySelectorAll('button.native-action-btn--smart')).map((node) => clean(node.textContent)).filter(Boolean),
      chatter_buttons: Array.from(document.querySelectorAll('.native-chatter-block button.chip-btn')).map((node) => clean(node.textContent)).filter(Boolean),
      attachment_upload: Boolean(document.querySelector('.native-attachment-upload input[type="file"]')),
      body_actions: Array.from(document.querySelectorAll('button.native-action-btn:not(.native-action-btn--smart)')).map((node) => clean(node.textContent)).filter(Boolean),
      visible_error: clean(document.querySelector('.status-panel.error, .validation-error')?.textContent || ''),
    };
  });
}

async function inspectRole(page, loginName, recordId) {
  const systemInit = await intentRequest(page, 'system.init', { with: ['workspace_home'] });
  const contract = await intentRequest(page, 'load_contract', {
    model: MODEL,
    view_type: 'form',
    include: 'all',
    action_id: Number(ACTION_ID),
    menu_id: Number(MENU_ID),
  });
  const surface = contractSurface(contract);
  await openForm(page, recordId);
  const dom = await domSurface(page);
  const roleSurface = systemInit?.role_surface || {};
  const statusbarOk = surface.statusbar_states.length === 0
    || dom.statusbar.length >= surface.statusbar_states.length;
  const smartOk = surface.smart_buttons === 0 || dom.smart_buttons.length > 0;
  const chatterOk = !surface.chatter_enabled || dom.chatter_buttons.includes('发送消息');
  const attachmentOk = !surface.attachments_enabled || dom.attachment_upload;
  return {
    login: loginName,
    role_code: String(roleSurface.role_code || '').trim(),
    landing_scene_key: String(roleSurface.landing_scene_key || '').trim(),
    default_route: systemInit?.default_route || {},
    contract_surface: surface,
    dom_surface: dom,
    status: roleSurface.role_code && statusbarOk && smartOk && chatterOk && attachmentOk && !dom.visible_error
      ? 'pass'
      : 'fail',
    checks: { role_surface_present: Boolean(roleSurface.role_code), statusbarOk, smartOk, chatterOk, attachmentOk },
  };
}

async function inspectState(page, stateRow) {
  const contract = await intentRequest(page, 'load_contract', {
    model: MODEL,
    view_type: 'form',
    include: 'all',
    action_id: Number(ACTION_ID),
    menu_id: Number(MENU_ID),
  });
  const states = statusbarStates(contract);
  const expected = states.find((row) => row.value === stateRow.state) || null;
  await openForm(page, stateRow.id);
  const dom = await domSurface(page);
  const active = dom.statusbar.find((row) => row.active) || null;
  return {
    state: stateRow.state,
    record_id: stateRow.id,
    expected_label: expected?.label || '',
    active_label: active?.label || '',
    statusbar_labels: dom.statusbar.map((row) => row.label),
    status: expected && active && expected.label === active.label ? 'pass' : 'fail',
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    model: MODEL,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    artifacts: outDir,
    role_logins: ROLE_LOGINS,
    state_records: STATE_RECORDS,
    paths: [],
    role_results: [],
    state_results: [],
  };

  try {
    for (const loginName of ROLE_LOGINS) {
      const context = await browser.newContext({ locale: 'zh-CN' });
      const page = await context.newPage();
      attachConsoleCapture(page);
      await login(page, loginName);
      const row = await inspectRole(page, loginName, STATE_RECORDS[0]?.id || 771);
      row.console_errors = page.__consoleErrors || [];
      row.status = row.status === 'pass' && row.console_errors.length === 0 ? 'pass' : 'fail';
      result.role_results.push(row);
      await page.screenshot({ path: path.join(outDir, `role-${loginName}.png`), fullPage: true });
      await context.close();
    }

    const stateContext = await browser.newContext({ locale: 'zh-CN' });
    const statePage = await stateContext.newPage();
    attachConsoleCapture(statePage);
    await login(statePage, ROLE_LOGINS[0] || 'wutao');
    for (const stateRow of STATE_RECORDS) {
      result.state_results.push(await inspectState(statePage, stateRow));
    }
    result.state_console_errors = statePage.__consoleErrors || [];
    await statePage.screenshot({ path: path.join(outDir, 'state-final.png'), fullPage: true });
    await stateContext.close();

    result.paths.push({
      path_id: 'P21',
      level: 'L5',
      name: 'role matrix form contract and render reachability',
      status: result.role_results.every((row) => row.status === 'pass') ? 'pass' : 'fail',
      roles: result.role_results.map((row) => ({
        login: row.login,
        role_code: row.role_code,
        status: row.status,
        checks: row.checks,
      })),
    });
    result.paths.push({
      path_id: 'P22',
      level: 'L5',
      name: 'state matrix statusbar active contract alignment',
      status: result.state_results.every((row) => row.status === 'pass') && result.state_console_errors.length === 0
        ? 'pass'
        : 'fail',
      states: result.state_results,
      state_console_errors: result.state_console_errors.length,
    });
    result.pass = result.paths.every((row) => row.status === 'pass');
    writeJson('summary.json', result);
    console.log(`[form_role_state_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths,
      role_count: result.role_results.length,
      state_count: result.state_results.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_role_state_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
