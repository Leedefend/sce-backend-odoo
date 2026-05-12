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
const ODOO_URL = process.env.ODOO_URL || 'http://127.0.0.1:18069';
const DB_NAME = process.env.DB_NAME || 'sc_prod_sim';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-native-custom-gap', ts);

const EXPECTED = {
  tabs: ['投标管理', '施工信息', 'WBS结构', '工程量清单', '工程结构', '合同', '工程资料', '驾驶舱', '描述', '设置', '协作 / 系统'],
  statusbar: ['草稿', '在建', '停工', '竣工', '结算中', '保修期', '关闭'],
  smartButtons: ['执行结构', '工程量清单', '预算/成本', '合同'],
  headerActions: ['共享只读', '分享可编辑的内容', '提交立项'],
  chatterActions: ['发送消息', '记录备注', '活动'],
  x2manyActions: ['添加行'],
  x2manyColumns: ['投标名称', '投标轮次', '招标人/业主', '投标报价', '清单合计', '状态', '投标截止时间'],
};
const FORBIDDEN_CUSTOM_TEXT = [
  'header_bar',
  'scene-block',
  '{"default_sort"',
  "'kind': 'open'",
  "'visible_profiles'",
  '"filters":[{"key"',
  ' header sheet container ',
  'header sheet container',
  ' sheet container ',
  ' container h1 ',
  'project.project.form',
  'display_name',
];

function writeJson(name, data) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, name), JSON.stringify(data, null, 2), 'utf8');
}

function unique(values) {
  return Array.from(new Set(values.map((item) => String(item || '').trim()).filter(Boolean)));
}

async function texts(locator) {
  return unique(await locator.allTextContents().catch(() => []));
}

async function hasText(page, label) {
  return (await page.getByText(label, { exact: true }).count().catch(() => 0)) > 0;
}

async function presence(page, labels) {
  const out = {};
  for (const label of labels) {
    out[label] = await hasText(page, label);
  }
  return out;
}

function missingFrom(presenceMap) {
  return Object.entries(presenceMap)
    .filter(([, ok]) => !ok)
    .map(([label]) => label);
}

async function collectFormSurface(page, kind) {
  const scoped = await page.evaluate((surfaceKind) => {
    const root = surfaceKind === 'native'
      ? document.querySelector('.o_form_view')
      : document.querySelector('.template-layout-shell, .native-form-tree, main');
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const unique = (values) => Array.from(new Set(values.map(normalize).filter(Boolean)));
    const text = (selector, scope = root) => unique(Array.from((scope || document).querySelectorAll(selector)).map((el) => el.textContent));
    const nativeForm = root || document;
    if (surfaceKind === 'native') {
      return {
        buttons: text('button', nativeForm),
        tabs: text('.o_notebook .nav-link, [role="tab"]', nativeForm),
        statusbar: text('.o_statusbar_status button, .o_statusbar_status .dropdown-item', nativeForm),
        header_actions: text('.o_form_statusbar button', nativeForm),
        smart_buttons: text('.o_form_button_box button, .o_control_panel_actions button', nativeForm),
        chatter_actions: text('.o-mail-Chatter button, .o_Chatter button, .o_chatter button', nativeForm),
        x2many_actions: text('.o_field_x2many_list_row_add a, .o_field_x2many_list_row_add button, .o_field_x2many_list_row_add', nativeForm),
        x2many_columns: text('.o_field_x2many_list thead th, .o_list_table thead th', nativeForm),
        field_labels: text('label, .o_form_label', nativeForm),
      };
    }
    const bodyText = normalize(document.body?.textContent || '');
    return {
      buttons: text('button', nativeForm),
      tabs: text('.native-tabs .native-tab, [role="tab"]', nativeForm),
      statusbar: text('.native-statusbar button, .native-statusbar [role="button"]', nativeForm),
      header_actions: text('.template-page-header-actions button, .native-container--header button', nativeForm),
      smart_buttons: text('.native-actions--smart button', nativeForm),
      chatter_actions: text('.native-chatter-block button', nativeForm),
      x2many_actions: text('.native-tab-panel .o2m-toolbar button, .native-tab-panel .chip-btn', nativeForm),
      x2many_columns: text('.native-tab-panel .o2m-header-cell, .native-tab-panel .o2m-fields .meta, .native-tab-panel th', nativeForm),
      field_labels: text('label, .field-label, .form-label', nativeForm),
      body_text: bodyText,
    };
  }, kind);
  const allButtons = scoped.buttons || [];
  const allTabs = scoped.tabs || [];
  const labels = await texts(page.locator('label, .o_form_label, .field-label, .form-label'));
  const inputs = await page.locator('input, textarea, select').count().catch(() => 0);
  const relationDialogs = await page.locator('.modal, [role="dialog"], .relation-dialog').count().catch(() => 0);
  const consoleErrors = page.__consoleErrors || [];

  const expectedPresence = {};
  for (const [key, values] of Object.entries(EXPECTED)) {
    expectedPresence[key] = await presence(page, values);
  }

  return {
    kind,
    url: page.url(),
    counts: {
      buttons: allButtons.length,
      tabs: allTabs.length,
      labels: labels.length,
      inputs,
      relation_dialogs: relationDialogs,
      console_errors: consoleErrors.length,
    },
    all_buttons: allButtons,
    all_tabs: allTabs,
    scoped,
    sample_labels: labels.slice(0, 80),
    expected_presence: expectedPresence,
    missing_expected: Object.fromEntries(
      Object.entries(expectedPresence).map(([key, value]) => [key, missingFrom(value)]),
    ),
    console_errors: consoleErrors,
    forbidden_text: kind === 'custom'
      ? FORBIDDEN_CUSTOM_TEXT.filter((item) => String(scoped.body_text || '').includes(item))
      : [],
  };
}

