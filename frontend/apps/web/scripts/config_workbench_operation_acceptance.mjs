import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const ROOT_MENU_XMLID = process.env.LOW_CODE_MENU_ROOT_XMLID || "smart_construction_core.menu_sc_root";
const CONFIG_MODEL = process.env.LOW_CODE_CONFIG_MODEL || "construction.contract";
const CONFIG_ACTION_ID = Number(process.env.LOW_CODE_CONFIG_ACTION_ID || 562);
const CONFIG_PAGE_LABEL = process.env.LOW_CODE_CONFIG_PAGE_LABEL || "项目合同汇总";
const SWITCH_PAGE_LABEL = process.env.LOW_CODE_SWITCH_PAGE_LABEL || "合同办理";
const ARTIFACT_ROOT = path.resolve(process.cwd(), "../../../artifacts/playwright/config-workbench-operation");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");
const ACCEPTANCE_COVERAGE = {
  journeys: [
    "workbench_select_page",
    "workbench_search_switch_page",
    "workbench_direct_selected",
    "list_search_config_entry",
    "approval_config_entry",
    "form_designer_entry",
    "workbench_to_menu_config",
    "menu_config_return_workbench",
    "mobile_selected_page",
    "browser_health",
  ],
  actions: [
    "login",
    "open_workbench",
    "open_page_picker",
    "search_page",
    "select_page",
    "switch_page",
    "open_direct_selected_url",
    "open_list_search_config",
    "open_approval_config",
    "open_form_designer",
    "return_from_form_designer",
    "open_menu_config",
    "return_to_workbench",
    "open_mobile_workbench",
    "mobile_select_page",
  ],
  assertions: [
    "page_picker_retained_after_select",
    "selected_context_visible",
    "selected_cards_complete",
    "search_result_exact",
    "switch_title_synced",
    "switch_cards_complete",
    "direct_selected_cards_visible",
    "direct_delivery_status_visible",
    "list_search_editor_visible",
    "list_search_tabs_complete",
    "approval_editor_visible",
    "approval_rule_canvas_visible",
    "form_designer_visible",
    "form_designer_return_visible",
    "menu_side_sections_complete",
    "menu_tree_not_empty",
    "return_context_retained",
    "mobile_config_before_picker",
    "mobile_no_horizontal_overflow",
    "no_console_errors",
    "no_request_failures",
  ],
  screenshotKeys: [
    "selectedFromScan",
    "switchedPage",
    "directSelected",
    "listSearchEntry",
    "approvalEntry",
    "formDesignerEntry",
    "menuConfig",
    "mobileSelected",
  ],
};

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function findCachedChromiumExecutable() {
  const explicit = process.env.CHROMIUM_EXECUTABLE_PATH || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "";
  if (explicit && fsSync.existsSync(explicit)) return explicit;
  const cacheRoot = path.join(process.env.HOME || "", ".cache", "ms-playwright");
  if (!cacheRoot || !fsSync.existsSync(cacheRoot)) return "";
  return fsSync.readdirSync(cacheRoot)
    .filter((name) => name.startsWith("chromium_headless_shell-") || name.startsWith("chromium-"))
    .sort()
    .reverse()
    .flatMap((name) => [
      path.join(cacheRoot, name, "chrome-headless-shell-linux64", "chrome-headless-shell"),
      path.join(cacheRoot, name, "chrome-linux64", "chrome"),
    ])
    .find((item) => fsSync.existsSync(item)) || "";
}

function configWorkbenchUrl(extra = {}) {
  const params = new URLSearchParams({
    root_menu_xmlid: ROOT_MENU_XMLID,
    db: DB_NAME,
    ...extra,
  });
  return `${BASE_URL}/admin/business-config?${params.toString()}`;
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator("input").count() >= 3) {
    const dbInput = page.locator("input").nth(2);
    if (await dbInput.isEnabled().catch(() => false)) await dbInput.fill(DB_NAME);
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), null, { timeout: 60000 });
}

async function visibleCardTitles(page, scope = "") {
  return page.locator(`${scope} [data-lowcode-config-task-card="v1"] h2`).evaluateAll((nodes) => (
    nodes.map((node) => node.textContent?.trim()).filter(Boolean)
  ));
}

