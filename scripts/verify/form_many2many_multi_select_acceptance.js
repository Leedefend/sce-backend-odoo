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
const RECORD_ID = Number(process.env.RECORD_ID || 771);
const ACTION_ID = Number(process.env.ACTION_ID || 506);
const MENU_ID = Number(process.env.MENU_ID || 353);
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-many2many-multi-select', ts);

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
  const dbInput = inputs.nth(2);
  if (await dbInput.count().catch(() => 0)) {
    const disabled = await dbInput.isDisabled().catch(() => false);
    if (!disabled) await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
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
        'X-Trace-Id': `form-m2m-multi-${Date.now()}`,
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
    };
  }, {
    dbName: DB_NAME,
    authToken,
    intentName: intent,
    payload: params,
    allowError: Boolean(options.allowError),
  });
}

async function createTag(page, label) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'create',
    model: 'project.tags',
    vals: { name: label },
    context: {},
  });
  return Number(resp.data.id || 0);
}

async function unlinkTag(page, id) {
  if (!id) return { ok: true };
  return intentRequest(page, 'api.data.unlink', {
    model: 'project.tags',
    ids: [id],
    context: {},
  }, { allowError: true });
}

async function readProjectTags(page) {
  const resp = await intentRequest(page, 'api.data', {
    op: 'read',
    model: 'project.project',
    ids: [RECORD_ID],
    fields: ['id', 'tag_ids'],
    context: {},
  });
  const row = Array.isArray(resp.data.records) ? resp.data.records[0] : null;
  return Array.isArray(row?.tag_ids) ? row.tag_ids : [];
}

async function restoreProjectTags(page, originalIds) {
  return intentRequest(page, 'api.data', {
    op: 'write',
    model: 'project.project',
    ids: [RECORD_ID],
    vals: { tag_ids: [[6, 0, originalIds]] },
    context: {},
  }, { allowError: true });
}

async function waitForFormReady(page) {
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    if (text.includes('页面加载失败') || text.includes('页面渲染失败')) return true;
    return !text.includes('正在加载页面');
  }, null, { timeout: 30000 });
}

async function openProject(page) {
  await page.goto(`${FRONTEND_URL}/r/project.project/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`, {
    waitUntil: 'domcontentloaded',
    timeout: 45000,
  });
  await waitForFormReady(page);
  const detailsTab = page.getByRole('button', { name: /明细与来源/ }).first();
  if (await detailsTab.count().catch(() => 0)) {
    await detailsTab.click();
  }
}

function tagEditor(page) {
  return page.locator('.relation-editor').first();
}

async function addTagByLabel(page, label) {
  const editor = tagEditor(page);
  const input = editor.locator('.relation-tags-input').first();
  await input.waitFor({ timeout: 15000 });
  await input.fill(label);
  const option = editor.locator('.relation-tag-option').filter({ hasText: label }).first();
  await option.waitFor({ timeout: 15000 });
  await option.click();
  await page.waitForFunction((target) => {
    return Array.from(document.querySelectorAll('.relation-tag'))
      .some((node) => String(node.textContent || '').includes(target));
  }, label, { timeout: 15000 });
}

async function saveForm(page) {
  await page.locator('.template-page-header-actions button.primary').filter({ hasText: /^保存$/ }).first().click();
  await page.getByText('保存成功，已同步最新表单内容。', { exact: true }).waitFor({ timeout: 20000 });
}

async function visibleTags(page) {
  return page.locator('.relation-tag').allInnerTexts()
    .then((items) => items.map((item) => normalize(item).replace(/\s*×$/, '').trim()))
    .catch(() => []);
}

async function removeTagByLabel(page, label) {
  const tag = tagEditor(page).locator('.relation-tag').filter({ hasText: label }).first();
  await tag.waitFor({ timeout: 15000 });
  await tag.click();
  await page.waitForFunction((target) => {
    return !Array.from(document.querySelectorAll('.relation-tag'))
      .some((node) => String(node.textContent || '').includes(target));
  }, label, { timeout: 15000 });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  attachConsoleCapture(page);

  const labels = [
    `P10 Multi Tag A ${Date.now()}`,
    `P10 Multi Tag B ${Date.now()}`,
  ];
  const summary = {
    pass: false,
    db: DB_NAME,
    login: LOGIN,
    model: 'project.project',
    record_id: RECORD_ID,
    action_id: ACTION_ID,
    menu_id: MENU_ID,
    artifact_dir: outDir,
    labels,
    checks: [],
    cleanup: {},
  };
  const tagIds = [];
  let originalTagIds = [];

  try {
    await login(page);
    originalTagIds = (await readProjectTags(page)).map((item) => Array.isArray(item) ? Number(item[0] || 0) : Number(item || 0)).filter(Boolean);
    for (const label of labels) {
      tagIds.push(await createTag(page, label));
    }
    await openProject(page);
    for (const label of labels) {
      await addTagByLabel(page, label);
    }
    await saveForm(page);
    await openProject(page);
    const tagsAfterSave = await visibleTags(page);
    const projectTagsAfterSave = await readProjectTags(page);

    for (const label of labels) {
      await removeTagByLabel(page, label);
    }
    await saveForm(page);
    await openProject(page);
    const tagsAfterRemove = await visibleTags(page);
    const projectTagsAfterRemove = await readProjectTags(page);

    summary.checks.push({
      path_id: 'P10',
      level: 'L4',
      scenario: 'many2many_select_multiple_remove_reload',
      status: labels.every((label) => tagsAfterSave.includes(label))
        && labels.every((label) => !tagsAfterRemove.includes(label))
        && tagIds.every((id) => JSON.stringify(projectTagsAfterSave).includes(String(id)))
        && tagIds.every((id) => !JSON.stringify(projectTagsAfterRemove).includes(String(id)))
        ? 'pass'
        : 'fail',
      tag_ids: tagIds,
      original_tag_ids: originalTagIds,
      tags_after_save: tagsAfterSave,
      project_tags_after_save: projectTagsAfterSave,
      tags_after_remove: tagsAfterRemove,
      project_tags_after_remove: projectTagsAfterRemove,
    });
  } catch (err) {
    summary.error = err instanceof Error ? err.stack || err.message : String(err);
  } finally {
    summary.cleanup.restore_project_tags = await restoreProjectTags(page, originalTagIds).catch((err) => ({
      ok: false,
      error: { message: err instanceof Error ? err.message : String(err) },
    }));
    summary.cleanup.unlink_tags = [];
    for (const id of tagIds) {
      summary.cleanup.unlink_tags.push(await unlinkTag(page, id).catch((err) => ({
        ok: false,
        id,
        error: { message: err instanceof Error ? err.message : String(err) },
      })));
    }
    summary.cleanup.project_tags_after_cleanup = await readProjectTags(page).catch((err) => ([
      { error: err instanceof Error ? err.message : String(err) },
    ]));
    summary.actionable_console_errors = (page.__consoleErrors || []).filter((line) =>
      !String(line).includes('favicon') && !String(line).includes('ResizeObserver'),
    );
    summary.pass = !summary.error
      && summary.checks.every((item) => item.status === 'pass')
      && summary.actionable_console_errors.length === 0
      && summary.cleanup.restore_project_tags?.ok !== false
      && summary.cleanup.unlink_tags.every((item) => item.ok !== false);
    await page.screenshot({ path: path.join(outDir, summary.pass ? 'final.png' : 'failure.png'), fullPage: true }).catch(() => {});
    writeJson('summary.json', summary);
    await browser.close();
  }

  if (!summary.pass) {
    console.error(JSON.stringify(summary, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(summary, null, 2));
}

main();
