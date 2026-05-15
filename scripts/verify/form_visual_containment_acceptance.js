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
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const MODEL = process.env.MVP_MODEL || 'project.project';
const RECORD_ID = process.env.RECORD_ID || '771';
const ACTION_ID = process.env.ACTION_ID || '506';
const MENU_ID = process.env.MENU_ID || '353';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';

const ts = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const outDir = path.join(ARTIFACTS_DIR, 'form-visual-containment', ts);

const VIEWPORTS = [
  { id: 'desktop', width: 1440, height: 980 },
  { id: 'tablet', width: 900, height: 1180 },
  { id: 'mobile', width: 390, height: 844 },
];

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

async function login(page) {
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

async function openForm(page) {
  await page.goto(
    `${FRONTEND_URL}/r/${MODEL}/${RECORD_ID}?menu_id=${MENU_ID}&action_id=${ACTION_ID}`,
    { waitUntil: 'domcontentloaded', timeout: 45000 },
  );
  await page.locator('.template-layout-shell').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const text = String(document.querySelector('.template-layout-shell')?.textContent || '');
    return !text.includes('正在加载页面') && !text.includes('页面加载失败') && !text.includes('页面渲染失败');
  }, null, { timeout: 30000 });
}

async function visualProbe(page) {
  return page.evaluate(() => {
    const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const viewport = { width: window.innerWidth, height: window.innerHeight };
    const selectors = [
      '.template-layout-shell',
      '.page',
      '.native-statusbar',
      '.native-statusbar-step',
      '.native-actions--smart',
      '.native-action-btn--smart',
      '.native-tabs',
      '.native-tab',
      '.native-chatter-block',
      '.many2one-combobox',
      '.relation-editor',
      '.relation-dialog',
      '.relation-dialog-table-wrap',
    ];
    const nodes = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map((node, index) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          selector,
          index,
          text: normalize(node.textContent).slice(0, 120),
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          right: rect.right,
          bottom: rect.bottom,
          overflow_x: style.overflowX,
          overflow_y: style.overflowY,
          scroll_width: node.scrollWidth,
          client_width: node.clientWidth,
          scroll_height: node.scrollHeight,
          client_height: node.clientHeight,
          visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        };
      }),
    );
    const visibleNodes = nodes.filter((row) => row.visible);
    const clipped = visibleNodes.filter((row) => {
      if (['.template-layout-shell', '.page', '.native-statusbar', '.relation-dialog-table-wrap'].includes(row.selector)) return false;
      const allowsHorizontalScroll = ['auto', 'scroll'].includes(row.overflow_x);
      return row.scroll_width > row.client_width + 2 && !allowsHorizontalScroll;
    });
    const invalidBoxes = visibleNodes.filter((row) => row.width < 1 || row.height < 1);
    const offscreenCritical = visibleNodes.filter((row) => {
      if (![
        '.template-layout-shell',
        '.native-statusbar',
        '.native-statusbar-step',
        '.native-action-btn--smart',
        '.native-chatter-block',
        '.many2one-combobox',
        '.relation-dialog',
      ].includes(row.selector)) return false;
      if (row.selector === '.relation-dialog') {
        return row.x < 0 || row.y < 0 || row.right > viewport.width || row.bottom > viewport.height;
      }
      if (row.selector === '.native-statusbar' || row.selector === '.native-statusbar-step') return false;
      return row.right < 0 || row.x > viewport.width;
    });
    const overlaps = [];
    const critical = visibleNodes.filter((row) => [
      '.native-statusbar-step',
      '.native-action-btn--smart',
      '.native-tab',
      '.many2one-combobox',
    ].includes(row.selector));
    for (let i = 0; i < critical.length; i += 1) {
      for (let j = i + 1; j < critical.length; j += 1) {
        const a = critical[i];
        const b = critical[j];
        if (a.selector === b.selector && Math.abs(a.y - b.y) < 2) continue;
        const xOverlap = Math.max(0, Math.min(a.right, b.right) - Math.max(a.x, b.x));
        const yOverlap = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.y, b.y));
        const overlapArea = xOverlap * yOverlap;
        const minArea = Math.max(1, Math.min(a.width * a.height, b.width * b.height));
        if (overlapArea / minArea > 0.35) {
          overlaps.push({ a, b, ratio: Number((overlapArea / minArea).toFixed(3)) });
        }
      }
    }
    return {
      viewport,
      body_scroll_width: document.documentElement.scrollWidth,
      body_client_width: document.documentElement.clientWidth,
      horizontal_page_overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
      counts: selectors.reduce((acc, selector) => {
        acc[selector] = document.querySelectorAll(selector).length;
        return acc;
      }, {}),
      clipped,
      invalid_boxes: invalidBoxes,
      offscreen_critical: offscreenCritical,
      overlaps: overlaps.slice(0, 20),
    };
  });
}

