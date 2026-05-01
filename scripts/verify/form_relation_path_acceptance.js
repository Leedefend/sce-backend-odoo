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
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-relation-path', ts);

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

async function intentRequest(page, intent, params) {
  return page.evaluate(async ({ dbName, intentName, payload }) => {
    const token = sessionStorage.getItem(`sc_auth_token:${dbName}`);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
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
    return body.data;
  }, { dbName: DB_NAME, intentName: intent, payload: params });
}

async function createAcceptanceTagFixture(page) {
  const label = `L4 Acceptance Tag ${ts}`;
  const created = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'project.tags',
    vals: { name: label },
    context: {},
  });
  return {
    id: Number(created?.id || 0),
    label,
  };
}

async function cleanupAcceptanceTagFixture(page, fixture) {
  const summary = {
    tag_id: fixture?.id || 0,
    unlinked_project: false,
    deleted_tag: false,
    delete_policy: null,
    errors: [],
  };
  if (!fixture?.id) return summary;
  try {
    await intentRequest(page, 'api.data', {
      op: 'write',
      model: MODEL,
      ids: [Number(RECORD_ID)],
      vals: { tag_ids: [[3, fixture.id]] },
      context: {},
    });
    summary.unlinked_project = true;
  } catch (err) {
    summary.errors.push(err instanceof Error ? err.message : String(err));
  }
  try {
    const deleted = await intentRequest(page, 'api.data.unlink', {
      model: 'project.tags',
      ids: [fixture.id],
      context: {},
    });
    summary.deleted_tag = true;
    summary.delete_policy = deleted?.delete_policy || null;
  } catch (err) {
    summary.errors.push(err instanceof Error ? err.message : String(err));
  }
  return summary;
}

async function loginCustom(page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 });
}

async function openCustomForm(page) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'networkidle' },
  );
  await page.locator('.template-layout-shell input.input').first().waitFor({ timeout: 30000 });
}

function relationBox(page, index) {
  return page.locator('.many2one-combobox').nth(index);
}

async function relationValue(page, index) {
  return relationBox(page, index).locator('input').inputValue();
}

async function openSearchMore(page, index) {
  await relationBox(page, index).locator('button').filter({ hasText: '搜索更多' }).first().click();
  await page.locator('.relation-dialog').waitFor({ timeout: 10000 });
}

async function dialogSnapshot(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return {
      title: normalize(document.querySelector('.relation-dialog h3')?.textContent),
      headers: Array.from(document.querySelectorAll('.relation-dialog th')).map((node) => normalize(node.textContent)).filter(Boolean),
      rows: Array.from(document.querySelectorAll('.relation-dialog tbody tr')).map((row) => normalize(row.textContent)),
      buttons: Array.from(document.querySelectorAll('.relation-dialog button')).map((button) => ({
        text: normalize(button.textContent),
        disabled: button.disabled,
        className: button.className,
      })),
      keyword: document.querySelector('.relation-dialog input.input')?.value || '',
    };
  });
}

async function exerciseSearchMoreCancel(page) {
  const before = await relationValue(page, 1);
  await openSearchMore(page, 1);
  const snapshot = await dialogSnapshot(page);
  await page.locator('.relation-dialog button').filter({ hasText: '取消' }).click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const after = await relationValue(page, 1);
  return {
    path_id: 'P08',
    level: 'L4',
    scenario: 'search_more_cancel',
    status: before === after
      && snapshot.title === '项目管理员：搜索更多'
      && snapshot.buttons.some((button) => button.text === '选择' && button.disabled)
      && snapshot.buttons.some((button) => button.text === '取消')
      ? 'pass'
      : 'fail',
    before,
    after,
    snapshot,
  };
}

async function exerciseSearchMoreSelect(page) {
  await openSearchMore(page, 1);
  const firstRow = page.locator('.relation-dialog tbody tr').first();
  const rowText = normalize(await firstRow.innerText());
  await firstRow.click();
  const selectButton = page.locator('.relation-dialog button.primary').filter({ hasText: '选择' }).first();
  const selectEnabled = !(await selectButton.isDisabled());
  await selectButton.click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  const after = await relationValue(page, 1);
  return {
    path_id: 'P08',
    level: 'L4',
    scenario: 'search_more_select',
    status: selectEnabled && rowText.includes(after) && after === 'Demo Project User' ? 'pass' : 'fail',
    row_text: rowText,
    after,
    select_enabled: selectEnabled,
  };
}

async function exerciseQuickPartialMatch(page) {
  const input = relationBox(page, 1).locator('input');
  await input.fill('Project User');
  await input.press('Enter');
  await page.waitForTimeout(1200);
  const after = await relationValue(page, 1);
  return {
    path_id: 'P07',
    level: 'L4',
    scenario: 'single_contains_or_exact_quick_fill',
    status: after === 'Demo Project User' ? 'pass' : 'fail',
    keyword: 'Project User',
    after,
    contract_match_mode: 'single_contains_or_exact',
  };
}

