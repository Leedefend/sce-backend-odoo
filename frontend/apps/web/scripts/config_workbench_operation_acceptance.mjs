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
    "delivery_status_default_user_task_only",
    "direct_delivery_status_default_user_task_only",
    "list_search_editor_visible",
    "list_search_tabs_complete",
    "list_search_editor_focused_after_entry",
    "approval_editor_visible",
    "approval_rule_canvas_visible",
    "approval_editor_focused_after_entry",
    "form_designer_visible",
    "form_designer_return_visible",
    "form_designer_business_actions_hidden",
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

async function visibleTechnicalTerms(page, scope = "body") {
  const text = await page.locator(scope).innerText({ timeout: 10000 }).catch(() => "");
  const patterns = [
    /construction\.[a-z0-9_.]+/gi,
    /ui\.[a-z0-9_.]+/gi,
    /\b(action_id|view_id|role_key|model=|root_menu_xmlid)\b/gi,
    /\b(user_confirmed_|technical_|synced_from_|generated_from_|migrated_from_|daily_dev)\w*/gi,
    /对象\s+[a-z0-9_.]+/gi,
    /页面\s*(ID|id)\s*[:：]?\s*\d+/g,
  ];
  return patterns
    .flatMap((pattern) => text.match(pattern) || [])
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .filter((item, index, items) => items.indexOf(item) === index);
}

async function deliveryReadinessLabels(page, scope) {
  return page.locator(`${scope} .delivery-readiness-item span`).evaluateAll((nodes) => (
    nodes.map((node) => node.textContent?.trim()).filter(Boolean)
  ));
}

function defaultDeliveryReadinessIsUserTaskOnly(labels = []) {
  const expected = ["表单配置", "列表与搜索配置", "菜单配置", "审批配置"];
  return labels.length === expected.length
    && expected.every((label) => labels.includes(label))
    && !labels.includes("版本与快照")
    && !labels.includes("覆盖检查");
}

