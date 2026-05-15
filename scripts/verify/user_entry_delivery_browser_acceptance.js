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
const ROOT_DIR = fs.existsSync(path.join(process.cwd(), 'frontend/apps/web/package.json'))
  ? process.cwd()
  : path.resolve(process.cwd(), '../../..');

const FRONTEND_URL = process.env.FRONTEND_URL || process.env.E2E_BASE_URL || 'http://localhost:18081';
const DB_NAME = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const DEFAULT_PASSWORD = process.env.E2E_ROLE_MATRIX_DEFAULT_PASSWORD || process.env.E2E_PASSWORD || 'demo';
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.join(ROOT_DIR, 'artifacts');
const HEADLESS = String(process.env.HEADLESS || '1').trim() !== '0';

const REPORT_JSON = path.join(ARTIFACTS_DIR, 'backend', 'user_entry_delivery_browser_acceptance.json');
const REPORT_MD = path.join(ARTIFACTS_DIR, 'backend', 'user_entry_delivery_browser_acceptance.md');

const ROLES = [
  {
    role: 'executive',
    login: process.env.ROLE_EXECUTIVE_LOGIN || 'demo_role_executive',
    password: process.env.ROLE_EXECUTIVE_PASSWORD || DEFAULT_PASSWORD,
    mode: 'home_today',
    initialText: [/今天先做什么/, /付款申请待审批|任务逾期风险|项目跟进/],
    clickButton: /查看详情/,
    targetPath: /^\/(s\/(finance\.payment_requests|project\.management|task\.center|risk\.center)|r\/)/,
  },
  {
    role: 'pm',
    login: process.env.ROLE_PM_LOGIN || 'demo_role_pm',
    password: process.env.ROLE_PM_PASSWORD || DEFAULT_PASSWORD,
    mode: 'direct_business',
    initialText: [/项目列表/],
    targetPath: /^\/s\/projects\.list/,
  },
  {
    role: 'pm_my_work_menu',
    login: process.env.ROLE_PM_LOGIN || 'demo_role_pm',
    password: process.env.ROLE_PM_PASSWORD || DEFAULT_PASSWORD,
    mode: 'menu_my_work',
    navigatePath: '/my-work',
    initialText: [/我的工作/, /待办|风险|已完成|失败/],
    targetPath: /^\/(my-work|s\/my_work\.workspace)$/,
  },
  {
    role: 'pm_my_work_back_home',
    login: process.env.ROLE_PM_LOGIN || 'demo_role_pm',
    password: process.env.ROLE_PM_PASSWORD || DEFAULT_PASSWORD,
    mode: 'my_work_back_home',
    navigatePath: '/my-work',
    initialText: [/我的工作/, /待办|风险|已完成|失败/],
    clickButton: /返回角色首页/,
    targetPath: /^\/(s\/workspace\.home|s\/projects\.list|)?$/,
  },
  {
    role: 'finance',
    login: process.env.ROLE_FINANCE_LOGIN || 'demo_role_finance',
    password: process.env.ROLE_FINANCE_PASSWORD || DEFAULT_PASSWORD,
    mode: 'direct_business',
    initialText: [/付款申请|付款申请审批|PRQ|新建|记录/],
    targetPath: /^\/s\/finance\.payment_requests/,
  },
];

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function writeReports(report) {
  ensureDir(REPORT_JSON);
  fs.writeFileSync(REPORT_JSON, JSON.stringify(report, null, 2) + '\n', 'utf8');

  const lines = [
    '# User Entry Delivery Browser Acceptance',
    '',
    `- ok: ${report.ok}`,
    `- frontend_url: ${report.frontend_url}`,
    `- db_name: ${report.db_name}`,
    `- role_count: ${report.summary.role_count}`,
    `- pass_count: ${report.summary.pass_count}`,
    `- error_count: ${report.summary.error_count}`,
    '',
    '| role | mode | initial_path | final_path | expected_text | first_screen | no_debug_noise | product_order | click_chain | one_hop | errors |',
    '| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
  ];
  for (const row of report.rows) {
    lines.push(
      `| ${row.role} | ${row.mode} | ${row.initial_path || ''} | ${row.final_path || ''} | ${row.expected_text_ok ? 'yes' : 'no'} | ${row.first_screen_ok ? 'yes' : 'n/a'} | ${row.no_debug_noise ? 'yes' : 'no'} | ${row.product_order_ok ? 'yes' : 'n/a'} | ${row.click_chain_ok ? 'yes' : 'n/a'} | ${row.one_hop_ok ? 'yes' : 'n/a'} | ${row.errors.length} |`,
    );
  }
  ensureDir(REPORT_MD);
  fs.writeFileSync(REPORT_MD, lines.join('\n') + '\n', 'utf8');
}

