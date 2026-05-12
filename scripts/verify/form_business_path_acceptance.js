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
const ODOO_URL = process.env.ODOO_URL || 'http://127.0.0.1:8070';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-business-path', ts);

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

const VALIDATION_ERROR_PATTERNS = [
  '不能为空',
  '创建失败，请检查填写内容',
  '请填写',
  '必填',
  'required',
];

async function waitForValidationSignal(page, timeout = 10000) {
  const pattern = new RegExp(VALIDATION_ERROR_PATTERNS.join('|'), 'i');
  try {
    await page.getByText(pattern, { exact: false }).first().waitFor({ timeout });
    return true;
  } catch (_err) {
    return false;
  }
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

async function loginCustom(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if ((await dbInput.count().catch(() => 0)) > 0) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) {
      await dbInput.fill(DB_NAME);
    }
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function loginNative(page) {
  await page.goto(`${ODOO_URL}/web/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  const dbInput = page.locator('input[name="db"]');
  if (await dbInput.count().catch(() => 0)) await dbInput.fill(DB_NAME);
  await page.locator('input[name="login"]').fill(LOGIN);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await page.waitForURL((url) => !url.pathname.includes('/web/login'), { timeout: 30000 });
}

async function openCustomForm(page) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'networkidle' },
  );
  await page.locator('.template-layout-shell input.input').first().waitFor({ timeout: 30000 });
}

async function openNativeForm(page) {
  await page.goto(
    `${ODOO_URL}/web?form_acceptance_ts=${Date.now()}#id=${RECORD_ID}&model=${MODEL}&view_type=form&action=${ACTION_ID}&menu_id=${MENU_ID}`,
    { waitUntil: 'domcontentloaded' },
  );
  await page.locator('.o_form_view').waitFor({ timeout: 30000 });
}

async function customNameValue(page) {
  return customInputValue(page, 0);
}

async function customInputValue(page, index) {
  return page.evaluate((inputIndex) => {
    const input = document.querySelectorAll('.template-layout-shell input.input')[inputIndex];
    return input ? input.value : '';
  }, index);
}

async function setCustomName(page, value) {
  return setCustomInput(page, 0, value);
}

async function setCustomInput(page, index, value) {
  const input = page.locator('.template-layout-shell input.input').first();
  const target = index === 0 ? input : page.locator('.template-layout-shell input.input').nth(index);
  await target.fill(value);
  await page.waitForTimeout(150);
}

async function saveCustom(page) {
  const save = page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first();
  await save.waitFor({ timeout: 10000 });
  if (await save.isDisabled().catch(() => false)) {
    const editButton = page.locator('.template-page-header-actions button').filter({ hasText: /^编辑$/ }).first();
    if (await editButton.count().catch(() => 0)) {
      await editButton.click();
      await page.waitForTimeout(200);
    }
  }
  await save.waitFor({ state: 'visible', timeout: 10000 });
  await save.click();
}

async function waitForCustomSaveSuccess(page) {
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 15000 });
}

async function nativeInputValue(page, index) {
  return page.evaluate((inputIndex) => {
    const inputs = Array.from(document.querySelectorAll('.o_form_view input.o_input, .o_form_view textarea.o_input'));
    const input = inputs[inputIndex] || null;
    return input ? input.value : '';
  }, index);
}

async function exerciseRequiredNameValidation(page, originalName) {
  await setCustomName(page, '');
  await saveCustom(page);
  const hasSignal = await waitForValidationSignal(page, 10000);
  const body = normalize(await page.locator('.template-layout-shell').innerText());
  await setCustomName(page, originalName);
  const hasValidationText = VALIDATION_ERROR_PATTERNS.some((token) => body.toLowerCase().includes(token.toLowerCase()));
  return {
    path_id: 'P20',
    level: 'L4',
    status: hasSignal || hasValidationText ? 'pass' : 'fail',
    observed_error: body.match(/[^。；\n]*(不能为空|创建失败，请检查填写内容|请填写|必填|required)[^。；\n]*/i)?.[0] || '',
  };
}