async function viewportEvidence(locator) {
  return locator.evaluate((el) => {
    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
    return {
      top: Math.round(rect.top),
      bottom: Math.round(rect.bottom),
      height: Math.round(rect.height),
      viewportHeight,
      startsInPrimaryViewport: rect.top >= 0 && rect.top <= Math.min(420, viewportHeight * 0.55),
    };
  }).catch(() => ({
    top: null,
    bottom: null,
    height: null,
    viewportHeight: null,
    startsInPrimaryViewport: false,
  }));
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

function taskResult(pass, evidence, details = {}) {
  return {
    status: pass ? "pass" : "fail",
    evidence,
    details,
  };
}

function scoreResult(score, reason) {
  return { score, reason };
}

function buildPageStructureResult(checks) {
  const expectedCards = ["表单字段与布局", "列表与搜索", "菜单入口", "审批规则"];
  const desktop = checks.pageStructureDesktop || {};
  const directStart = checks.directStartStructure || {};
  const mobileOrder = checks.mobileOrder || [];
  const mobileBodyWidth = checks.mobileBodyWidth || {};
  const desktopSelectedPass = String(desktop.headerTitle || "").includes(CONFIG_PAGE_LABEL)
    && desktop.currentConfig?.count === 1
    && expectedCards.every((item) => desktop.currentConfig?.cardTitles?.includes(item))
    && desktop.pageDirectory?.count === 1
    && desktop.pageDirectory?.searchControlCount === 1
    && desktop.pageDirectory?.rowCount >= 2
    && desktop.deliveryStatus?.count === 1
    && desktop.crossZoneLeakage?.cardsInsideDirectory === 0
    && desktop.crossZoneLeakage?.directoryRowsInsideConfig === 0;
  const directStartPass = String(directStart.headerTitle || "").includes(CONFIG_PAGE_LABEL)
    && directStart.topContext?.count === 1
    && directStart.currentConfig?.count === 1
    && expectedCards.every((item) => directStart.currentConfig?.cardTitles?.includes(item))
    && directStart.deliveryStatus?.count === 1
    && directStart.pageDirectory?.count === 0;
  const mobilePass = mobileOrder[0]?.top !== null
    && mobileOrder[1]?.top !== null
    && mobileOrder[2]?.top !== null
    && mobileOrder[0]?.top < mobileOrder[1]?.top
    && mobileOrder[1]?.top < mobileOrder[2]?.top
    && mobileBodyWidth.documentScrollWidth <= mobileBodyWidth.innerWidth + 8;
  const failures = [];
  if (!desktopSelectedPass) failures.push("desktop_selected_structure_not_canonical");
  if (!directStartPass) failures.push("direct_start_structure_not_canonical");
  if (!mobilePass) failures.push("mobile_structure_order_or_width_invalid");
  return {
    schema_version: "config_workbench_page_structure.v1",
    status: failures.length ? "fail" : "pass",
    failures,
    desktop_selected: {
      standard: [
        "header_context",
        "current_config_panel",
        "page_directory_panel",
        "delivery_status_rail",
      ],
      result: desktop,
    },
    direct_selected_start: {
      standard: [
        "header_context",
        "top_context_actions",
        "current_config_panel",
        "delivery_status_panel",
      ],
      result: directStart,
    },
    mobile_selected: {
      standard_order: [
        "current_config_panel",
        "page_directory_panel",
        "delivery_status_rail",
      ],
      result: {
        order: mobileOrder,
        width: mobileBodyWidth,
      },
    },
  };
}

function buildProductUsability({ ok, metrics, checks, screenshots, consoleErrors, requestFailed }) {
  const screenshotReady = (key) => Boolean(screenshots[key]);
  const expectedCards = ["表单字段与布局", "列表与搜索", "菜单入口", "审批规则"];
  const pageStructure = buildPageStructureResult(checks);
  const cardsComplete = expectedCards.every((item) => checks.cardsAfterSelect?.includes(item))
    && expectedCards.every((item) => checks.directStartCards?.includes(item));
  const pageContextVisible = String(checks.selectedText || "").includes(CONFIG_PAGE_LABEL)
    && String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL)
    && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL);
  const entryNamesStable = checks.cardsAfterSelect?.join("|") === checks.directStartCards?.join("|")
    && checks.formDesignerReturnButtonCount > 0;
  const listSearchUsable = checks.listSearchTitle === "列表与搜索设置"
    && checks.listSearchTabs?.join("|") === "列表列|搜索条件|默认分组"
    && checks.listSearchCanvasCount === 1;
  const approvalUsable = checks.approvalTitle === "审批规则"
    && checks.approvalRulePanelCount === 1
    && checks.approvalStepCanvasCount === 1;
  const formUsable = checks.formDesignerTitle === "当前页面字段配置"
    && String(checks.formDesignerStepText || "").includes(CONFIG_PAGE_LABEL)
    && checks.formDesignerReturnButtonCount > 0;
  const editorFocusReady = checks.listSearchPanelViewport?.startsInPrimaryViewport === true
    && checks.approvalPanelViewport?.startsInPrimaryViewport === true;
  const formDesignerActionHygieneReady = (checks.formDesignerBusinessActionButtons || []).length === 0;
  const menuUsable = checks.menuSideSections?.join("|") === "新增入口|批量维护|检查发布"
    && checks.menuTreeRows > 0
    && !String(checks.menuTreeHead || "").includes("0 个可配置菜单");
  const mobileStable = checks.mobileOrder?.[0]?.top !== null
    && checks.mobileOrder?.[1]?.top !== null
    && checks.mobileOrder?.[2]?.top !== null
    && checks.mobileOrder?.[0]?.top < checks.mobileOrder?.[1]?.top
    && checks.mobileOrder?.[1]?.top < checks.mobileOrder?.[2]?.top
    && checks.mobileBodyWidth?.documentScrollWidth <= checks.mobileBodyWidth?.innerWidth + 8;
  const browserHealthy = consoleErrors.length === 0 && requestFailed.length === 0 && metrics?.health_passed === true;
  const defaultDeliveryStatusFocused = defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels)
    && defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels);
  const visibleTechnicalTermsClean = [
    ...(checks.selectedVisibleTechnicalTerms || []),
    ...(checks.directStartVisibleTechnicalTerms || []),
    ...(checks.formDesignerVisibleTechnicalTerms || []),
    ...(checks.menuConfigVisibleTechnicalTerms || []),
  ].length === 0;
  const evidenceReady = ACCEPTANCE_COVERAGE.screenshotKeys.every(screenshotReady)
    && metrics?.coverage_ratio === 1;
  const searchUsable = checks.searchRows?.length === 1
    && checks.searchRows[0] === SWITCH_PAGE_LABEL
    && String(checks.switchedTitle || "").includes(SWITCH_PAGE_LABEL);

  const taskResults = {
    find_business_page: taskResult(
      checks.scanRowsBeforeSelect >= 2 && checks.scanRowsAfterSelect >= 2 && searchUsable,
      ["selectedFromScan", "switchedPage"],
      { scanRowsBeforeSelect: checks.scanRowsBeforeSelect, scanRowsAfterSelect: checks.scanRowsAfterSelect, searchRows: checks.searchRows },
    ),
    understand_config_scope: taskResult(
      pageContextVisible && cardsComplete,
      ["selectedFromScan", "directSelected"],
      { cardsAfterSelect: checks.cardsAfterSelect, directStartCards: checks.directStartCards },
    ),
    configure_form_fields: taskResult(
      formUsable && formDesignerActionHygieneReady && String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL),
      ["formDesignerEntry"],
      { formDesignerTitle: checks.formDesignerTitle, formReturnedTitle: checks.formReturnedTitle, formDesignerBusinessActionButtons: checks.formDesignerBusinessActionButtons },
    ),
    configure_list_search: taskResult(
      listSearchUsable && checks.listSearchPanelViewport?.startsInPrimaryViewport === true,
      ["listSearchEntry"],
      { listSearchTitle: checks.listSearchTitle, listSearchTabs: checks.listSearchTabs, listSearchPanelViewport: checks.listSearchPanelViewport },
    ),
    configure_approval_rules: taskResult(
      approvalUsable && checks.approvalPanelViewport?.startsInPrimaryViewport === true,
      ["approvalEntry"],
      { approvalTitle: checks.approvalTitle, approvalRulePanelCount: checks.approvalRulePanelCount, approvalPanelViewport: checks.approvalPanelViewport },
    ),
    configure_menu_entry: taskResult(
      menuUsable,
      ["menuConfig"],
      { menuSideSections: checks.menuSideSections, menuTreeHead: checks.menuTreeHead, menuTreeRows: checks.menuTreeRows },
    ),
    return_to_workbench: taskResult(
      String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL)
      && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL)
      && checks.returnedCards?.includes("菜单入口"),
      ["formDesignerEntry", "menuConfig"],
      { formReturnedTitle: checks.formReturnedTitle, returnedTitle: checks.returnedTitle },
    ),
    mobile_operation: taskResult(
      mobileStable,
      ["mobileSelected"],
      { mobileOrder: checks.mobileOrder, mobileBodyWidth: checks.mobileBodyWidth },
    ),
  };

  const dimensions = {
    current_context: scoreResult(pageContextVisible ? 2 : 0, "标题、卡片和返回路径必须指向当前业务页面。"),
    page_structure: scoreResult(pageStructure.status === "pass" ? 2 : 0, "页面必须符合配置工作台结构合同。"),
    information_architecture: scoreResult(cardsComplete && checks.directDeliveryStatusCount === 1 && pageStructure.status === "pass" && defaultDeliveryStatusFocused ? 2 : 0, "配置任务、页面目录和交付状态必须层级清晰，默认只展示用户任务状态。"),
    operation_convention: scoreResult(searchUsable && formUsable && listSearchUsable && approvalUsable && menuUsable && editorFocusReady && formDesignerActionHygieneReady ? 2 : 0, "搜索、选择、配置、返回必须符合常见后台产品习惯。"),
    entry_naming: scoreResult(entryNamesStable ? 2 : 0, "同一能力的入口命名必须稳定且使用业务语言。"),
    task_efficiency: scoreResult(formUsable && listSearchUsable && approvalUsable && menuUsable && editorFocusReady ? 2 : 0, "关键配置任务必须能从卡片主入口直接进入并进入当前编辑焦点。"),
    status_feedback: scoreResult(metrics?.journey_passed_count === ACCEPTANCE_COVERAGE.journeys.length ? 2 : 0, "加载、禁用、返回和健康状态必须可被报告证明。"),
    error_recovery: scoreResult(String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL) && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL) ? 2 : 0, "从子能力返回必须保留业务页面上下文。"),
    visual_stability: scoreResult(mobileStable && pageStructure.status === "pass" ? 2 : 0, "桌面和 390px 移动端不得遮挡或横向溢出。"),
    user_language: scoreResult(cardsComplete && entryNamesStable && visibleTechnicalTermsClean ? 2 : 0, "默认界面必须使用业务语言，不要求用户理解技术模型。"),
    verifiability: scoreResult(evidenceReady ? 2 : 0, "结论必须可由截图、指标和报告文件复现。"),
  };
  const scoreTotal = Object.values(dimensions).reduce((sum, item) => sum + item.score, 0);
  const maxScore = Object.keys(dimensions).length * 2;
  const zeroScoreDimensions = Object.entries(dimensions).filter(([, item]) => item.score === 0).map(([key]) => key);

  const blockingIssues = [];
  if (!ok) blockingIssues.push("operation_gate_failed");
  if (!pageContextVisible) blockingIssues.push("current_business_page_context_unclear");
  if (!cardsComplete) blockingIssues.push("config_task_cards_incomplete");
  if (!entryNamesStable) blockingIssues.push("capability_entry_naming_inconsistent");
  if (!formUsable || !listSearchUsable || !approvalUsable || !menuUsable) blockingIssues.push("capability_entry_not_product_usable");
  if (!defaultDeliveryStatusFocused) blockingIssues.push("delivery_status_default_noise_leaked");
  if (!editorFocusReady) blockingIssues.push("config_editor_not_focused_after_entry");
  if (!formDesignerActionHygieneReady) blockingIssues.push("form_designer_business_actions_leaked");
  if (pageStructure.status !== "pass") blockingIssues.push("page_structure_contract_failed");
  if (!visibleTechnicalTermsClean) blockingIssues.push("visible_technical_terms_leaked");
  if (!mobileStable) blockingIssues.push("mobile_layout_not_stable");
  if (!browserHealthy) blockingIssues.push("browser_health_failed");
  if (!evidenceReady) blockingIssues.push("acceptance_evidence_incomplete");

  const riskItems = [];
  if (scoreTotal < maxScore) riskItems.push("product_usability_score_not_full");
  if (zeroScoreDimensions.length) riskItems.push(`zero_score_dimensions:${zeroScoreDimensions.join(",")}`);

  return {
    schema_version: "config_workbench_product_usability.v1",
    delivery_status: blockingIssues.length ? "delivery_blocked" : (scoreTotal >= 20 && !zeroScoreDimensions.length ? "delivery_ready" : "delivery_risk"),
    score_total: scoreTotal,
    score_required: 20,
    max_score: maxScore,
    dimensions,
    page_structure: pageStructure,
    blocking_issues: blockingIssues,
    risk_items: riskItems,
    task_results: taskResults,
    evidence: {
      report_path: REPORT_PATH,
      command: "DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 make verify.business_config.config_workbench_operation_acceptance",
      screenshots,
    },
  };
}