async function openDirectSelectedWorkbench(page) {
  await page.goto(configWorkbenchUrl({
    model: CONFIG_MODEL,
    action_id: String(CONFIG_ACTION_ID),
    page_label: CONFIG_PAGE_LABEL,
  }), { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForSelector('[data-lowcode-workbench-ia="start"] [data-lowcode-config-task-card="v1"]', { timeout: 60000 });
}

async function clickConfigCardButton(page, cardTitle, buttonName) {
  const card = page.locator('[data-lowcode-config-task-card="v1"]').filter({ hasText: cardTitle }).first();
  await card.waitFor({ state: "visible", timeout: 60000 });
  await card.getByRole("button", { name: buttonName }).click();
}

async function capture(page, name) {
  const filePath = path.join(ARTIFACT_ROOT, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

function buildCoverageSummary({ screenshots, consoleErrors, requestFailed }) {
  const screenshotCount = Object.keys(screenshots).filter((key) => ACCEPTANCE_COVERAGE.screenshotKeys.includes(key)).length;
  return {
    schema_version: "config_workbench_operation_acceptance_metrics.v1",
    journey_count: ACCEPTANCE_COVERAGE.journeys.length,
    journey_passed_count: ACCEPTANCE_COVERAGE.journeys.length,
    action_count: ACCEPTANCE_COVERAGE.actions.length,
    action_passed_count: ACCEPTANCE_COVERAGE.actions.length,
    assertion_count: ACCEPTANCE_COVERAGE.assertions.length,
    assertion_passed_count: ACCEPTANCE_COVERAGE.assertions.length,
    screenshot_required_count: ACCEPTANCE_COVERAGE.screenshotKeys.length,
    screenshot_captured_count: screenshotCount,
    browser_console_error_count: consoleErrors.length,
    browser_request_failed_count: requestFailed.length,
    coverage_ratio: 1,
    health_passed: consoleErrors.length === 0 && requestFailed.length === 0,
    journeys: ACCEPTANCE_COVERAGE.journeys,
    actions: ACCEPTANCE_COVERAGE.actions,
    assertions: ACCEPTANCE_COVERAGE.assertions,
  };
}

function buildFailureCoverageSummary({ screenshots, consoleErrors, requestFailed, failureMessage }) {
  const screenshotCount = Object.keys(screenshots).filter((key) => ACCEPTANCE_COVERAGE.screenshotKeys.includes(key)).length;
  return {
    schema_version: "config_workbench_operation_acceptance_metrics.v1",
    journey_count: ACCEPTANCE_COVERAGE.journeys.length,
    journey_passed_count: 0,
    action_count: ACCEPTANCE_COVERAGE.actions.length,
    action_passed_count: 0,
    assertion_count: ACCEPTANCE_COVERAGE.assertions.length,
    assertion_passed_count: 0,
    screenshot_required_count: ACCEPTANCE_COVERAGE.screenshotKeys.length,
    screenshot_captured_count: screenshotCount,
    browser_console_error_count: consoleErrors.length,
    browser_request_failed_count: requestFailed.length,
    coverage_ratio: 0,
    health_passed: false,
    failure_category: consoleErrors.length || requestFailed.length ? "browser_health" : "user_operation",
    failure_message: failureMessage,
    journeys: ACCEPTANCE_COVERAGE.journeys,
    actions: ACCEPTANCE_COVERAGE.actions,
    assertions: ACCEPTANCE_COVERAGE.assertions,
  };
}

async function main() {
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: "zh-CN" });
  const consoleErrors = [];
  const requestFailed = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 500));
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));
  page.on("requestfailed", (req) => {
    const failure = req.failure()?.errorText || "";
    if (!failure.includes("net::ERR_ABORTED")) {
      requestFailed.push(`${req.method()} ${req.url()} ${failure}`.slice(0, 500));
    }
  });

  const checks = {};
  const screenshots = {};
  try {
    await login(page);

    await page.goto(configWorkbenchUrl(), { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForLoadState("networkidle", { timeout: 25000 }).catch(() => {});
    await page.getByRole("button", { name: /选择业务页面/ }).first().click();
    await page.waitForSelector(".scan-panel", { timeout: 60000 });
    await page.getByPlaceholder("输入页面名称").fill("合同");
    await page.waitForTimeout(800);
    checks.scanRowsBeforeSelect = await page.locator(".scan-row").count();
    await page.locator(".scan-row").filter({ hasText: CONFIG_PAGE_LABEL }).first().getByRole("button", { name: /选择|当前配置/ }).click();
    await page.waitForSelector(".selected-page-overview", { timeout: 60000 });
    await page.waitForTimeout(800);
    checks.selectedText = await page.locator(".selected-page-overview").first().innerText();
    checks.cardsAfterSelect = await visibleCardTitles(page);
    checks.scanRowsAfterSelect = await page.locator(".scan-row").count();
    screenshots.selectedFromScan = await capture(page, "01-selected-from-scan");

    await page.getByPlaceholder("输入页面名称").fill(SWITCH_PAGE_LABEL);
    await page.waitForTimeout(500);
    checks.searchRows = await page.locator(".scan-row-main strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.locator(".scan-row").filter({ hasText: SWITCH_PAGE_LABEL }).first().getByRole("button", { name: "选择" }).click();
    await page.waitForFunction((label) => {
      const selected = document.querySelector(".scan-row--selected .scan-row-main strong");
      return selected?.textContent?.trim() === label;
    }, SWITCH_PAGE_LABEL, { timeout: 60000 });
    await page.waitForTimeout(800);
    checks.switchedTitle = await page.locator(".business-config-header h1").innerText();
    checks.cardsAfterSwitch = await visibleCardTitles(page);
    screenshots.switchedPage = await capture(page, "02-switched-page");

    await openDirectSelectedWorkbench(page);
    checks.directStartCards = await visibleCardTitles(page, '[data-lowcode-workbench-ia="start"]');
    checks.directDeliveryStatusCount = await page.locator('[data-lowcode-delivery-readiness="low_code_delivery_readiness.v1"]').count();
    screenshots.directSelected = await capture(page, "03-direct-selected");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "列表与搜索", "配置列表");
    const listSearchPanel = page.locator(".edit-panel").filter({ hasText: "列表与搜索设置" });
    await listSearchPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.listSearchTitle = await listSearchPanel.locator("h2").innerText();
    checks.listSearchTabs = await listSearchPanel.locator(".list-search-tabs button span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    checks.listSearchCanvasCount = await listSearchPanel.locator(".field-chip-editor").count();
    screenshots.listSearchEntry = await capture(page, "04-list-search-entry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "审批规则", "配置审批");
    const approvalPanel = page.locator(".approval-panel");
    await approvalPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.approvalTitle = await approvalPanel.locator("h2").innerText();
    checks.approvalRulePanelCount = await approvalPanel.locator(".approval-rule-panel").count();
    checks.approvalStepCanvasCount = await approvalPanel.locator(".approval-steps").count();
    screenshots.approvalEntry = await capture(page, "05-approval-entry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "表单字段与布局", "配置表单字段");
    await page.waitForURL((url) => String(url).includes(`/f/${CONFIG_MODEL}/new`), { timeout: 60000 });
    await page.waitForSelector(".contract-form-settings", { timeout: 60000 });
    checks.formDesignerTitle = await page.locator(".contract-form-settings h4").innerText();
    checks.formDesignerStepText = await page.locator(".contract-form-design-strip").innerText();
    checks.formDesignerReturnButtonCount = await page.getByRole("button", { name: /返回配置/ }).count();
    screenshots.formDesignerEntry = await capture(page, "06-form-designer-entry");
    await page.getByRole("button", { name: /返回配置/ }).first().click();
    await page.waitForURL((url) => String(url).includes("/admin/business-config"), { timeout: 60000 });
    await page.waitForSelector('[data-lowcode-config-task-card="v1"]', { timeout: 60000 });
    checks.formReturnedTitle = await page.locator(".business-config-header h1").innerText();

    await page.getByRole("button", { name: /配置菜单/ }).first().click();
    await page.waitForURL((url) => String(url).includes("/admin/menu-config"), { timeout: 60000 });
    await page.waitForSelector(".menu-config-page", { timeout: 60000 });
    await page.waitForFunction(() => document.querySelectorAll(".menu-config-tree .tree-scroll .tree-node").length > 0, null, { timeout: 60000 });
    checks.menuSideSections = await page.locator(".menu-side-action-group .menu-side-section-title").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    checks.menuTreeHead = await page.locator(".menu-config-tree .tree-panel-head").innerText();
    checks.menuTreeRows = await page.locator(".menu-config-tree .tree-scroll .tree-node").count();
    checks.menuSelectedPanelCount = await page.locator(".menu-selected-panel").count();
    screenshots.menuConfig = await capture(page, "07-menu-config");
    await page.getByRole("button", { name: "返回配置工作台" }).click();
    await page.waitForURL((url) => String(url).includes("/admin/business-config"), { timeout: 60000 });
    await page.waitForSelector('[data-lowcode-config-task-card="v1"]', { timeout: 60000 });
    checks.returnedTitle = await page.locator(".business-config-header h1").innerText();
    checks.returnedCards = await visibleCardTitles(page);

    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(configWorkbenchUrl(), { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForLoadState("networkidle", { timeout: 25000 }).catch(() => {});
    await page.getByRole("button", { name: /选择业务页面/ }).first().click();
    await page.waitForSelector(".scan-panel", { timeout: 60000 });
    await page.getByPlaceholder("输入页面名称").fill("合同");
    await page.waitForTimeout(800);
    await page.locator(".scan-row").filter({ hasText: CONFIG_PAGE_LABEL }).first().getByRole("button", { name: /选择|当前配置/ }).click();
    await page.waitForSelector(".page-config-panel [data-lowcode-config-task-card='v1']", { timeout: 60000 });
    await page.waitForTimeout(800);
    checks.mobileOrder = await page.evaluate(() => [".page-config-panel", ".page-picker-panel", ".workbench-status-rail"].map((selector) => {
      const el = document.querySelector(selector);
      const rect = el?.getBoundingClientRect();
      return { selector, top: rect ? rect.top : null, display: el ? getComputedStyle(el).display : null };
    }));
    checks.mobileBodyWidth = await page.evaluate(() => ({
      innerWidth: window.innerWidth,
      bodyScrollWidth: document.body.scrollWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
    }));
    screenshots.mobileSelected = await capture(page, "08-mobile-selected");

    assert(checks.scanRowsBeforeSelect >= 2 && checks.scanRowsAfterSelect >= 2, "业务页面列表选择后不应丢失", checks);
    assert(checks.selectedText.includes(CONFIG_PAGE_LABEL), "选择页面后未展示当前配置上下文", checks);
    assert(checks.cardsAfterSelect.includes("表单字段与布局") && checks.cardsAfterSelect.includes("列表与搜索"), "选择页面后配置卡片不完整", checks);
    assert(checks.searchRows.length === 1 && checks.searchRows[0] === SWITCH_PAGE_LABEL, "业务页面搜索结果不符合用户预期", checks);
    assert(checks.switchedTitle.includes(SWITCH_PAGE_LABEL), "切换页面后标题未同步", checks);
    assert(checks.cardsAfterSwitch.includes("表单字段与布局") && checks.cardsAfterSwitch.includes("列表与搜索"), "切换页面后配置卡片不完整", checks);
    assert(checks.directStartCards.includes("表单字段与布局") && checks.directDeliveryStatusCount === 1, "直达已选页面缺少配置任务或交付状态", checks);
    assert(
      checks.listSearchTitle === "列表与搜索设置"
      && checks.listSearchTabs.join("|") === "列表列|搜索条件|默认分组"
      && checks.listSearchCanvasCount === 1,
      "列表与搜索配置入口没有打开可操作编辑面板",
      checks,
    );
    assert(
      checks.approvalTitle === "审批规则"
      && checks.approvalRulePanelCount === 1
      && checks.approvalStepCanvasCount === 1,
      "审批配置入口没有打开规则配置画布",
      checks,
    );
    assert(
      checks.formDesignerTitle === "当前页面字段配置"
      && checks.formDesignerStepText.includes(CONFIG_PAGE_LABEL)
      && checks.formDesignerReturnButtonCount > 0
      && checks.formReturnedTitle.includes(CONFIG_PAGE_LABEL),
      "表单配置入口没有形成进入设计器并返回工作台闭环",
      checks,
    );
    assert(checks.menuSideSections.join("|") === "新增入口|批量维护|检查发布", "菜单配置侧栏操作分组不完整", checks);
    assert(checks.menuTreeRows > 0 && !checks.menuTreeHead.includes("0 个可配置菜单"), "从配置工作台进入菜单配置后菜单目录为空", checks);
    assert(checks.returnedTitle.includes(CONFIG_PAGE_LABEL) && checks.returnedCards.includes("菜单入口"), "菜单配置返回工作台后上下文丢失", checks);
    assert(
      checks.mobileOrder[0].top !== null && checks.mobileOrder[1].top !== null && checks.mobileOrder[0].top < checks.mobileOrder[1].top,
      "移动端选择页面后应先展示当前配置，再展示页面目录",
      checks,
    );
    assert(checks.mobileBodyWidth.documentScrollWidth <= checks.mobileBodyWidth.innerWidth + 8, "移动端出现横向溢出", checks);
    assert(consoleErrors.length === 0 && requestFailed.length === 0, "浏览器存在控制台错误或失败请求", { consoleErrors, requestFailed });

    const metrics = buildCoverageSummary({ screenshots, consoleErrors, requestFailed });
    const report = {
      ok: true,
      baseUrl: BASE_URL,
      dbName: DB_NAME,
      login: LOGIN,
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
    };
    await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(JSON.stringify({ ok: true, reportPath: REPORT_PATH, metrics, checks }, null, 2));
  } catch (err) {
    const failureMessage = err instanceof Error ? err.message : String(err);
    const metrics = buildFailureCoverageSummary({ screenshots, consoleErrors, requestFailed, failureMessage });
    const report = {
      ok: false,
      baseUrl: BASE_URL,
      dbName: DB_NAME,
      login: LOGIN,
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
      failure: {
        message: failureMessage,
        details: err?.details || {},
      },
    };
    await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
