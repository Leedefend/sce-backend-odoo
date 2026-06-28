#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const ROOT = path.resolve(__dirname, '..', '..');
const requireFromWeb = createRequire(path.join(ROOT, 'frontend/apps/web/package.json'));
const { chromium } = requireFromWeb('playwright');

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT, 'artifacts');
const RUN_ID = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const OUT_DIR = path.join(ARTIFACTS_DIR, 'business-config-form-layout', RUN_ID);

const ALL_TARGETS = [
  {
    id: 'project_intake',
    title: '项目立项',
    path: '/f/project.project/new',
    final_columns: '3',
    params: {
      scene_label: '项目立项',
      scene_key: 'projects.intake',
      intake_mode: 'standard',
    },
  },
  {
    id: 'general_contract',
    title: '一般合同',
    path: '/f/sc.general.contract/new',
    params: {
      menu_id: '361',
      action_id: '669',
      product_domain: 'contract',
    },
  },
];

function requestedTargets() {
  const requested = String(process.env.ACCEPTANCE_TARGETS || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  if (!requested.length) return ALL_TARGETS;
  const wanted = new Set(requested);
  return ALL_TARGETS.filter((target) => wanted.has(target.id));
}

function ensureOutDir() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}

function writeJson(name, data) {
  ensureOutDir();
  fs.writeFileSync(path.join(OUT_DIR, name), JSON.stringify(data, null, 2), 'utf8');
}

function buildUrl(target, configMode) {
  const url = new URL(target.path, FRONTEND_URL);
  url.searchParams.set('db', DB_NAME);
  Object.entries(target.params || {}).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });
  if (configMode) {
    url.searchParams.set('config_mode', 'business_config_lowcode');
  }
  url.searchParams.set('_acceptance', `${RUN_ID}_${target.id}_${configMode ? 'config' : 'runtime'}`);
  return url.toString();
}

function countGridColumns(value) {
  return String(value || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function alternateColumns(value) {
  const current = Number(value);
  if (current === 3) return '2';
  return '3';
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  if ((await inputs.count()) > 2) {
    const dbInput = inputs.nth(2);
    if (!(await dbInput.isDisabled().catch(() => true))) {
      await dbInput.fill(DB_NAME);
    }
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 30000 });
  await page.waitForTimeout(1500);
}

async function waitForFormStable(page) {
  await page.waitForFunction(() => {
    const text = document.body?.innerText || '';
    const visibleGrids = Array.from(document.querySelectorAll('.template-form-section-grid')).filter((grid) => {
      const rect = grid.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && getComputedStyle(grid).gridTemplateColumns.trim();
    });
    return !text.includes('正在读取配置能力')
      && !text.includes('正在加载页面')
      && !text.includes('页面加载失败')
      && visibleGrids.length > 0;
  }, null, { timeout: 45000 });
  await page.waitForTimeout(3000);
}

async function snapshot(page, label) {
  return page.evaluate((label) => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const text = normalize(document.body?.innerText || '');
    const layoutSelect = Array.from(document.querySelectorAll('select')).find((node) => (
      node.closest('.contract-form-layout-tools')
    ));
    const buttons = Array.from(document.querySelectorAll('button'))
      .map((node) => ({ text: normalize(node.textContent), disabled: node.disabled }))
      .filter((button) => /预览|保存|重置|检查/.test(button.text));
    const grids = Array.from(document.querySelectorAll('.template-form-section-grid')).slice(0, 12).map((grid) => {
      const section = grid.closest('.template-form-section');
      const rect = grid.getBoundingClientRect();
      return {
        title: normalize(section?.querySelector('.template-form-section-title')?.textContent),
        columns: getComputedStyle(grid).gridTemplateColumns,
        fields: grid.querySelectorAll('[data-field-name]').length,
        visible: rect.width > 0 && rect.height > 0,
      };
    });
    return {
      label,
      url: location.href,
      select_value: layoutSelect?.value || '',
      has_designer: text.includes('页面布局') && text.includes('表单画布'),
      buttons,
      grids,
      body_head: text.slice(0, 500),
    };
  }, label);
}