function professionalScore(pass, reason, evidence = {}) {
  return {
    score: pass ? 3 : 0,
    reason,
    evidence,
  };
}

function buildProfessionalReadiness({ metrics, checks, screenshots, consoleErrors, requestFailed, productUsability }) {
  const screenshotsComplete = ACCEPTANCE_COVERAGE.screenshotKeys.every((key) => Boolean(screenshots[key]));
  const taskStatuses = Object.values(productUsability.task_results || {}).map((item) => item.status);
  const allTasksPassed = taskStatuses.length === 8 && taskStatuses.every((status) => status === "pass");
  const pageStructurePassed = productUsability.page_structure?.status === "pass";
  const healthPassed = consoleErrors.length === 0
    && requestFailed.length === 0
    && metrics?.health_passed === true;
  const cards = checks.cardsAfterSelect || [];
  const directCards = checks.directStartCards || [];
  const cardsStable = cards.length === 4 && cards.join("|") === directCards.join("|");
  const visibleTechnicalTerms = [
    ...(checks.selectedVisibleTechnicalTerms || []),
    ...(checks.directStartVisibleTechnicalTerms || []),
    ...(checks.formDesignerVisibleTechnicalTerms || []),
    ...(checks.menuConfigVisibleTechnicalTerms || []),
  ];
  const menuBoundaryStable = checks.menuSideSections?.join("|") === "新增入口|批量维护|检查发布"
    && checks.menuTreeRows > 0
    && !String(checks.menuTreeHead || "").includes("0 个可配置菜单")
    && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL);
  const workflowClosure = String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL)
    && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL)
    && checks.returnedCards?.includes("菜单入口");
  const responsiveProof = checks.mobileBodyWidth?.documentScrollWidth <= checks.mobileBodyWidth?.innerWidth + 8
    && productUsability.page_structure?.mobile_selected?.result?.order?.length === 3;
  const cognitiveLoadControlled = pageStructurePassed
    && cardsStable
    && checks.pageStructureDesktop?.pageDirectory?.rowCount >= 2
    && checks.pageStructureDesktop?.pageDirectory?.searchControlCount === 1
    && checks.pageStructureDesktop?.pageDirectory?.filterControlCount >= 3
    && defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels)
    && defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels);
  const capabilityDepthReady = checks.formDesignerTitle === "当前页面字段配置"
    && checks.listSearchTabs?.join("|") === "列表列|搜索条件|默认分组"
    && checks.approvalRulePanelCount === 1
    && checks.approvalStepCanvasCount === 1
    && checks.menuSelectedPanelCount === 1;
  const editorFocusReady = checks.listSearchPanelViewport?.startsInPrimaryViewport === true
    && checks.approvalPanelViewport?.startsInPrimaryViewport === true;
  const actionSemanticsReady = (checks.formDesignerBusinessActionButtons || []).length === 0;
  const releaseRepeatable = metrics?.coverage_ratio === 1
    && metrics?.journey_passed_count === ACCEPTANCE_COVERAGE.journeys.length
    && metrics?.assertion_passed_count === ACCEPTANCE_COVERAGE.assertions.length
    && productUsability.delivery_status === "delivery_ready"
    && productUsability.blocking_issues?.length === 0
    && productUsability.risk_items?.length === 0;

  const dimensions = {
    user_task_closure: professionalScore(allTasksPassed, "专业产品必须覆盖并通过关键用户任务闭环。", { taskStatuses }),
    page_structure_contract: professionalScore(pageStructurePassed, "专业产品必须有稳定页面结构合同。", productUsability.page_structure),
    cognitive_load_control: professionalScore(cognitiveLoadControlled, "专业产品必须降低扫描成本，目录、任务和状态职责清楚。", {
      cards,
      rowCount: checks.pageStructureDesktop?.pageDirectory?.rowCount,
      searchControlCount: checks.pageStructureDesktop?.pageDirectory?.searchControlCount,
      filterControlCount: checks.pageStructureDesktop?.pageDirectory?.filterControlCount,
      deliveryReadinessLabels: checks.deliveryReadinessLabels,
      directDeliveryReadinessLabels: checks.directDeliveryReadinessLabels,
    }),
    naming_and_language_consistency: professionalScore(cardsStable && !visibleTechnicalTerms.length, "专业产品必须全链路名称稳定并默认使用业务语言。", { cards, directCards, visibleTechnicalTerms }),
    capability_depth: professionalScore(capabilityDepthReady && editorFocusReady && actionSemanticsReady, "专业产品不能只到入口，表单、列表搜索、审批、菜单必须进入可操作配置面，并且进入后焦点和动作语义清楚。", {
      formDesignerTitle: checks.formDesignerTitle,
      listSearchTabs: checks.listSearchTabs,
      approvalRulePanelCount: checks.approvalRulePanelCount,
      approvalStepCanvasCount: checks.approvalStepCanvasCount,
      menuSelectedPanelCount: checks.menuSelectedPanelCount,
      listSearchPanelViewport: checks.listSearchPanelViewport,
      approvalPanelViewport: checks.approvalPanelViewport,
      formDesignerBusinessActionButtons: checks.formDesignerBusinessActionButtons,
    }),
    workflow_recovery: professionalScore(workflowClosure, "专业产品必须从子能力返回原工作台上下文。", {
      formReturnedTitle: checks.formReturnedTitle,
      returnedTitle: checks.returnedTitle,
      returnedCards: checks.returnedCards,
    }),
    responsive_resilience: professionalScore(responsiveProof, "专业产品必须在 390px 移动端保持顺序和宽度稳定。", {
      mobileOrder: checks.mobileOrder,
      mobileBodyWidth: checks.mobileBodyWidth,
    }),
    boundary_integrity: professionalScore(menuBoundaryStable, "专业产品必须保持菜单配置能力边界和业务返回上下文不混淆。", {
      menuSideSections: checks.menuSideSections,
      menuTreeHead: checks.menuTreeHead,
      returnedTitle: checks.returnedTitle,
    }),
    operational_health: professionalScore(healthPassed, "专业产品必须无浏览器错误和失败请求。", { consoleErrors, requestFailed }),
    evidence_and_repeatability: professionalScore(screenshotsComplete && releaseRepeatable, "专业产品验收必须可由命令、报告、截图重复证明。", {
      screenshotsComplete,
      coverageRatio: metrics?.coverage_ratio,
      journeyPassed: metrics?.journey_passed_count,
      assertionPassed: metrics?.assertion_passed_count,
    }),
  };
  const scoreTotal = Object.values(dimensions).reduce((sum, item) => sum + item.score, 0);
  const maxScore = Object.keys(dimensions).length * 3;
  const failedDimensions = Object.entries(dimensions).filter(([, item]) => item.score === 0).map(([key]) => key);
  const blockers = [];
  if (productUsability.delivery_status !== "delivery_ready") blockers.push("product_usability_not_delivery_ready");
  failedDimensions.forEach((key) => blockers.push(`professional_dimension_failed:${key}`));
  return {
    schema_version: "config_workbench_professional_readiness.v1",
    status: blockers.length ? "professional_blocked" : "professional_ready",
    score_total: scoreTotal,
    score_required: maxScore,
    max_score: maxScore,
    dimensions,
    blockers,
    evidence: {
      report_path: REPORT_PATH,
      command: "DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 make verify.business_config.config_workbench_operation_acceptance",
      screenshots,
    },
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
    checks.selectedVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".scan-panel");
    checks.deliveryReadinessLabels = await deliveryReadinessLabels(page, ".workbench-status-rail");
    checks.pageStructureDesktop = await page.evaluate(() => {
      const rectInfo = (selector) => {
        const el = document.querySelector(selector);
        const rect = el?.getBoundingClientRect();
        return {
          count: document.querySelectorAll(selector).length,
          top: rect ? rect.top : null,
          left: rect ? rect.left : null,
          width: rect ? rect.width : null,
          height: rect ? rect.height : null,
          display: el ? getComputedStyle(el).display : null,
        };
      };
      return {
        headerTitle: document.querySelector(".business-config-header h1")?.textContent?.trim() || "",
        currentConfig: {
          ...rectInfo(".page-config-panel"),
          overviewCount: document.querySelectorAll(".page-config-panel .selected-page-overview").length,
          cardTitles: Array.from(document.querySelectorAll(".page-config-panel [data-lowcode-config-task-card='v1'] h2"))
            .map((node) => node.textContent?.trim())
            .filter(Boolean),
        },
        pageDirectory: {
          ...rectInfo(".page-picker-panel"),
          searchControlCount: document.querySelectorAll(".scan-toolbar input[placeholder*='页面名称'], .scan-toolbar input[type='search']").length,
          filterControlCount: document.querySelectorAll(".scan-toolbar .page-type-tabs button").length,
          rowCount: document.querySelectorAll(".page-picker-panel .scan-row").length,
        },
        deliveryStatus: {
          ...rectInfo(".workbench-status-rail"),
          readinessCount: document.querySelectorAll(".workbench-status-rail [data-lowcode-delivery-readiness], .workbench-status-rail").length,
        },
        crossZoneLeakage: {
          cardsInsideDirectory: document.querySelectorAll(".page-picker-panel [data-lowcode-config-task-card='v1']").length,
          directoryRowsInsideConfig: document.querySelectorAll(".page-config-panel .scan-row").length,
        },
      };
    });
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
    checks.directDeliveryReadinessLabels = await deliveryReadinessLabels(page, ".workbench-start-status");
    checks.directStartVisibleTechnicalTerms = await visibleTechnicalTerms(page, "[data-lowcode-workbench-ia='start']");
    checks.directStartStructure = await page.evaluate(() => {
      const rectInfo = (selector) => {
        const el = document.querySelector(selector);
        const rect = el?.getBoundingClientRect();
        return {
          count: document.querySelectorAll(selector).length,
          top: rect ? rect.top : null,
          left: rect ? rect.left : null,
          width: rect ? rect.width : null,
          height: rect ? rect.height : null,
          display: el ? getComputedStyle(el).display : null,
        };
      };
      return {
        headerTitle: document.querySelector(".business-config-header h1")?.textContent?.trim() || "",
        topContext: {
          ...rectInfo(".workbench-start-lead"),
          actionCount: document.querySelectorAll(".workbench-start-lead button").length,
        },
        currentConfig: {
          ...rectInfo(".workbench-start-config"),
          cardTitles: Array.from(document.querySelectorAll("[data-lowcode-workbench-ia='start'] [data-lowcode-config-task-card='v1'] h2"))
            .map((node) => node.textContent?.trim())
            .filter(Boolean),
        },
        pageDirectory: rectInfo(".page-picker-panel"),
        deliveryStatus: rectInfo(".workbench-start-status"),
      };
    });
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
    checks.listSearchPanelViewport = await viewportEvidence(listSearchPanel);
    screenshots.listSearchEntry = await capture(page, "04-list-search-entry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "审批规则", "配置审批");
    const approvalPanel = page.locator(".approval-panel");
    await approvalPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.approvalTitle = await approvalPanel.locator("h2").innerText();
    checks.approvalRulePanelCount = await approvalPanel.locator(".approval-rule-panel").count();
    checks.approvalStepCanvasCount = await approvalPanel.locator(".approval-steps").count();
    checks.approvalPanelViewport = await viewportEvidence(approvalPanel);
    screenshots.approvalEntry = await capture(page, "05-approval-entry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "表单字段与布局", "配置表单字段");
    await page.waitForURL((url) => String(url).includes(`/f/${CONFIG_MODEL}/new`), { timeout: 60000 });
    await page.waitForSelector(".contract-form-settings", { timeout: 60000 });
    checks.formDesignerTitle = await page.locator(".contract-form-settings h4").innerText();
    checks.formDesignerStepText = await page.locator(".contract-form-design-strip").innerText();
    checks.formDesignerReturnButtonCount = await page.getByRole("button", { name: /返回配置/ }).count();
    checks.formDesignerVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".contract-form-settings");
    checks.formDesignerBusinessActionButtons = await page.locator("button").evaluateAll((buttons) => (
      buttons
        .map((button) => button.textContent?.trim())
        .filter((text) => text === "保存草稿" || text === "提交")
    ));
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
    checks.menuConfigVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".menu-config-page");
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
    assert(defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels), "默认交付状态不应展示内部审计指标", checks);
    assert(defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels), "直达态默认交付状态不应展示内部审计指标", checks);
    assert(
      checks.listSearchTitle === "列表与搜索设置"
      && checks.listSearchTabs.join("|") === "列表列|搜索条件|默认分组"
      && checks.listSearchCanvasCount === 1,
      "列表与搜索配置入口没有打开可操作编辑面板",
      checks,
    );
    assert(checks.listSearchPanelViewport.startsInPrimaryViewport === true, "列表与搜索配置入口打开后没有进入当前编辑焦点", checks);
    assert(
      checks.approvalTitle === "审批规则"
      && checks.approvalRulePanelCount === 1
      && checks.approvalStepCanvasCount === 1,
      "审批配置入口没有打开规则配置画布",
      checks,
    );
    assert(checks.approvalPanelViewport.startsInPrimaryViewport === true, "审批配置入口打开后没有进入当前编辑焦点", checks);
    assert(
      checks.formDesignerTitle === "当前页面字段配置"
      && checks.formDesignerStepText.includes(CONFIG_PAGE_LABEL)
      && checks.formDesignerReturnButtonCount > 0
      && checks.formReturnedTitle.includes(CONFIG_PAGE_LABEL),
      "表单配置入口没有形成进入设计器并返回工作台闭环",
      checks,
    );
    assert(checks.formDesignerBusinessActionButtons.length === 0, "表单配置态不应出现业务办理动作按钮", checks);
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
    const productUsability = buildProductUsability({
      ok: true,
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
    });
    const professionalReadiness = buildProfessionalReadiness({
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
      productUsability,
    });
    assert(
      productUsability.delivery_status === "delivery_ready",
      "配置工作台尚未达到交付级产品化验收标准",
      { productUsability },
    );
    assert(
      professionalReadiness.status === "professional_ready",
      "配置工作台尚未达到专业产品水准验收标准",
      { professionalReadiness },
    );

    const report = {
      ok: true,
      baseUrl: BASE_URL,
      dbName: DB_NAME,
      login: LOGIN,
      metrics,
      product_usability: productUsability,
      professional_readiness: professionalReadiness,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
    };
    await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(JSON.stringify({ ok: true, reportPath: REPORT_PATH, metrics, product_usability: productUsability, professional_readiness: professionalReadiness, checks }, null, 2));
  } catch (err) {
    const failureMessage = err instanceof Error ? err.message : String(err);
    const metrics = buildFailureCoverageSummary({ screenshots, consoleErrors, requestFailed, failureMessage });
    const productUsability = err?.details?.productUsability || buildProductUsability({
      ok: false,
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
    });
    const professionalReadiness = err?.details?.professionalReadiness || buildProfessionalReadiness({
      metrics,
      checks,
      screenshots,
      consoleErrors,
      requestFailed,
      productUsability,
    });
    const report = {
      ok: false,
      baseUrl: BASE_URL,
      dbName: DB_NAME,
      login: LOGIN,
      metrics,
      product_usability: productUsability,
      professional_readiness: professionalReadiness,
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