function hasBlockingError(text) {
  return /NAV_MENU_NO_ACTION|scene not found|当前账号暂无可用功能|当前无可用入口|页面加载失败|页面渲染失败|System exception/i.test(String(text || ''));
}

function summarizeClickChain(events) {
  const rows = Array.isArray(events) ? events : [];
  const telemetryEvents = rows
    .filter((row) => row.intent === 'telemetry.track')
    .map((row) => row.event_type)
    .filter(Boolean);
  const businessIntents = rows
    .map((row) => row.intent)
    .filter((intent) => ['ui.contract', 'ui.contract.v2', 'load_view', 'api.data'].includes(intent));
  return {
    telemetry_events: Array.from(new Set(telemetryEvents)),
    business_intents: Array.from(new Set(businessIntents)),
    telemetry_ok: telemetryEvents.some((eventType) => /^workspace\./.test(eventType)),
    business_intent_ok: businessIntents.length > 0,
  };
}

function firstTextIndex(text, patterns) {
  const candidates = patterns
    .map((pattern) => String(text || '').search(pattern))
    .filter((idx) => idx >= 0);
  return candidates.length ? Math.min(...candidates) : -1;
}

async function firstVisibleBox(page, pattern) {
  const locator = page.getByText(pattern).first();
  if (!(await locator.count())) return null;
  const box = await locator.boundingBox().catch(() => null);
  return box ? {
    x: Math.round(box.x),
    y: Math.round(box.y),
    width: Math.round(box.width),
    height: Math.round(box.height),
  } : null;
}

function boxInFirstScreen(box, viewport) {
  if (!box || !viewport) return false;
  return box.y >= 0 && box.y < Math.max(1, viewport.height - 24);
}

async function checkFirstScreen(page, role) {
  if (!/^home_/.test(role.mode)) {
    return { ok: true, boxes: {} };
  }
  const viewport = page.viewportSize() || { width: 1440, height: 960 };
  const boxes = {
    today: await firstVisibleBox(page, /今天先做什么|今日优先动作/),
    risk: await firstVisibleBox(page, /系统提醒（高优先）|风险待处理清单/),
    action: await firstVisibleBox(page, role.clickButton),
  };
  const todayOk = boxInFirstScreen(boxes.today, viewport);
  const riskOk = role.mode === 'home_today_and_risk' ? boxInFirstScreen(boxes.risk, viewport) : true;
  const actionOk = boxInFirstScreen(boxes.action, viewport);
  return { ok: todayOk && riskOk && actionOk, boxes };
}

function checkProductOrder(text, role) {
  if (!/^home_/.test(role.mode)) {
    return { ok: true, positions: {} };
  }
  const positions = {
    today: firstTextIndex(text, [/今天先做什么/, /今日优先动作/]),
    risk: firstTextIndex(text, [/系统提醒（高优先）/, /风险待处理清单/]),
    quick: firstTextIndex(text, [/我可以做什么/, /可使用的业务域/]),
  };
  const todayBeforeQuick = positions.today >= 0 && positions.quick >= 0 && positions.today < positions.quick;
  const riskBeforeQuick = role.mode === 'home_today_and_risk'
    ? positions.risk >= 0 && positions.risk < positions.quick
    : true;
  return { ok: todayBeforeQuick && riskBeforeQuick, positions };
}