async function exerciseEditSavePersistence(customPage, nativePage, originalValue) {
  const fieldIndex = 0;
  const updatedValue = `${originalValue} L4-${Date.now().toString().slice(-6)}`;
  await setCustomInput(customPage, fieldIndex, updatedValue);
  await saveCustom(customPage);
  await waitForCustomSaveSuccess(customPage);
  await openCustomForm(customPage);
  const customAfterSave = await customInputValue(customPage, fieldIndex);
  await openNativeForm(nativePage);
  const nativeAfterSave = await nativeInputValue(nativePage, fieldIndex);

  await setCustomInput(customPage, fieldIndex, originalValue);
  await saveCustom(customPage);
  await waitForCustomSaveSuccess(customPage);
  await openCustomForm(customPage);
  const customAfterRevert = await customInputValue(customPage, fieldIndex);
  await openNativeForm(nativePage);
  const nativeAfterRevert = await nativeInputValue(nativePage, fieldIndex);

  return {
    path_id: 'P04/P23',
    level: 'L4',
    status: customAfterSave === updatedValue && nativeAfterSave === updatedValue
      && customAfterRevert === originalValue && nativeAfterRevert === originalValue
      ? 'pass'
      : 'fail',
    field_index: fieldIndex,
    field_label: '名称',
    original_value: originalValue,
    updated_value: updatedValue,
    custom_after_save: customAfterSave,
    native_after_save: nativeAfterSave,
    custom_after_revert: customAfterRevert,
    native_after_revert: nativeAfterRevert,
  };
}

async function exerciseOne2manyValidation(page) {
  await page.locator('.native-tabs .native-tab').filter({ hasText: '投标管理' }).first().click().catch(() => {});
  await page.locator('.native-tab-panel .o2m-toolbar button').filter({ hasText: '添加行' }).first().click();
  await page.locator('.native-tab-panel .o2m-row').first().waitFor({ timeout: 10000 });
  await saveCustom(page);
  await waitForValidationSignal(page, 10000);
  const details = await page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const panel = document.querySelector('.native-tab-panel');
    const errors = Array.from(document.querySelectorAll('.o2m-row-error, .status-panel, .warn, .template-layout-shell'))
      .map((node) => normalize(node.textContent))
      .filter((text) => text.includes('不能为空') || text.includes('创建失败，请检查填写内容'));
    const labels = Array.from((panel || document).querySelectorAll('.o2m-field .meta'))
      .map((node) => normalize(node.textContent))
      .filter(Boolean);
    return { errors, labels };
  });
  await page.reload({ waitUntil: 'networkidle' });
  await page.locator('.template-layout-shell input.input').first().waitFor({ timeout: 30000 });
  return {
    path_id: 'P12/P20',
    level: 'L4',
    status: details.errors.some((text) => text.includes('投标名称不能为空') || text.includes('状态不能为空'))
      ? 'pass'
      : 'fail',
    row_labels: details.labels,
    observed_errors: details.errors.slice(0, 5),
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const result = {
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    odoo_url: ODOO_URL,
    artifacts: outDir,
    paths: [],
  };

  try {
    const customContext = await browser.newContext({ locale: 'zh-CN' });
    const nativeContext = await browser.newContext({ locale: 'zh-CN' });
    const customPage = await customContext.newPage();
    const nativePage = await nativeContext.newPage();
    attachConsoleCapture(customPage);
    attachConsoleCapture(nativePage);

    await loginCustom(customPage);
    await loginNative(nativePage);
    await openCustomForm(customPage);
    await openNativeForm(nativePage);

    const originalName = await customNameValue(customPage);
    result.original_name = originalName;
    result.paths.push(await exerciseRequiredNameValidation(customPage, originalName));
    result.paths.push(await exerciseEditSavePersistence(customPage, nativePage, originalName));
    result.paths.push(await exerciseOne2manyValidation(customPage));

    result.console_errors = {
      custom: customPage.__consoleErrors || [],
      native: nativePage.__consoleErrors || [],
    };
    await customPage.screenshot({ path: path.join(outDir, 'custom_final.png'), fullPage: true });
    await nativePage.screenshot({ path: path.join(outDir, 'native_final.png'), fullPage: true });
    await customContext.close();
    await nativeContext.close();

    result.pass = result.paths.every((row) => row.status === 'pass')
      && result.console_errors.custom.length === 0
      && result.console_errors.native.length === 0;
    writeJson('summary.json', result);
    console.log(`[form_business_path_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths,
      console_errors: {
        custom: result.console_errors.custom.length,
        native: result.console_errors.native.length,
      },
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_business_path_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