function includesText(values, label) {
  return values.some((value) => value === label || value.includes(label));
}

function missingScoped(surface, key, labels) {
  const values = surface.scoped[key] || [];
  return labels.filter((label) => !includesText(values, label));
}

async function exerciseCustomOne2manyPath(page) {
  await page.locator('.native-tabs .native-tab').filter({ hasText: '投标管理' }).first().click().catch(() => {});
  const scopedPanel = page.locator('.native-tab-panel').filter({ hasText: '投标管理' }).first();
  const panelExists = (await scopedPanel.count().catch(() => 0)) > 0;
  const panel = panelExists ? scopedPanel : page.locator('.native-tab-panel').first();
  await panel.locator('.o2m-toolbar button').filter({ hasText: '添加行' }).first().click();
  await panel.locator('.o2m-row').first().waitFor({ timeout: 10000 });
  return page.evaluate((expectedColumns) => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const activePanel = Array.from(document.querySelectorAll('.native-tab-panel'))
      .find((node) => normalize(node.textContent || '').includes('投标管理'))
      || document.querySelector('.native-tab-panel');
    const row = activePanel && activePanel.querySelector('.o2m-row');
    const labels = Array.from((row || document).querySelectorAll('.o2m-field .meta'))
      .map((el) => normalize(el.textContent))
      .filter(Boolean);
    const fields = Array.from((row || document).querySelectorAll('.o2m-field')).map((field) => {
      const label = normalize(field.querySelector('.meta')?.textContent || '');
      const control = field.querySelector('input, select, textarea');
      return {
        label,
        disabled: Boolean(control && control.disabled),
      };
    });
    const amountTotal = fields.find((field) => field.label.includes('清单合计'));
    return {
      add_row: Boolean(row),
      row_labels: labels,
      readonly_columns_disabled: {
        '清单合计': Boolean(amountTotal && amountTotal.disabled),
      },
      missing_row_labels: expectedColumns.filter((label) => !labels.some((value) => value.includes(label))),
    };
  }, EXPECTED.x2manyColumns);
}

