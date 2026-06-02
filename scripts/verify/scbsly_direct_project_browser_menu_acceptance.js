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

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://1.95.85.92:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const LOGIN = process.env.E2E_LOGIN || 'wutao';
const PASSWORD = process.env.E2E_PASSWORD || '123456';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || 'artifacts';
const HEADLESS = String(process.env.HEADLESS || '1').trim() !== '0';
const OUT_DIR = path.join(
  ARTIFACTS_DIR,
  'browser',
  'scbsly-direct-project-menu',
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+$/, ''),
);

const EXPECTED_GROUPS = [
  {
    label: '合同类单据',
    leaves: ['施工合同', '分包合同', '租赁合同', '供货合同', '劳务合同', '机械合同（合同）'],
  },
  {
    label: '材料管理类单据',
    leaves: ['材料计划', '报价单', '入库', '材料结算单', '库存统计表（新）'],
  },
  {
    label: '劳务管理类单据',
    leaves: ['方单', '零星用工', '劳务结算'],
  },
  {
    label: '分包管理类单据',
    leaves: ['分包方单', '分包结算单'],
  },
  {
    label: '机械与租赁管理类单据',
    leaves: ['机械台班记录', '机械结算单', '租入', '还租', '租赁结算单'],
  },
  {
    label: '费用与资金管理类单据',
    leaves: [
      '项目费用报销单',
      '管理人员工资表',
      '油卡登记',
      '充值登记',
      '加油登记',
      '支付申请',
      '工程进度收款',
      '往来单位付款',
      '工程结算单',
      '进项上报',
      '总包进项上报',
      '成本统计表（数据）',
    ],
  },
  {
    label: '项目管理类单据',
    leaves: ['施工日志（新）'],
  },
];

const EXPECTED_LABELS = [
  '旧业务数据核对',
  '直营项目数据核对',
  ...EXPECTED_GROUPS.flatMap((group) => group.leaves),
];

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeJson(name, payload) {
  ensureDir(OUT_DIR);
  fs.writeFileSync(path.join(OUT_DIR, name), JSON.stringify(payload, null, 2) + '\n', 'utf8');
}

function writeMarkdown(report) {
  const lines = [
    '# SCBSLY Direct Project Browser Menu Acceptance',
    '',
    `- ok: ${report.ok}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- login: ${report.login}`,
    `- expected_count: ${report.summary.expected_count}`,
    `- visible_count: ${report.summary.visible_count}`,
    `- missing_count: ${report.summary.missing_count}`,
    `- collapsed_toggle_clicks: ${report.summary.collapsed_toggle_clicks}`,
    '',
    '| label | visible | count |',
    '| --- | ---: | ---: |',
  ];
  for (const row of report.rows) {
    lines.push(`| ${row.label} | ${row.visible ? 'yes' : 'no'} | ${row.count} |`);
  }
  fs.writeFileSync(path.join(OUT_DIR, 'report.md'), lines.join('\n') + '\n', 'utf8');
}

async function login(page) {
  await page.goto(`${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`, {
    waitUntil: 'networkidle',
    timeout: 45000,
  });
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const dbInput = page.locator('input[autocomplete="off"]');
  if (await dbInput.isEditable().catch(() => false)) {
    await dbInput.fill(DB_NAME);
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 45000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => undefined);
  await page.waitForSelector('[data-component="SidebarNav"] .menu', { timeout: 30000 });
}

async function expandAllVisibleMenuToggles(page) {
  let totalClicks = 0;
  for (let round = 0; round < 40; round += 1) {
    const clicked = await page.evaluate(() => {
      function isVisible(element) {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== 'none'
          && style.visibility !== 'hidden'
          && Number(style.opacity || 1) !== 0
          && rect.width > 0
          && rect.height > 0;
      }
      const toggles = Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.toggle'))
        .filter((button) => isVisible(button) && String(button.textContent || '').includes('▸'));
      for (const button of toggles) {
        button.click();
      }
      return toggles.length;
    });
    totalClicks += clicked;
    if (!clicked) break;
    await page.waitForTimeout(120);
  }
  return totalClicks;
}

async function collectMenuLabels(page) {
  return page.evaluate(() => {
    function normalizeText(value) {
      return String(value || '').replace(/\s+/g, ' ').trim();
    }
    function isVisible(element) {
      const style = window.getComputedStyle(element);
      const rects = element.getClientRects();
      const rect = element.getBoundingClientRect();
      return style.display !== 'none'
        && style.visibility !== 'hidden'
        && Number(style.opacity || 1) !== 0
        && rects.length > 0
        && rect.width > 0
        && rect.height > 0;
    }
    return Array.from(document.querySelectorAll('[data-component="SidebarNav"] .menu button.label'))
      .filter((button) => isVisible(button))
      .map((button) => ({
        text: normalizeText(button.textContent),
        title: normalizeText(button.getAttribute('title')),
        disabled: Boolean(button.disabled),
        rect: (() => {
          const rect = button.getBoundingClientRect();
          return {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          };
        })(),
      }));
  });
}

async function main() {
  ensureDir(OUT_DIR);
  const browser = await chromium.launch({ headless: HEADLESS });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  const consoleMessages = [];
  const pageErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleMessages.push(normalize(message.text()));
    }
  });
  page.on('pageerror', (error) => pageErrors.push(normalize(error.message)));

  try {
    await login(page);
    await page.screenshot({ path: path.join(OUT_DIR, '01-after-login-before-expand.png'), fullPage: true });
    const collapsedToggleClicks = await expandAllVisibleMenuToggles(page);
    await page.waitForTimeout(300);
    const labels = await collectMenuLabels(page);
    const bodyText = normalize(await page.locator('body').innerText({ timeout: 5000 }).catch(() => ''));
    await page.screenshot({ path: path.join(OUT_DIR, '02-after-expand-all.png'), fullPage: true });

    const visibleByLabel = new Map();
    for (const item of labels) {
      visibleByLabel.set(item.text, (visibleByLabel.get(item.text) || 0) + 1);
    }
    const rows = EXPECTED_LABELS.map((label) => ({
      label,
      visible: visibleByLabel.has(label),
      count: visibleByLabel.get(label) || 0,
    }));
    const missing = rows.filter((row) => !row.visible).map((row) => row.label);
    const report = {
      ok: missing.length === 0,
      frontend_url: FRONTEND_URL,
      db_name: DB_NAME,
      login: LOGIN,
      out_dir: OUT_DIR,
      summary: {
        expected_count: EXPECTED_LABELS.length,
        visible_count: rows.filter((row) => row.visible).length,
        missing_count: missing.length,
        collapsed_toggle_clicks: collapsedToggleClicks,
      },
      missing,
      rows,
      observed_labels: labels,
      body_sample: bodyText.slice(0, 2000),
      console_errors: consoleMessages,
      page_errors: pageErrors,
      screenshots: [
        path.join(OUT_DIR, '01-after-login-before-expand.png'),
        path.join(OUT_DIR, '02-after-expand-all.png'),
      ],
    };
    writeJson('report.json', report);
    writeMarkdown(report);
    console.log(JSON.stringify(report.summary, null, 2));
    console.log(`SCBSLY_DIRECT_PROJECT_BROWSER_MENU=${report.ok ? 'PASS' : 'FAIL'}`);
    if (!report.ok) {
      console.error(`missing=${missing.join(', ')}`);
      process.exitCode = 1;
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