async function openConfig(page, target) {
  await page.goto(buildUrl(target, true), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForFormStable(page);
}

async function selectColumns(page, columns) {
  const select = page.locator('.contract-form-layout-tools select').first();
  await select.waitFor({ timeout: 15000 });
  await select.selectOption(columns);
  await page.waitForTimeout(1000);
}

async function saveAndPreview(page, target, expectedColumns, suffix) {
  const button = page.getByRole('button', { name: /保存并预览/ });
  await button.waitFor({ timeout: 15000 });
  await button.click();
  await page.waitForURL((url) => !url.searchParams.has('config_mode'), { timeout: 45000 });
  await waitForFormStable(page);
  const result = await snapshot(page, `${target.id}-${suffix}`);
  const firstGrid = result.grids.find((grid) => grid.visible && grid.fields > 0 && countGridColumns(grid.columns) > 0)
    || result.grids.find((grid) => grid.visible && countGridColumns(grid.columns) > 0)
    || result.grids[0];
  const actualColumns = countGridColumns(firstGrid && firstGrid.columns);
  if (result.has_designer) {
    const err = new Error(`${target.id} expected runtime preview, still in designer`);
    err.previewSnapshot = result;
    throw err;
  }
  if (actualColumns !== Number(expectedColumns)) {
    const err = new Error(`${target.id} expected ${expectedColumns} columns, got ${actualColumns}`);
    err.previewSnapshot = result;
    throw err;
  }
  return result;
}

async function runTarget(page, target) {
  await openConfig(page, target);
  const initial = await snapshot(page, `${target.id}-initial`);
  const originalColumns = initial.select_value;
  if (!['1', '2', '3'].includes(originalColumns)) {
    throw new Error(`${target.id} invalid initial columns: ${originalColumns}`);
  }

  const candidateColumns = alternateColumns(originalColumns);
  const finalColumns = target.final_columns || originalColumns;
  let dirty = null;
  let changedPreview = null;
  let restoreDirty = null;
  let restoredPreview = null;
  let restoreAttempted = false;
  try {
    await selectColumns(page, candidateColumns);
    dirty = await snapshot(page, `${target.id}-dirty-${candidateColumns}`);
    const saveButton = dirty.buttons.find((button) => button.text.includes('保存表单设置'));
    if (!saveButton || saveButton.disabled) {
      throw new Error(`${target.id} save button did not become enabled after column change`);
    }
    changedPreview = await saveAndPreview(page, target, candidateColumns, `preview-${candidateColumns}`);

    if (candidateColumns === finalColumns) {
      restoreAttempted = true;
      restoredPreview = changedPreview;
      restoreDirty = {
        skipped: true,
        reason: 'candidate already equals final columns',
      };
    } else {
      await openConfig(page, target);
      await selectColumns(page, finalColumns);
      restoreDirty = await snapshot(page, `${target.id}-restore-dirty-${finalColumns}`);
      const restoreSaveButton = restoreDirty.buttons.find((button) => button.text.includes('保存表单设置'));
      if (!restoreSaveButton || restoreSaveButton.disabled) {
        throw new Error(`${target.id} restore save button did not become enabled`);
      }
      restoreAttempted = true;
      restoredPreview = await saveAndPreview(page, target, finalColumns, `restored-${finalColumns}`);
    }
  } catch (err) {
    if (!restoreAttempted) {
      await openConfig(page, target).catch(() => null);
      await selectColumns(page, finalColumns).catch(() => null);
      restoreDirty = await snapshot(page, `${target.id}-restore-after-error-${finalColumns}`).catch(() => null);
      const restoreButton = restoreDirty && restoreDirty.buttons.find((button) => button.text.includes('保存表单设置'));
      if (restoreButton && !restoreButton.disabled) {
        restoreAttempted = true;
        restoredPreview = await saveAndPreview(page, target, finalColumns, `restored-after-error-${finalColumns}`).catch(() => null);
      }
    }
    err.acceptanceContext = {
      target: target.id,
      originalColumns,
      candidateColumns,
      finalColumns,
      initial,
      dirty,
      changedPreview,
      restoreDirty,
      restoredPreview,
      restoreAttempted,
      previewSnapshot: err.previewSnapshot || null,
    };
    throw err;
  }

  return {
    target: target.id,
    title: target.title,
    original_columns: originalColumns,
    candidate_columns: candidateColumns,
    final_columns: finalColumns,
    initial,
    dirty,
    changed_preview: changedPreview,
    restore_dirty: restoreDirty,
    restored_preview: restoredPreview,
  };
}

(async () => {
  const targets = requestedTargets();
  if (!targets.length) {
    throw new Error('No acceptance targets selected');
  }
  const browser = await chromium.launch({ headless: process.env.HEADLESS !== '0' });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: 'zh-CN' });
  const responses = [];
  page.on('response', (response) => {
    const url = response.url();
    if (/ui\.business_config\.contract\.save|ui\.contract\.v2|business_config/.test(url)) {
      responses.push({ status: response.status(), url: url.slice(0, 220) });
    }
  });
  try {
    await login(page);
    const results = [];
    for (const target of targets) {
      results.push(await runTarget(page, target));
    }
    const report = {
      ok: true,
      frontend_url: FRONTEND_URL,
      db: DB_NAME,
      targets: results,
      responses,
      artifacts_dir: OUT_DIR,
    };
    writeJson('report.json', report);
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch((err) => {
  ensureOutDir();
  writeJson('error.json', {
    ok: false,
    message: err.message,
    stack: err.stack,
    acceptance_context: err.acceptanceContext || null,
  });
  console.error(err);
  process.exit(1);
});