async function waitForCustomFormReady(page) {
  await page.locator('.native-form-tree, .template-layout-shell').first().waitFor({ timeout: 45000 });
  await page.locator('.native-tabs .native-tab').filter({ hasText: '投标管理' }).first().waitFor({ timeout: 45000 });
  await page.locator('.native-statusbar').first().waitFor({ timeout: 45000 });
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载页面')
      && document.querySelectorAll('.native-tabs .native-tab').length > 0
      && document.querySelectorAll('.native-statusbar').length > 0
      && text.includes('投标管理');
  }, null, { timeout: 45000 });
}

async function loginCustom(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function loginNative(page) {
  await page.goto(`${ODOO_URL}/web/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: 'domcontentloaded' });
  const dbInput = page.locator('input[name="db"]');
  if (await dbInput.count().catch(() => 0)) {
    await dbInput.fill(DB_NAME);
  }
  await page.locator('input[name="login"]').fill(LOGIN);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"], input[type="submit"]').first().click();
  await page.waitForURL((url) => !url.pathname.includes('/web/login'), { timeout: 30000 });
}

function attachConsoleCapture(page) {
  page.__consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      page.__consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    page.__consoleErrors.push(err.message);
  });
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
  };

  try {
    const customContext = await browser.newContext({ locale: 'zh-CN' });
    const customPage = await customContext.newPage();
    attachConsoleCapture(customPage);
    await loginCustom(customPage);
    await customPage.goto(
      `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
      { waitUntil: 'domcontentloaded', timeout: 45000 },
    );
    await waitForCustomFormReady(customPage);
    result.custom_business_paths = {
      one2many_add_row: await exerciseCustomOne2manyPath(customPage),
    };
    await customPage.screenshot({ path: path.join(outDir, 'custom_form.png'), fullPage: true });
    result.custom = await collectFormSurface(customPage, 'custom');
    await customContext.close();

    const nativeContext = await browser.newContext({ locale: 'zh-CN' });
    const nativePage = await nativeContext.newPage();
    attachConsoleCapture(nativePage);
    await loginNative(nativePage);
    await nativePage.goto(
      `${ODOO_URL}/web#id=${RECORD_ID}&model=${MODEL}&view_type=form&action=${ACTION_ID}&menu_id=${MENU_ID}`,
      { waitUntil: 'domcontentloaded' },
    );
    await nativePage.locator('.o_form_view').waitFor({ timeout: 30000 });
    await nativePage.screenshot({ path: path.join(outDir, 'native_form.png'), fullPage: true });
    result.native = await collectFormSurface(nativePage, 'native');
    await nativeContext.close();

    const scopedKey = {
      tabs: 'tabs',
      statusbar: 'statusbar',
      smartButtons: 'smart_buttons',
      headerActions: 'header_actions',
      chatterActions: 'chatter_actions',
      x2manyActions: 'x2many_actions',
      x2manyColumns: 'x2many_columns',
    };
    const gap = {};
    for (const key of Object.keys(EXPECTED)) {
      const nativeMissing = missingScoped(result.native, scopedKey[key], EXPECTED[key]);
      const customMissing = missingScoped(result.custom, scopedKey[key], EXPECTED[key]);
      gap[key] = {
        native_missing: nativeMissing,
        custom_missing: customMissing,
        custom_missing_but_native_present: customMissing.filter((label) => !nativeMissing.includes(label)),
      };
    }
    result.gap = gap;
    result.pass = Object.values(gap).every((row) => row.custom_missing_but_native_present.length === 0)
      && result.custom_business_paths.one2many_add_row.add_row
      && result.custom_business_paths.one2many_add_row.missing_row_labels.length === 0
      && result.custom_business_paths.one2many_add_row.readonly_columns_disabled['清单合计']
      && result.custom.forbidden_text.length === 0;

    writeJson('summary.json', result);
    console.log(`[form_native_custom_gap_audit] artifacts=${outDir}`);
    console.log(JSON.stringify({ pass: result.pass, gap, custom_business_paths: result.custom_business_paths }, null, 2));
    if (!result.pass) {
      process.exit(1);
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_native_custom_gap_audit] FAIL: ${err.message}`);
  process.exit(1);
});