function checkMenuMyWorkIntent(row) {
  if (!['menu_my_work', 'my_work_back_home'].includes(row.mode)) return true;
  return row.captured_intents.includes('my.work.summary');
}

async function login(page, role) {
  const url = `${FRONTEND_URL}/login?db=${encodeURIComponent(DB_NAME)}&t=${Date.now()}`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.locator('input[autocomplete="username"]').fill(role.login);
  await page.locator('input[autocomplete="current-password"]').fill(role.password);
  const dbInput = page.locator('input[autocomplete="off"]');
  const dbEditable = await dbInput.isEditable().catch(() => false);
  if (dbEditable) {
    await dbInput.fill(DB_NAME);
  } else {
    const currentDb = normalize(await dbInput.inputValue().catch(() => ''));
    if (currentDb && currentDb !== DB_NAME) {
      throw new Error(`login db input is locked to ${currentDb}, expected ${DB_NAME}`);
    }
  }
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), null, { timeout: 30000 });
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForFunction(() => {
    const text = String(document.body?.textContent || '');
    return !text.includes('正在加载场景') && !text.includes('正在加载页面');
  }, null, { timeout: 12000 }).catch(() => {});
}

async function waitForRoleText(page, role) {
  await page.waitForFunction((sources) => {
    const text = String(document.body?.textContent || '');
    if (text.includes('正在加载场景') || text.includes('正在加载页面')) return false;
    return sources.every((source) => new RegExp(source).test(text));
  }, role.initialText.map((pattern) => pattern.source), { timeout: 18000 }).catch(() => {});
}