async function exerciseDeferredNoMatchCreate(page) {
  const label = `L4 Deferred Partner ${Date.now().toString().slice(-6)}`;
  const input = relationBox(page, 0).locator('input');
  await input.fill(label);
  await input.blur();
  await page.waitForTimeout(1200);
  const inlineLabels = await page.locator('.many2one-inline-create').allInnerTexts().catch(() => []);
  const saveEnabled = !(await page.locator('.template-page-header-actions button.primary').first().isDisabled());
  await openSearchMore(page, 0);
  const snapshot = await dialogSnapshot(page);
  await page.locator('.relation-dialog button').filter({ hasText: '取消' }).click();
  await page.locator('.relation-dialog').waitFor({ state: 'detached', timeout: 10000 });
  await input.fill('');
  await input.blur();
  await page.waitForTimeout(300);
  return {
    path_id: 'P09',
    level: 'L4',
    scenario: 'no_match_deferred_create_until_main_save',
    status: inlineLabels.some((text) => text.includes(label))
      && saveEnabled
      && snapshot.title === '客户：搜索更多'
      && snapshot.keyword === label
      && snapshot.rows.length === 0
      ? 'pass'
      : 'fail',
    typed_label: label,
    inline_labels: inlineLabels,
    save_enabled: saveEnabled,
    search_snapshot: snapshot,
  };
}

async function waitForSaveSuccess(page) {
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 15000 });
}

async function exerciseMany2manySelectRemove(page, tagFixture) {
  const tagLabel = tagFixture.label;
  const editor = page.locator('.relation-editor').first();
  await editor.locator('input').first().fill(tagLabel);
  const select = editor.locator('select').first();
  await select.waitFor({ timeout: 10000 });
  await page.waitForFunction((label) => {
    return Array.from(document.querySelectorAll('.relation-editor select option'))
      .some((option) => String(option.textContent || '').trim() === label);
  }, tagLabel, { timeout: 10000 });
  const optionValue = await select.locator('option').filter({ hasText: tagLabel }).first().getAttribute('value');
  await select.selectOption(optionValue || '');
  await page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first().click();
  await waitForSaveSuccess(page);
  await openCustomForm(page);
  const selectedAfterSave = await page.locator('.relation-tag').allInnerTexts().catch(() => []);

  const reloadedEditor = page.locator('.relation-editor').first();
  const reloadedSelect = reloadedEditor.locator('select').first();
  await reloadedSelect.selectOption([]);
  await page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first().click();
  await waitForSaveSuccess(page);
  await openCustomForm(page);
  const selectedAfterRemove = await page.locator('.relation-tag').allInnerTexts().catch(() => []);

  return {
    path_id: 'P10',
    level: 'L4',
    scenario: 'many2many_select_remove_reload',
    status: selectedAfterSave.some((text) => normalize(text) === tagLabel)
      && !selectedAfterRemove.some((text) => normalize(text) === tagLabel)
      ? 'pass'
      : 'fail',
    tag_label: tagLabel,
    selected_after_save: selectedAfterSave.map(normalize),
    selected_after_remove: selectedAfterRemove.map(normalize),
  };
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  let context;
  let page;
  let tagFixture = null;
  const result = {
    db: DB_NAME,
    login: LOGIN,
    model: MODEL,
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    frontend_url: FRONTEND_URL,
    artifacts: outDir,
    paths: [],
  };
  try {
    context = await browser.newContext({ locale: 'zh-CN' });
    page = await context.newPage();
    attachConsoleCapture(page);
    await loginCustom(page);
    tagFixture = await createAcceptanceTagFixture(page);
    result.fixture = tagFixture;
    await openCustomForm(page);
    result.paths.push(await exerciseSearchMoreCancel(page));
    result.paths.push(await exerciseSearchMoreSelect(page));
    result.paths.push(await exerciseQuickPartialMatch(page));
    result.paths.push(await exerciseDeferredNoMatchCreate(page));
    result.paths.push(await exerciseMany2manySelectRemove(page, tagFixture));
    result.console_errors = page.__consoleErrors || [];
    await page.screenshot({ path: path.join(outDir, 'custom_relation_final.png'), fullPage: true });

    result.pass = result.paths.every((row) => row.status === 'pass') && result.console_errors.length === 0;
    if (tagFixture) {
      result.fixture_cleanup = await cleanupAcceptanceTagFixture(page, tagFixture);
      result.pass = result.pass
        && result.fixture_cleanup.unlinked_project
        && result.fixture_cleanup.deleted_tag
        && result.fixture_cleanup.errors.length === 0;
    }
    writeJson('summary.json', result);
    console.log(`[form_relation_path_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths,
      console_errors: result.console_errors.length,
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    if (page && tagFixture && !result.fixture_cleanup) {
      result.fixture_cleanup = await cleanupAcceptanceTagFixture(page, tagFixture);
      writeJson('fixture_cleanup.json', result.fixture_cleanup);
    }
    if (context) await context.close();
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_relation_path_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
