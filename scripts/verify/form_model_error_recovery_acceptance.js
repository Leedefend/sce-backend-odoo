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
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const DEFAULT_SPECIMENS = [
  { tier: 'M2', model: 'payment.request', recordId: 28489, actionId: 585, menuId: 0, label: '付款/收款申请' },
  { tier: 'M3', model: 'purchase.order', recordId: 9, actionId: 549, menuId: 0, label: '采购单' },
  { tier: 'M4', model: 'sc.legacy.receipt.income.fact', recordId: 7220, actionId: 561, menuId: 0, label: '历史收款收入事实' },
  { tier: 'M5', model: 'sc.dictionary', recordId: 5, actionId: 619, menuId: 0, label: '业务字典' },
];

const SPECIMENS = process.env.SPECIMENS_JSON
  ? JSON.parse(process.env.SPECIMENS_JSON)
  : DEFAULT_SPECIMENS;

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-model-error-recovery', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function clean(value) {
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
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function token(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || '', DB_NAME);
}

async function intentRequest(page, intent, params) {
  const authToken = await token(page);
  return page.evaluate(async ({ dbName, authToken: bearer, intentName, payload }) => {
    const headers = { 'Content-Type': 'application/json', 'X-Trace-Id': `form-model-error-recovery-${Date.now()}` };
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

function formUrl(specimen, idPart) {
  const query = new URLSearchParams();
  if (Number(specimen.menuId || 0) > 0) query.set('menu_id', String(specimen.menuId));
  if (Number(specimen.actionId || 0) > 0) query.set('action_id', String(specimen.actionId));
  const route = idPart === 'new' ? 'f' : 'r';
  return `${FRONTEND_URL}/${route}/${encodeURIComponent(specimen.model)}/${idPart}?${query.toString()}`;
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const shell = document.querySelector('.template-layout-shell');
    const text = String(shell?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openExisting(page, specimen) {
  await page.goto(formUrl(specimen, specimen.recordId), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
}

async function openCreate(page, specimen) {
  await page.goto(formUrl(specimen, 'new'), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
}

async function domState(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const shell = document.querySelector('.template-layout-shell');
    return {
      url: window.location.href,
      title: normalize(document.querySelector('.template-page-title, h1, .title')?.textContent || ''),
      input_count: document.querySelectorAll('.template-layout-shell input, .template-layout-shell textarea, .template-layout-shell select').length,
      readonly_count: document.querySelectorAll('.readonly-value, .readonly-field, .form-readonly, .native-readonly').length,
      statusbar_count: document.querySelectorAll('.native-statusbar-step').length,
      validation_text: normalize(document.querySelector('.validation-error, .submission-feedback--warn, .status-panel.error')?.textContent || ''),
      text_sample: normalize(shell?.textContent || '').slice(0, 800),
    };
  });
}

function contractFacts(contract) {
  const form = contract?.views?.form || {};
  const permissions = contract?.permissions?.effective?.rights || {};
  const validationRules = Array.isArray(contract?.validation_rules) ? contract.validation_rules : [];
  const requiredRules = validationRules.filter((rule) => String(rule?.code || '').toUpperCase() === 'REQUIRED');
  return {
    render_profile: clean(contract?.render_profile),
    field_count: Object.keys(contract?.fields || {}).length,
    can_create: permissions.create === true,
    can_write: permissions.write === true,
    validation_rule_count: validationRules.length,
    required_fields: requiredRules.map((rule) => clean(rule.field)).filter(Boolean),
    has_form: Boolean(form && typeof form === 'object'),
  };
}

function hasReadonlyProjectionSurface(state, specimen) {
  return state.validation_text === ''
    && state.text_sample.length > 80
    && state.text_sample.includes(String(specimen.label || '').trim());
}

function collectConcurrencyKeys(value, pathName = '$', rows = []) {
  if (!value || typeof value !== 'object') return rows;
  if (Array.isArray(value)) {
    value.slice(0, 50).forEach((item, index) => collectConcurrencyKeys(item, `${pathName}[${index}]`, rows));
    return rows;
  }
  Object.entries(value).forEach(([key, child]) => {
    const nextPath = `${pathName}.${key}`;
    if (/^(if_match|ifMatch|write_date|record_version|concurrency|conflict_policy|version_token)$/i.test(key)) {
      rows.push({ path: nextPath, value: typeof child === 'object' ? '[object]' : clean(child) });
    }
    collectConcurrencyKeys(child, nextPath, rows);
  });
  return rows;
}

async function checkRecovery(page, specimen) {
  await openExisting(page, specimen);
  const initial = await domState(page);
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
  const afterReload = await domState(page);
  await page.goto(`${FRONTEND_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.goto(formUrl(specimen, specimen.recordId), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormReady(page);
  const afterDeepLink = await domState(page);
  const renderable = (state) => state.input_count > 0
    || state.readonly_count > 0
    || state.statusbar_count > 0
    || hasReadonlyProjectionSurface(state, specimen);
  return {
    path_id: 'P25',
    status: renderable(initial) && renderable(afterReload) && renderable(afterDeepLink) ? 'pass' : 'fail',
    initial,
    after_reload: afterReload,
    after_deep_link: afterDeepLink,
  };
}

async function clickPrimarySave(page) {
  const saveButtons = page.locator('button.primary').filter({ hasText: /保存|创建|提交|确认/ });
  const count = await saveButtons.count();
  for (let index = 0; index < count; index += 1) {
    const button = saveButtons.nth(index);
    if (await button.isVisible().catch(() => false) && !(await button.isDisabled().catch(() => true))) {
      await button.click();
      return true;
    }
  }
  return false;
}

async function checkCreateValidation(page, specimen, facts) {
  if (!facts.can_create) {
    return {
      path_id: 'P20',
      status: 'not_applicable',
      reason: 'contract denies create for this user/model',
    };
  }
  if (!facts.required_fields.length) {
    return {
      path_id: 'P20',
      status: 'blocked',
      reason: 'CONTRACT_MISSING: create validation has no REQUIRED rules to exercise safely',
    };
  }
  await openCreate(page, specimen);
  const before = await domState(page);
  const clicked = await clickPrimarySave(page);
  if (!clicked) {
    return {
      path_id: 'P20',
      status: 'blocked',
      reason: 'no enabled save/create control is reachable in create form',
      before,
    };
  }
  await page.waitForTimeout(800);
  const after = await domState(page);
  const stillNew = /\/f\/[^/]+\/new\b/.test(new URL(after.url).pathname);
  const friendly = /必填|不能为空|创建失败|检查填写内容|请选择|required/i.test(`${after.validation_text} ${after.text_sample}`);
  return {
    path_id: 'P20',
    status: stillNew && friendly ? 'pass' : 'fail',
    required_fields: facts.required_fields,
    before,
    after,
    checks: { clicked, stillNew, friendly },
  };
}

function checkConcurrencyContract(contract) {
  const keys = collectConcurrencyKeys(contract);
  const recordScoped = keys.filter((row) => {
    if (/meta\.etag|contract_version|schema_version/i.test(row.path)) return false;
    if (/\.fields\.write_date$|\.field_groups\.write_date$|\.field_rules\.write_date$|\.field_policies\.write_date$|\.field_semantics\.write_date$/i.test(row.path)) {
      return false;
    }
    return /if_match|ifMatch|record_version|version_token|concurrency|conflict_policy/i.test(row.path);
  });
  const hasRecordConflictSemantics = recordScoped.length > 0;
  return {
    path_id: 'P24',
    status: hasRecordConflictSemantics ? 'pass' : 'blocked',
    reason: hasRecordConflictSemantics
      ? 'record conflict semantics are present in contract'
      : 'CONTRACT_MISSING: form contract/save chain does not expose record version or stale-write conflict semantics',
    evidence_keys: recordScoped,
  };
}

async function inspectSpecimen(page, specimen) {
  let contract = null;
  if (Number(specimen.actionId || 0) > 0) {
    contract = await intentRequest(page, 'ui.contract', {
      op: 'action_open',
      action_id: Number(specimen.actionId || 0),
      record_id: Number(specimen.recordId || 0),
      render_profile: 'edit',
      contract_surface: 'user',
    });
  }
  if (!contract) {
    contract = await intentRequest(page, 'load_contract', {
      model: specimen.model,
      view_type: 'form',
      include: 'all',
      action_id: Number(specimen.actionId || 0) || undefined,
      menu_id: Number(specimen.menuId || 0) || undefined,
    });
  }
  const facts = contractFacts(contract);
  const p25 = await checkRecovery(page, specimen);
  const p20 = await checkCreateValidation(page, specimen, facts);
  const p24 = checkConcurrencyContract(contract);
  return {
    ...specimen,
    contract: facts,
    paths: [p20, p24, p25],
    status: [p20, p25].every((row) => row.status === 'pass' || row.status === 'not_applicable')
      && p24.status === 'blocked'
      ? 'conditional'
      : ([p20, p25].every((row) => row.status === 'pass' || row.status === 'not_applicable') && p24.status === 'pass' ? 'pass' : 'fail'),
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    login: LOGIN,
    frontend_url: FRONTEND_URL,
    artifacts: outDir,
    specimens: SPECIMENS,
    rows: [],
    paths: [],
  };

  try {
    const context = await browser.newContext({ locale: 'zh-CN' });
    const page = await context.newPage();
    attachConsoleCapture(page);
    await login(page);

    for (const specimen of SPECIMENS) {
      const row = await inspectSpecimen(page, specimen);
      result.rows.push(row);
      await page.screenshot({
        path: path.join(outDir, `${row.tier}-${row.model.replace(/\./g, '_')}-${row.recordId}-latest.png`),
        fullPage: true,
      });
    }

    result.console_errors = page.__consoleErrors || [];
    result.paths = ['P20', 'P24', 'P25'].map((pathId) => {
      const rows = result.rows.map((row) => ({
        tier: row.tier,
        model: row.model,
        record_id: row.recordId,
        status: row.paths.find((item) => item.path_id === pathId)?.status || 'missing',
        reason: row.paths.find((item) => item.path_id === pathId)?.reason || '',
      }));
      return {
        path_id: pathId,
        level: pathId === 'P25' ? 'L6' : 'L5',
        status: rows.every((row) => row.status === 'pass' || row.status === 'not_applicable')
          ? 'pass'
          : (rows.some((row) => row.status === 'fail' || row.status === 'missing') ? 'fail' : 'blocked'),
        rows,
      };
    });
    await context.close();
    result.pass = result.paths.find((row) => row.path_id === 'P20')?.status === 'pass'
      && result.paths.find((row) => row.path_id === 'P25')?.status === 'pass'
      && ['pass', 'blocked'].includes(result.paths.find((row) => row.path_id === 'P24')?.status || '')
      && result.console_errors.length === 0;
    result.decision = result.pass && result.paths.find((row) => row.path_id === 'P24')?.status === 'blocked'
      ? 'conditional_pass_with_p24_contract_blocker'
      : (result.pass ? 'pass' : 'fail');
    writeJson('summary.json', result);
    console.log(`[form_model_error_recovery_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      decision: result.decision,
      paths: result.paths,
      console_errors: result.console_errors.length,
    }, null, 2));
    process.exit(result.pass ? 0 : 1);
  } catch (err) {
    result.pass = false;
    result.error = err instanceof Error ? err.message : String(err);
    writeJson('summary.json', result);
    console.error(`[form_model_error_recovery_acceptance] failed artifacts=${outDir}`);
    console.error(result.error);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

main();