async function runRole(browser, role) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const intentEvents = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(err.message));
  page.on('request', (request) => {
    if (!request.url().includes('/api/v1/intent')) return;
    try {
      const payload = JSON.parse(request.postData() || '{}');
      if (payload.intent) {
        const params = payload.params && typeof payload.params === 'object' ? payload.params : {};
        intentEvents.push({
          intent: String(payload.intent),
          event_type: typeof params.event_type === 'string' ? params.event_type : '',
        });
      }
    } catch {
      // ignore non-json request bodies
    }
  });

  const row = {
    role: role.role,
    login: role.login,
    mode: role.mode,
    initial_path: '',
    final_path: '',
    expected_text_ok: false,
    no_blocking_empty: false,
    first_screen_ok: role.mode === 'direct_business',
    first_screen_boxes: {},
    no_debug_noise: false,
    product_order_ok: role.mode === 'direct_business',
    order_positions: {},
    one_hop_ok: role.mode === 'direct_business' || role.mode === 'menu_my_work',
    click_chain_ok: role.mode === 'direct_business' || role.mode === 'menu_my_work',
    click_chain: {
      clicked_button: '',
      telemetry_events: [],
      business_intents: [],
      telemetry_ok: role.mode === 'direct_business' || role.mode === 'menu_my_work',
      business_intent_ok: role.mode === 'direct_business' || role.mode === 'menu_my_work',
    },
    captured_intents: [],
    captured_telemetry_events: [],
    console_errors: [],
    errors: [],
    ok: false,
  };

  try {
    await login(page, role);
    await waitForRoleText(page, role);
    row.initial_path = new URL(page.url()).pathname;
    let text = await page.locator('body').innerText({ timeout: 10000 });
    if (role.navigatePath) {
      await page.goto(`${FRONTEND_URL}${role.navigatePath}`, { waitUntil: 'networkidle' });
      await page.waitForFunction(() => {
        const text = String(document.body?.textContent || '');
        return !text.includes('正在加载场景') && !text.includes('正在加载页面');
      }, null, { timeout: 12000 }).catch(() => {});
      await waitForRoleText(page, role);
      row.initial_path = new URL(page.url()).pathname;
      row.final_path = row.initial_path;
      text = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
    }
    row.expected_text_ok = role.initialText.every((pattern) => pattern.test(text));
    row.no_blocking_empty = !hasBlockingError(text);
    row.no_debug_noise = !/result_summary|active_filters|debug|traceback/i.test(text);
    const firstScreen = await checkFirstScreen(page, role);
    row.first_screen_ok = firstScreen.ok;
    row.first_screen_boxes = firstScreen.boxes;
    if (!row.no_debug_noise) {
      row.errors.push('debug_noise_visible');
    }
    if (!row.first_screen_ok) {
      row.errors.push(`first_screen=${JSON.stringify(row.first_screen_boxes)}`);
    }
    const productOrder = checkProductOrder(text, role);
    row.product_order_ok = productOrder.ok;
    row.order_positions = productOrder.positions;
    if (!row.product_order_ok) {
      row.errors.push(`product_order=${JSON.stringify(row.order_positions)}`);
    }

    if (role.mode === 'direct_business' || role.mode === 'menu_my_work') {
      row.one_hop_ok = role.targetPath.test(row.initial_path);
      if (role.mode === 'menu_my_work' && !row.one_hop_ok) {
        row.errors.push(`menu_my_work_path=${row.initial_path}`);
      }
    } else {
      const button = page.getByRole('button', { name: role.clickButton }).first();
      const count = await button.count();
      if (!count) {
        row.errors.push(`missing click button: ${role.clickButton}`);
      } else {
        const clickStartedAt = intentEvents.length;
        row.click_chain.clicked_button = String(role.clickButton);
        await button.click();
        await page.waitForLoadState('networkidle').catch(() => {});
        await page.waitForTimeout(1200);
        row.final_path = new URL(page.url()).pathname;
        text = await page.locator('body').innerText().catch(() => '');
        row.one_hop_ok = role.targetPath.test(row.final_path) && !hasBlockingError(text);
        row.click_chain = {
          ...row.click_chain,
          ...summarizeClickChain(intentEvents.slice(clickStartedAt)),
        };
        row.click_chain_ok = role.mode === 'my_work_back_home'
          ? row.click_chain.telemetry_ok
          : row.click_chain.telemetry_ok && row.click_chain.business_intent_ok;
        if (!row.click_chain_ok) {
          row.errors.push(`click_chain=${JSON.stringify(row.click_chain)}`);
        }
      }
    }
  } catch (err) {
    row.errors.push(err && err.message ? err.message : String(err));
  } finally {
    row.captured_intents = Array.from(new Set(intentEvents.map((event) => event.intent)));
    row.captured_telemetry_events = Array.from(new Set(intentEvents.map((event) => event.event_type).filter(Boolean)));
    if (!checkMenuMyWorkIntent(row)) {
      row.errors.push(`missing_my_work_summary_intent=${JSON.stringify(row.captured_intents)}`);
    }
    row.console_errors = consoleErrors.slice(0, 20);
    if (consoleErrors.length) {
      row.errors.push(`console_errors=${consoleErrors.length}`);
    }
    row.ok = row.expected_text_ok && row.no_blocking_empty && row.first_screen_ok && row.no_debug_noise && row.product_order_ok && row.one_hop_ok && row.click_chain_ok && row.errors.length === 0;
    await context.close();
  }
  return row;
}

async function main() {
  const browser = await chromium.launch({ headless: HEADLESS });
  let rows = [];
  try {
    for (const role of ROLES) {
      rows.push(await runRole(browser, role));
    }
  } finally {
    await browser.close();
  }

  const report = {
    ok: rows.every((row) => row.ok),
    frontend_url: FRONTEND_URL,
    db_name: DB_NAME,
    summary: {
      role_count: rows.length,
      pass_count: rows.filter((row) => row.ok).length,
      error_count: rows.reduce((acc, row) => acc + row.errors.length, 0),
    },
    rows,
  };
  writeReports(report);
  if (!report.ok) {
    console.error(`[user_entry_delivery_browser_acceptance] FAIL ${REPORT_JSON}`);
    console.error(JSON.stringify(report.summary, null, 2));
    process.exit(1);
  }
  console.log(`[user_entry_delivery_browser_acceptance] PASS ${REPORT_JSON}`);
}

main().catch((err) => {
  console.error(`[user_entry_delivery_browser_acceptance] FAIL: ${err.message}`);
  process.exit(1);
});