async function openRelationDialog(page) {
  const button = page.locator('.many2one-combobox button:visible').filter({ hasText: '搜索更多' }).first();
  if ((await button.count().catch(() => 0)) === 0) {
    return false;
  }
  await button.click();
  await page.locator('.relation-dialog').waitFor({ timeout: 10000 });
  return true;
}

async function runViewport(browser, spec) {
  const context = await browser.newContext({
    locale: 'zh-CN',
    viewport: { width: spec.width, height: spec.height },
  });
  const page = await context.newPage();
  attachConsoleCapture(page);
  try {
    await login(page);
    await openForm(page);
    await page.screenshot({ path: path.join(outDir, `${spec.id}_form.png`), fullPage: true });
    const formProbe = await visualProbe(page);
    const dialogOpened = await openRelationDialog(page);
    let dialogProbe = {
      clipped: [],
      invalid_boxes: [],
      offscreen_critical: [],
      overlaps: [],
      skipped: true,
    };
    const screenshots = {
      form: path.join(outDir, `${spec.id}_form.png`),
    };
    if (dialogOpened) {
      screenshots.relation_dialog = path.join(outDir, `${spec.id}_relation_dialog.png`);
      await page.screenshot({ path: screenshots.relation_dialog, fullPage: true });
      dialogProbe = await visualProbe(page);
      dialogProbe.offscreen_critical = dialogProbe.offscreen_critical.filter((row) => row.selector === '.relation-dialog');
      dialogProbe.clipped = dialogProbe.clipped.filter((row) => row.selector === '.relation-dialog');
      await page.keyboard.press('Escape');
    }
    const pass = !formProbe.horizontal_page_overflow
      && formProbe.clipped.length === 0
      && formProbe.invalid_boxes.length === 0
      && formProbe.offscreen_critical.length === 0
      && formProbe.overlaps.length === 0
      && dialogProbe.clipped.length === 0
      && dialogProbe.invalid_boxes.length === 0
      && dialogProbe.offscreen_critical.length === 0
      && dialogProbe.overlaps.length === 0
      && (page.__consoleErrors || []).length === 0;
    return {
      id: spec.id,
      viewport: { width: spec.width, height: spec.height },
      status: pass ? 'pass' : 'fail',
      relation_dialog_opened: dialogOpened,
      screenshots,
      form_probe: formProbe,
      dialog_probe: dialogProbe,
      console_errors: page.__consoleErrors || [],
    };
  } finally {
    await context.close();
  }
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
    artifacts: outDir,
    paths: [],
  };
  try {
    for (const viewport of VIEWPORTS) {
      result.paths.push(await runViewport(browser, viewport));
    }
    result.pass = result.paths.every((row) => row.status === 'pass');
    writeJson('summary.json', result);
    console.log(`[form_visual_containment_acceptance] artifacts=${outDir}`);
    console.log(JSON.stringify({
      pass: result.pass,
      paths: result.paths.map((row) => ({ id: row.id, status: row.status })),
    }, null, 2));
    if (!result.pass) process.exit(1);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  writeJson('error.json', { message: err.message, stack: err.stack });
  console.error(`[form_visual_containment_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
