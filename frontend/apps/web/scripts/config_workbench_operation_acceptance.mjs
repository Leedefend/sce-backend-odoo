import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { CONFIG_WORKBENCH_OPERATION_COVERAGE as ACCEPTANCE_COVERAGE } from "./lib/config_workbench_operation_coverage.mjs";
import { readProductPageRegionClasses } from "./lib/product_page_structure_source.mjs";

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
const SUMMARY_PATH = path.join(ARTIFACT_ROOT, "summary.json");
const VERBOSE_OUTPUT = ["1", "true", "yes"].includes(String(process.env.CONFIG_WORKBENCH_ACCEPTANCE_VERBOSE || "").toLowerCase());
const PRODUCT_PAGE_REGION_CLASSES = readProductPageRegionClasses();
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

async function visibleCardPrimaryActions(page, scope = "") {
  return page.locator(`${scope} [data-lowcode-config-task-card="v1"]`).evaluateAll((cards) => (
    cards.map((card) => {
      const title = card.querySelector("h2")?.textContent?.trim() || "";
      const actions = Array.from(card.querySelectorAll("button"))
        .map((button) => button.textContent?.trim())
        .filter(Boolean);
      return { title, actions };
    })
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

async function capture(page, key, options = {}) {
  const fileName = ACCEPTANCE_COVERAGE.screenshotFiles[key];
  assert(fileName, "未知截图证据 key", { key });
  const filePath = path.join(ARTIFACT_ROOT, fileName);
  await page.screenshot({ path: filePath, fullPage: options.fullPage !== false });
  return filePath;
}

async function prepareArtifactRoot() {
  const normalized = path.normalize(ARTIFACT_ROOT);
  if (!normalized.endsWith(path.normalize("artifacts/playwright/config-workbench-operation"))) {
    throw new Error(`Refuse to clean unexpected artifact directory: ${ARTIFACT_ROOT}`);
  }
  await fs.rm(ARTIFACT_ROOT, { recursive: true, force: true });
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
}

async function listArtifactEvidenceFiles() {
  const files = await fs.readdir(ARTIFACT_ROOT).catch(() => []);
  return files.filter((item) => item.endsWith(".png") || item === "report.json").sort();
}

function expectedArtifactPngFiles() {
  return ACCEPTANCE_COVERAGE.screenshotKeys.map((key) => ACCEPTANCE_COVERAGE.screenshotFiles[key]);
}

async function visibleTechnicalTerms(page, scope = "body") {
  const text = await page.locator(scope).innerText({ timeout: 10000 }).catch(() => "");
  const patterns = [
    /construction\.[a-z0-9_.]+/gi,
    /ui\.[a-z0-9_.]+/gi,
    /\b(action_id|view_id|role_key|model=|root_menu_xmlid)\b/gi,
    /\b(user_confirmed_|technical_|synced_from_|generated_from_|migrated_from_|daily_dev)\w*/gi,
    /\b[a-z][a-z0-9]*_[a-z0-9_]+\b/gi,
    /\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+\b/g,
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
      startsInEditorFocusViewport: rect.top >= 0 && rect.top <= Math.min(180, viewportHeight * 0.24),
    };
  }).catch(() => ({
    top: null,
    bottom: null,
    height: null,
    viewportHeight: null,
    startsInPrimaryViewport: false,
    startsInEditorFocusViewport: false,
  }));
}

async function productWorkspaceGapEvidence(page, items = []) {
  return page.evaluate((selectors) => {
    const parsePx = (value) => {
      const parsed = Number(String(value || "").replace("px", ""));
      return Number.isFinite(parsed) ? parsed : null;
    };
    return selectors.map((item) => {
      const el = document.querySelector(item.selector);
      if (!el) return { ...item, ready: false, columnGapPx: null, rowGapPx: null, display: "" };
      const style = getComputedStyle(el);
      return {
        ...item,
        ready: true,
        display: style.display,
        columnGapPx: parsePx(style.columnGap),
        rowGapPx: parsePx(style.rowGap),
        className: el.className || "",
      };
    });
  }, items);
}

async function productPageRegionAlignmentEvidence(page, items = []) {
  return page.evaluate((configs) => {
    const rectFor = (selector) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return null;
      return {
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        top: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        className: el.className || "",
      };
    };
    return configs.map((item) => {
      const anchor = rectFor(item.anchor);
      const regions = (item.regions || []).map((region) => {
        const rect = rectFor(region.selector);
        if (!anchor || !rect) {
          return {
            ...region,
            ready: Boolean(region.optional && anchor),
            optionalMissing: Boolean(region.optional && !rect),
            leftDelta: null,
            rightDelta: null,
            rect,
          };
        }
        return {
          ...region,
          ready: true,
          leftDelta: Math.round(Math.abs(anchor.left - rect.left)),
          rightDelta: Math.round(Math.abs(anchor.right - rect.right)),
          rect,
        };
      });
      return {
        page: item.page,
        scope: item.scope,
        anchor: item.anchor,
        anchorReady: Boolean(anchor),
        anchorRect: anchor,
        regions,
        ready: Boolean(anchor) && regions.length > 0 && regions.every((region) => region.ready),
        maxDelta: Math.max(0, ...regions
          .filter((region) => region.ready && region.leftDelta !== null && region.rightDelta !== null)
          .flatMap((region) => [region.leftDelta, region.rightDelta])),
      };
    });
  }, items);
}

async function productPageRuntimeSemanticEvidence(page, items = []) {
  return page.evaluate((configs) => configs.map((item) => {
    const checks = (item.checks || []).map((check) => {
      const el = document.querySelector(check.selector);
      const className = el?.className || "";
      const mode = el?.getAttribute("data-product-page-mode") || "";
      const requiredClasses = check.classes || [];
      return {
        ...check,
        ready: Boolean(el),
        className,
        mode,
        classPass: requiredClasses.every((classNamePart) => String(className).split(/\s+/).includes(classNamePart)),
        modePass: check.mode ? mode === check.mode : true,
      };
    });
    return {
      page: item.page,
      scope: item.scope,
      checks,
      ready: checks.length > 0 && checks.every((check) => check.ready && check.classPass && check.modePass),
    };
  }), items);
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

function buildTerminalSummary(report) {
  const metrics = report.metrics || {};
  const productUsability = report.product_usability || {};
  const professionalReadiness = report.professional_readiness || {};
  const checks = report.checks || {};
  return {
    ok: report.ok === true,
    reportPath: REPORT_PATH,
    summaryPath: SUMMARY_PATH,
    assertion: `${metrics.assertion_passed_count || 0}/${metrics.assertion_count || 0}`,
    journeys: `${metrics.journey_passed_count || 0}/${metrics.journey_count || 0}`,
    actions: `${metrics.action_passed_count || 0}/${metrics.action_count || 0}`,
    screenshots: `${metrics.screenshot_captured_count || 0}/${metrics.screenshot_required_count || 0}`,
    delivery: productUsability.delivery_status || "unknown",
    professional: professionalReadiness.status || "unknown",
    consoleErrors: metrics.browser_console_error_count ?? 0,
    requestFailed: metrics.browser_request_failed_count ?? 0,
    currentPage: checks.pageStructureDesktop?.currentConfig?.overviewLabel || "",
    formDesignerCurrentPageLabel: checks.formDesignerCurrentPageLabel || "",
    menuTreeHead: checks.menuTreeHead || "",
    failure: report.failure?.message || metrics.failure_message || "",
  };
}

async function writeReportAndSummary(report) {
  const summary = buildTerminalSummary(report);
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  await fs.writeFile(SUMMARY_PATH, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
  return summary;
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

function assertCoverageKeys(actualObject, expectedKeys, message) {
  const actualKeys = Object.keys(actualObject || {});
  const missing = expectedKeys.filter((key) => !actualKeys.includes(key));
  const extra = actualKeys.filter((key) => !expectedKeys.includes(key));
  const orderMismatch = expectedKeys
    .map((key, index) => ({ index, actual: actualKeys[index], expected: key }))
    .filter((item) => item.actual !== item.expected);
  assert(
    missing.length === 0 && extra.length === 0 && orderMismatch.length === 0 && actualKeys.length === expectedKeys.length,
    message,
    { actualKeys, expectedKeys, missing, extra, orderMismatch },
  );
}

function buildPageStructureResult(checks) {
  const expectedCards = ["表单字段与布局", "列表与搜索", "菜单入口", "审批规则"];
  const desktop = checks.pageStructureDesktop || {};
  const directStart = checks.directStartStructure || {};
  const mobileOrder = checks.mobileOrder || [];
  const mobileBodyWidth = checks.mobileBodyWidth || {};
  const mobileViewport = checks.mobileViewport || {};
  const desktopSelectedPass = String(desktop.headerTitle || "").includes(CONFIG_PAGE_LABEL)
    && desktop.currentConfig?.count === 1
    && desktop.currentConfig?.overviewLabel === CONFIG_PAGE_LABEL
    && desktop.currentConfig?.overviewLabelTruncated === false
    && expectedCards.every((item) => desktop.currentConfig?.cardTitles?.includes(item))
    && desktop.pageDirectory?.count === 1
    && desktop.pageDirectory?.searchControlCount === 1
    && desktop.pageDirectory?.rowCount >= 2
    && desktop.deliveryStatus?.count === 1
    && desktop.crossZoneLeakage?.cardsInsideDirectory === 0
    && desktop.crossZoneLeakage?.directoryRowsInsideConfig === 0;
  const directStartPass = String(directStart.headerTitle || "").includes(CONFIG_PAGE_LABEL)
    && directStart.topContext?.count === 1
    && directStart.topContext?.overviewLabel === CONFIG_PAGE_LABEL
    && directStart.topContext?.overviewLabelTruncated === false
    && directStart.topContext?.actionCount <= 2
    && directStart.currentConfig?.count === 1
    && expectedCards.every((item) => directStart.currentConfig?.cardTitles?.includes(item))
    && directStart.deliveryStatus?.count === 1
    && directStart.pageDirectory?.count === 0;
  const mobilePass = mobileOrder[0]?.top !== null
    && mobileOrder[1]?.top !== null
    && mobileOrder[2]?.top !== null
    && mobileOrder[0]?.top >= 0
    && mobileOrder[0]?.top <= 220
    && mobileViewport.currentConfigVisibleInPrimaryViewport === true
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
        viewport: mobileViewport,
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
    && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL)
    && checks.pageStructureDesktop?.currentConfig?.overviewLabel === CONFIG_PAGE_LABEL
    && checks.pageStructureDesktop?.currentConfig?.overviewLabelTruncated === false
    && checks.directStartStructure?.topContext?.overviewLabel === CONFIG_PAGE_LABEL
    && checks.directStartStructure?.topContext?.overviewLabelTruncated === false;
  const entryNamesStable = checks.cardsAfterSelect?.join("|") === checks.directStartCards?.join("|")
    && checks.formDesignerReturnButtonCount > 0;
  const listSearchUsable = checks.listSearchTitle === "列表与搜索设置"
    && checks.listSearchTabs?.join("|") === "列表列|搜索条件|默认分组"
    && checks.listSearchCanvasCount === 1
    && checks.listSearchActionHintText?.includes("上移")
    && checks.listSearchActionAriaCount >= 3
    && checks.listSearchReturnWorkbenchButtonCount > 0;
  const approvalUsable = checks.approvalTitle === "审批规则"
    && checks.approvalRulePanelCount === 1
    && checks.approvalStepCanvasCount === 1
    && checks.approvalStepMoveButtonCount > 0
    && checks.approvalStepActionHintText?.includes("上移")
    && checks.approvalStepActionAriaCount >= 3
    && checks.approvalReturnWorkbenchButtonCount > 0;
  const formUsable = checks.formDesignerTitle === "当前页面字段配置"
    && String(checks.formDesignerStepText || "").includes(CONFIG_PAGE_LABEL)
    && checks.formDesignerCurrentPageLabel === CONFIG_PAGE_LABEL
    && checks.formDesignerFieldSearchInputCount > 0
    && checks.formDesignerFieldSearchResultCount > 0
    && checks.formDesignerReturnButtonCount > 0
    && String(checks.formDesignerShellTitle || "").includes(CONFIG_PAGE_LABEL);
  const editorFocusReady = checks.listSearchPanelViewport?.startsInPrimaryViewport === true
    && checks.approvalPanelViewport?.startsInPrimaryViewport === true
    && checks.listSearchPanelViewport?.startsInEditorFocusViewport === true
    && checks.approvalPanelViewport?.startsInEditorFocusViewport === true;
  const formDesignerActionHygieneReady = (checks.formDesignerBusinessActionButtons || []).length === 0;
  const menuUsable = checks.menuSideSections?.join("|") === "新增入口|批量维护|检查发布"
    && checks.menuTreeRows > 0
    && !String(checks.menuTreeHead || "").includes("0 个可配置菜单");
  const mobileStable = checks.mobileOrder?.[0]?.top !== null
    && checks.mobileOrder?.[1]?.top !== null
    && checks.mobileOrder?.[2]?.top !== null
    && checks.mobileOrder?.[0]?.top >= 0
    && checks.mobileOrder?.[0]?.top <= 220
    && checks.mobileViewport?.currentConfigVisibleInPrimaryViewport === true
    && checks.mobileOrder?.[0]?.top < checks.mobileOrder?.[1]?.top
    && checks.mobileOrder?.[1]?.top < checks.mobileOrder?.[2]?.top
    && checks.mobileBodyWidth?.documentScrollWidth <= checks.mobileBodyWidth?.innerWidth + 8
    && checks.mobileConfigurationTopbar?.platformEyebrowVisible === false;
  const browserHealthy = consoleErrors.length === 0 && requestFailed.length === 0 && metrics?.health_passed === true;
  const productRegionAlignmentReady = (checks.productPageRegionAlignment || []).length >= 4
    && (checks.productPageRegionAlignment || []).every((item) => item.ready === true && item.maxDelta <= 1);
  const productRuntimeSemanticsReady = (checks.productPageRuntimeSemantics || []).length >= 4
    && (checks.productPageRuntimeSemantics || []).every((item) => item.ready === true);
  const defaultDeliveryStatusFocused = defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels)
    && defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels)
    && checks.defaultSnapshotSummaryCount === 0
    && checks.mobileSnapshotSummaryCount === 0;
  const visibleTechnicalTermsClean = [
    ...(checks.selectedVisibleTechnicalTerms || []),
    ...(checks.directStartVisibleTechnicalTerms || []),
    ...(checks.listSearchVisibleTechnicalTerms || []),
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
      { formDesignerTitle: checks.formDesignerTitle, formDesignerShellTitle: checks.formDesignerShellTitle, formReturnedTitle: checks.formReturnedTitle, formDesignerBusinessActionButtons: checks.formDesignerBusinessActionButtons },
    ),
    configure_list_search: taskResult(
      listSearchUsable && checks.listSearchPanelViewport?.startsInPrimaryViewport === true,
      ["listSearchEntry"],
      { listSearchTitle: checks.listSearchTitle, listSearchTabs: checks.listSearchTabs, listSearchPanelViewport: checks.listSearchPanelViewport, listSearchReturnWorkbenchButtonCount: checks.listSearchReturnWorkbenchButtonCount },
    ),
    configure_approval_rules: taskResult(
      approvalUsable && checks.approvalPanelViewport?.startsInPrimaryViewport === true,
      ["approvalEntry"],
      { approvalTitle: checks.approvalTitle, approvalRulePanelCount: checks.approvalRulePanelCount, approvalPanelViewport: checks.approvalPanelViewport, approvalReturnWorkbenchButtonCount: checks.approvalReturnWorkbenchButtonCount },
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
      { mobileOrder: checks.mobileOrder, mobileViewport: checks.mobileViewport, mobileBodyWidth: checks.mobileBodyWidth, mobileConfigurationTopbar: checks.mobileConfigurationTopbar },
    ),
  };
  assertCoverageKeys(
    taskResults,
    ACCEPTANCE_COVERAGE.productUsabilityTasks,
    "配置工作台用户任务验收结果必须与共享 coverage 完全一致",
  );

  const dimensions = {
    current_context: scoreResult(pageContextVisible ? 2 : 0, "标题、卡片和返回路径必须指向当前业务页面。"),
    page_structure: scoreResult(pageStructure.status === "pass" ? 2 : 0, "页面必须符合配置工作台结构合同。"),
    information_architecture: scoreResult(cardsComplete && checks.directDeliveryStatusCount === 1 && pageStructure.status === "pass" && defaultDeliveryStatusFocused ? 2 : 0, "配置任务、页面目录和交付状态必须层级清晰，默认只展示用户任务状态。"),
    operation_convention: scoreResult(searchUsable && formUsable && listSearchUsable && approvalUsable && menuUsable && editorFocusReady && formDesignerActionHygieneReady ? 2 : 0, "搜索、选择、配置、返回必须符合常见后台产品习惯。"),
    entry_naming: scoreResult(entryNamesStable ? 2 : 0, "同一能力的入口命名必须稳定且使用业务语言。"),
    task_efficiency: scoreResult(formUsable && listSearchUsable && approvalUsable && menuUsable && editorFocusReady ? 2 : 0, "关键配置任务必须能从卡片主入口直接进入并进入当前编辑焦点。"),
    status_feedback: scoreResult(metrics?.journey_passed_count === ACCEPTANCE_COVERAGE.journeys.length ? 2 : 0, "加载、禁用、返回和健康状态必须可被报告证明。"),
    error_recovery: scoreResult(String(checks.formReturnedTitle || "").includes(CONFIG_PAGE_LABEL) && String(checks.returnedTitle || "").includes(CONFIG_PAGE_LABEL) ? 2 : 0, "从子能力返回必须保留业务页面上下文。"),
    visual_stability: scoreResult(mobileStable && pageStructure.status === "pass" && productRegionAlignmentReady && productRuntimeSemanticsReady ? 2 : 0, "桌面区域外边界必须对齐，运行时区域语义必须存在，390px 移动端不得遮挡或横向溢出。"),
    user_language: scoreResult(cardsComplete && entryNamesStable && visibleTechnicalTermsClean ? 2 : 0, "默认界面必须使用业务语言，不要求用户理解技术模型。"),
    verifiability: scoreResult(evidenceReady ? 2 : 0, "结论必须可由截图、指标和报告文件复现。"),
  };
  assertCoverageKeys(
    dimensions,
    ACCEPTANCE_COVERAGE.productUsabilityDimensions,
    "配置工作台交付维度必须与共享 coverage 完全一致",
  );
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
  if (!productRegionAlignmentReady) blockingIssues.push("product_page_region_alignment_failed");
  if (!productRuntimeSemanticsReady) blockingIssues.push("product_page_runtime_semantics_missing");
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
    score_required: maxScore,
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
  const allTasksPassed = taskStatuses.length === ACCEPTANCE_COVERAGE.productUsabilityTasks.length
    && taskStatuses.every((status) => status === "pass");
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
    ...(checks.listSearchVisibleTechnicalTerms || []),
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
    && productUsability.page_structure?.mobile_selected?.result?.order?.length === 3
    && checks.mobileConfigurationTopbar?.platformEyebrowVisible === false;
  const productRegionAlignmentReady = (checks.productPageRegionAlignment || []).length >= 4
    && (checks.productPageRegionAlignment || []).every((item) => item.ready === true && item.maxDelta <= 1);
  const productRuntimeSemanticsReady = (checks.productPageRuntimeSemantics || []).length >= 4
    && (checks.productPageRuntimeSemantics || []).every((item) => item.ready === true);
  const cognitiveLoadControlled = pageStructurePassed
    && cardsStable
    && checks.pageStructureDesktop?.pageDirectory?.rowCount >= 2
    && checks.pageStructureDesktop?.pageDirectory?.searchControlCount === 1
    && checks.pageStructureDesktop?.pageDirectory?.filterControlCount >= 3
    && defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels)
    && defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels);
  const capabilityDepthReady = checks.formDesignerTitle === "当前页面字段配置"
    && checks.formDesignerCurrentPageLabel === CONFIG_PAGE_LABEL
    && checks.formDesignerFieldSearchInputCount > 0
    && checks.formDesignerFieldSearchResultCount > 0
    && checks.listSearchTabs?.join("|") === "列表列|搜索条件|默认分组"
    && checks.listSearchReturnWorkbenchButtonCount > 0
    && checks.listSearchActionHintText?.includes("上移")
    && checks.listSearchActionAriaCount >= 3
    && checks.approvalRulePanelCount === 1
    && checks.approvalStepCanvasCount === 1
    && checks.approvalStepMoveButtonCount > 0
    && checks.approvalStepActionHintText?.includes("上移")
    && checks.approvalStepActionAriaCount >= 3
    && checks.approvalReturnWorkbenchButtonCount > 0
    && checks.menuSelectedPanelCount === 1
    && checks.menuSearchInputCount > 0
    && checks.menuSearchClearButtonCount > 0;
  const editorFocusReady = checks.listSearchPanelViewport?.startsInPrimaryViewport === true
    && checks.approvalPanelViewport?.startsInPrimaryViewport === true
    && checks.listSearchPanelViewport?.startsInEditorFocusViewport === true
    && checks.approvalPanelViewport?.startsInEditorFocusViewport === true;
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
      formDesignerShellTitle: checks.formDesignerShellTitle,
      formDesignerCurrentPageLabel: checks.formDesignerCurrentPageLabel,
      formDesignerFieldSearchInputCount: checks.formDesignerFieldSearchInputCount,
      formDesignerFieldSearchResultCount: checks.formDesignerFieldSearchResultCount,
      listSearchTabs: checks.listSearchTabs,
      listSearchReturnWorkbenchButtonCount: checks.listSearchReturnWorkbenchButtonCount,
      listSearchActionHintText: checks.listSearchActionHintText,
      listSearchActionAriaCount: checks.listSearchActionAriaCount,
      approvalRulePanelCount: checks.approvalRulePanelCount,
      approvalStepCanvasCount: checks.approvalStepCanvasCount,
      approvalStepMoveButtonCount: checks.approvalStepMoveButtonCount,
      approvalStepActionHintText: checks.approvalStepActionHintText,
      approvalStepActionAriaCount: checks.approvalStepActionAriaCount,
      approvalReturnWorkbenchButtonCount: checks.approvalReturnWorkbenchButtonCount,
      menuSelectedPanelCount: checks.menuSelectedPanelCount,
      menuSearchInputCount: checks.menuSearchInputCount,
      menuSearchSummaryText: checks.menuSearchSummaryText,
      menuSearchClearButtonCount: checks.menuSearchClearButtonCount,
      listSearchPanelViewport: checks.listSearchPanelViewport,
      approvalPanelViewport: checks.approvalPanelViewport,
      formDesignerBusinessActionButtons: checks.formDesignerBusinessActionButtons,
    }),
    workflow_recovery: professionalScore(workflowClosure, "专业产品必须从子能力返回原工作台上下文。", {
      formReturnedTitle: checks.formReturnedTitle,
      returnedTitle: checks.returnedTitle,
      returnedCards: checks.returnedCards,
    }),
    responsive_resilience: professionalScore(responsiveProof && productRegionAlignmentReady && productRuntimeSemanticsReady, "专业产品必须在桌面保持页面区域外边界对齐，运行时语义可审计，并在 390px 移动端保持顺序和宽度稳定。", {
      mobileOrder: checks.mobileOrder,
      mobileViewport: checks.mobileViewport,
      mobileBodyWidth: checks.mobileBodyWidth,
      mobileConfigurationTopbar: checks.mobileConfigurationTopbar,
      productPageRegionAlignment: checks.productPageRegionAlignment,
      productPageRuntimeSemantics: checks.productPageRuntimeSemantics,
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
  assertCoverageKeys(
    dimensions,
    ACCEPTANCE_COVERAGE.professionalDimensions,
    "配置工作台专业产品维度必须与共享 coverage 完全一致",
  );
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
  await prepareArtifactRoot();
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
    checks.cardPrimaryActionsAfterSelect = await visibleCardPrimaryActions(page);
    checks.scanRowsAfterSelect = await page.locator(".scan-row").count();
    checks.selectedVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".scan-panel");
    checks.deliveryReadinessLabels = await deliveryReadinessLabels(page, ".workbench-status-rail");
    checks.defaultSnapshotSummaryCount = await page.locator(".workbench-status-rail .workbench-status-snapshot").count();
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
      const labelInfo = (selector) => {
        const el = document.querySelector(selector);
        return {
          overviewLabel: el?.textContent?.trim() || "",
          overviewLabelTruncated: el ? el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1 : true,
        };
      };
      return {
        headerTitle: document.querySelector(".business-config-header h1")?.textContent?.trim() || "",
        currentConfig: {
          ...rectInfo(".page-config-panel"),
          ...labelInfo(".page-config-panel .selected-page-overview strong"),
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
    screenshots.selectedFromScan = await capture(page, "selectedFromScan");

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
    checks.switchedCurrentLabelLayout = await page.locator(".page-config-panel .selected-page-overview strong").evaluate((node) => {
      const rects = Array.from(node.getClientRects()).filter((rect) => rect.width > 0 && rect.height > 0);
      return {
        text: node.textContent?.trim() || "",
        lineCount: rects.length,
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
      };
    });
    checks.cardsAfterSwitch = await visibleCardTitles(page);
    screenshots.switchedPage = await capture(page, "switchedPage");

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
      const labelInfo = (selector) => {
        const el = document.querySelector(selector);
        return {
          overviewLabel: el?.textContent?.trim() || "",
          overviewLabelTruncated: el ? el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1 : true,
        };
      };
      return {
        headerTitle: document.querySelector(".business-config-header h1")?.textContent?.trim() || "",
        topContext: {
          ...rectInfo(".workbench-start-lead"),
          ...labelInfo(".workbench-start-lead strong"),
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
    checks.productWorkspaceGaps = await productWorkspaceGapEvidence(page, [
      { page: "business_config", selector: ".workbench-start", scope: "direct_two_column_workbench" },
    ]);
    checks.productPageRegionAlignment = await productPageRegionAlignmentEvidence(page, [
      {
        page: "business_config",
        scope: "direct_selected_start",
        anchor: ".business-config-header",
        regions: [
          { selector: "[data-lowcode-workbench-ia='start']", name: "start_surface" },
        ],
      },
    ]);
    checks.productPageRuntimeSemantics = await productPageRuntimeSemanticEvidence(page, [
      {
        page: "business_config",
        scope: "direct_selected_start",
        checks: [
          { selector: ".business-config-page", name: "page_shell", classes: ["sc-page"], mode: "admin" },
          { selector: ".business-config-header", name: "page_header", classes: [PRODUCT_PAGE_REGION_CLASSES.pageHeader] },
          { selector: "[data-lowcode-workbench-ia='start']", name: "main_surface", classes: [PRODUCT_PAGE_REGION_CLASSES.mainSurface] },
        ],
      },
    ]);
    screenshots.directSelected = await capture(page, "directSelected");

    await page.goto(`${BASE_URL}/a/${CONFIG_ACTION_ID}?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector(".page .list-toolbar, .page .list-empty-state", { timeout: 60000 });
    checks.businessRuntimeWorkspaceGaps = await productWorkspaceGapEvidence(page, [
      { page: "business_runtime", selector: ".page", scope: "list_page_stack" },
    ]);
    checks.productPageRegionAlignment.push(...await productPageRegionAlignmentEvidence(page, [
      {
        page: "business_runtime",
        scope: "list_page_regions",
        anchor: ".page .list-toolbar",
        regions: [
          { selector: ".page .table, .page .list-empty-state", name: "list_main_surface" },
        ],
      },
    ]));
    checks.productPageRuntimeSemantics.push(...await productPageRuntimeSemanticEvidence(page, [
      {
        page: "business_runtime",
        scope: "list_page_regions",
        checks: [
          { selector: ".page", name: "page_shell", classes: ["sc-page", "sc-product-workspace-stack"], mode: "list" },
          { selector: ".page .list-toolbar", name: "page_toolbar", classes: [PRODUCT_PAGE_REGION_CLASSES.pageToolbar] },
          { selector: ".page .table, .page .list-empty-state", name: "main_surface", classes: [PRODUCT_PAGE_REGION_CLASSES.mainSurface] },
        ],
      },
    ]));
    checks.businessRuntimeListPageClass = await page.locator(".page").first().evaluate((node) => node.className || "");
    checks.businessRuntimeListToolbarCount = await page.locator(".page .list-toolbar").count();
    await page.goto(`${BASE_URL}/f/${encodeURIComponent(CONFIG_MODEL)}/new?db=${encodeURIComponent(DB_NAME)}&action_id=${CONFIG_ACTION_ID}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector(".card .form-grid", { timeout: 60000 });
    checks.businessRuntimeWorkspaceGaps.push(...await productWorkspaceGapEvidence(page, [
      { page: "business_runtime", selector: ".card", scope: "form_panel_shell" },
    ]));
    checks.productPageRegionAlignment.push(...await productPageRegionAlignmentEvidence(page, [
      {
        page: "business_runtime",
        scope: "form_page_regions",
        anchor: ".template-page-header",
        regions: [
          { selector: ".card", name: "form_main_surface" },
        ],
      },
    ]));
    checks.productPageRuntimeSemantics.push(...await productPageRuntimeSemanticEvidence(page, [
      {
        page: "business_runtime",
        scope: "form_page_regions",
        checks: [
          { selector: "[data-product-page-mode='form']", name: "page_shell", classes: ["sc-page"], mode: "form" },
          { selector: ".template-page-header", name: "page_header", classes: [PRODUCT_PAGE_REGION_CLASSES.pageHeader] },
          { selector: ".card", name: "main_surface", classes: [PRODUCT_PAGE_REGION_CLASSES.mainSurface] },
        ],
      },
    ]));
    checks.businessRuntimeFormShellClass = await page.locator(".card").first().evaluate((node) => node.className || "");
    checks.businessRuntimeFormBusinessActionButtons = await page.locator("button").evaluateAll((buttons) => (
      buttons
        .map((button) => button.textContent?.trim())
        .filter((text) => text === "保存草稿" || text === "提交")
    ));

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "表单字段与布局", "版本记录");
    const versionPanel = page.locator(".version-panel");
    await versionPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.versionPanelTitle = await versionPanel.locator("h2").innerText();
    checks.versionPanelCloseButtonCount = await versionPanel.getByRole("button", { name: "收起版本记录" }).count();
    checks.versionPanelLegacyCloseButtonCount = await versionPanel.getByRole("button", { name: "关闭" }).count();
    checks.versionPanelActionLabels = await versionPanel.locator("button").evaluateAll((buttons) => (
      buttons.map((button) => button.textContent?.trim()).filter(Boolean)
    ));

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "列表与搜索", "配置列表与搜索");
    const listSearchPanel = page.locator(".edit-panel").filter({ hasText: "列表与搜索设置" });
    await listSearchPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.listSearchTitle = await listSearchPanel.locator("h2").innerText();
    checks.listSearchTabs = await listSearchPanel.locator(".list-search-tabs button span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    checks.listSearchTabsPosition = await listSearchPanel.locator(".list-search-tabs").evaluate((node) => getComputedStyle(node).position);
    checks.listSearchCanvasCount = await listSearchPanel.locator(".field-chip-editor").count();
    checks.listSearchPanelViewport = await viewportEvidence(listSearchPanel);
    checks.productWorkspaceGaps.push(...await productWorkspaceGapEvidence(page, [
      { page: "business_config", selector: ".edit-panel.config-editor-panel", scope: "list_search_inline_editor" },
    ]));
    checks.listSearchReturnWorkbenchButtonCount = await listSearchPanel.getByRole("button", { name: "返回工作台" }).count();
    checks.listSearchSaveButtonCount = await listSearchPanel.getByRole("button", { name: "保存列表与搜索" }).count();
    checks.listSearchLegacySaveButtonCount = await listSearchPanel.getByRole("button", { name: "保存设置" }).count();
    checks.listSearchActionHintText = await listSearchPanel.locator(".field-chip-action-hint").first().innerText();
    checks.listSearchActionAriaCount = await listSearchPanel.locator(".field-chip button[aria-label^='上移'], .field-chip button[aria-label^='下移'], .field-chip button[aria-label^='移除']").count();
    await listSearchPanel.locator(".edit-meta").scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    checks.listSearchFooterOverlapEvidence = await page.evaluate(() => {
      const panel = document.querySelector(".edit-panel.config-editor-panel");
      const tabs = panel?.querySelector(".list-search-tabs");
      const meta = panel?.querySelector(".edit-meta");
      if (!panel || !tabs || !meta) return { ready: false, blockedByTabs: true };
      const metaRect = meta.getBoundingClientRect();
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const x = Math.min(Math.max(metaRect.left + 32, 24), viewportWidth - 24);
      const y = Math.min(Math.max(metaRect.top + Math.min(16, metaRect.height / 2), 24), viewportHeight - 24);
      const topElement = document.elementFromPoint(x, y);
      return {
        ready: true,
        blockedByTabs: Boolean(topElement && tabs.contains(topElement)),
        sample: { x: Math.round(x), y: Math.round(y) },
        metaRect: {
          top: Math.round(metaRect.top),
          left: Math.round(metaRect.left),
          right: Math.round(metaRect.right),
          bottom: Math.round(metaRect.bottom),
        },
        topElementClass: topElement instanceof HTMLElement ? topElement.className : "",
      };
    });
    checks.listSearchVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".edit-panel");
    screenshots.listSearchEntry = await capture(page, "listSearchEntry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "审批规则", "配置审批规则");
    const approvalPanel = page.locator(".approval-panel");
    await approvalPanel.waitFor({ state: "visible", timeout: 60000 });
    checks.approvalTitle = await approvalPanel.locator("h2").innerText();
    checks.approvalRulePanelCount = await approvalPanel.locator(".approval-rule-panel").count();
    checks.approvalRulePanelPosition = await approvalPanel.locator(".approval-rule-panel").evaluate((node) => getComputedStyle(node).position);
    checks.approvalStepCanvasCount = await approvalPanel.locator(".approval-steps").count();
    checks.approvalPanelViewport = await viewportEvidence(approvalPanel);
    checks.approvalStepMoveButtonCount = await approvalPanel.locator(".approval-step-actions button[title='上移'], .approval-step-actions button[title='下移']").count();
    checks.approvalStepActionHintText = await approvalPanel.locator(".approval-step-action-hint").innerText();
    checks.approvalStepActionAriaCount = await approvalPanel.locator(".approval-step-actions button[aria-label^='上移第'], .approval-step-actions button[aria-label^='下移第'], .approval-step-actions button[aria-label^='移除第']").count();
    checks.approvalReturnWorkbenchButtonCount = await approvalPanel.getByRole("button", { name: "返回工作台" }).count();
    checks.approvalFullRuleButtonCount = await approvalPanel.getByRole("button", { name: "打开完整规则" }).count();
    checks.approvalLegacyMoreRuleButtonCount = await approvalPanel.getByRole("button", { name: "更多规则" }).count();
    checks.approvalDiscardButtonCount = await approvalPanel.getByRole("button", { name: "放弃调整" }).count();
    checks.approvalLegacyRestoreButtonCount = await approvalPanel.getByRole("button", { name: "还原" }).count();
    await approvalPanel.locator(".edit-panel-actions").scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    checks.approvalFooterOverlapEvidence = await page.evaluate(() => {
      const panel = document.querySelector(".approval-panel");
      const rulePanel = panel?.querySelector(".approval-rule-panel");
      const actions = panel?.querySelector(".edit-panel-actions");
      if (!panel || !rulePanel || !actions) return { ready: false, blockedByRulePanel: true };
      const actionsRect = actions.getBoundingClientRect();
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const x = Math.min(Math.max(actionsRect.left + 32, 24), viewportWidth - 24);
      const y = Math.min(Math.max(actionsRect.top + Math.min(18, actionsRect.height / 2), 24), viewportHeight - 24);
      const topElement = document.elementFromPoint(x, y);
      return {
        ready: true,
        blockedByRulePanel: Boolean(topElement && rulePanel.contains(topElement)),
        sample: { x: Math.round(x), y: Math.round(y) },
        actionsRect: {
          top: Math.round(actionsRect.top),
          left: Math.round(actionsRect.left),
          right: Math.round(actionsRect.right),
          bottom: Math.round(actionsRect.bottom),
        },
        topElementClass: topElement instanceof HTMLElement ? topElement.className : "",
      };
    });
    screenshots.approvalEntry = await capture(page, "approvalEntry");

    await openDirectSelectedWorkbench(page);
    await clickConfigCardButton(page, "表单字段与布局", "配置表单与布局");
    await page.waitForURL((url) => String(url).includes(`/f/${CONFIG_MODEL}/new`), { timeout: 60000 });
    await page.waitForSelector(".contract-form-settings", { timeout: 60000 });
    checks.formDesignerTitle = await page.locator(".contract-form-settings h4").innerText();
    checks.formDesignerShellTitle = await page.locator(".topbar .headline").innerText().catch(() => "");
    checks.formDesignerStepText = await page.locator(".contract-form-design-strip").innerText();
    checks.formDesignerCurrentPageLabel = await page.locator(".contract-form-design-strip strong").first().innerText();
    checks.formDesignerFieldSearchInputCount = await page.locator(".contract-form-field-search input").count();
    checks.formDesignerFieldSearchResultCount = await page.locator(".contract-form-field-search-item").count();
    checks.formDesignerReturnButtonCount = await page.getByRole("button", { name: "返回工作台" }).count();
    checks.formDesignerLegacyReturnButtonCount = await page.getByRole("button", { name: "返回配置" }).count();
    checks.formDesignerDiscardButtonCount = await page.getByRole("button", { name: "放弃调整" }).count();
    checks.formDesignerLegacyResetButtonCount = await page.getByRole("button", { name: "重置" }).count();
    checks.formDesignerVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".contract-form-settings");
    checks.formDesignerBusinessActionButtons = await page.locator("button").evaluateAll((buttons) => (
      buttons
        .map((button) => button.textContent?.trim())
        .filter((text) => text === "保存草稿" || text === "提交")
    ));
    checks.productWorkspaceGaps.push(...await productWorkspaceGapEvidence(page, [
      { page: "form_designer", selector: ".form-grid--designer-workspace", scope: "designer_three_column" },
      { page: "form_designer", selector: ".contract-form-designer-control-grid", scope: "designer_center_control_grid" },
    ]));
    await page.locator(".contract-field-central-create").click();
    await page.locator(".contract-field-create-dialog").waitFor({ state: "visible", timeout: 60000 });
    checks.formFieldCreateDialogTitle = await page.locator("#contract-field-create-title").innerText();
    checks.formFieldCreateCloseLabelCount = await page.locator(".contract-field-create-close[aria-label='取消新增字段']").count();
    checks.formFieldCreateLegacyCloseLabelCount = await page.locator(".contract-field-create-close[aria-label='关闭']").count();
    await page.getByRole("button", { name: "取消新增字段" }).click();
    await page.locator(".contract-field-create-dialog").waitFor({ state: "hidden", timeout: 60000 });
    screenshots.formDesignerEntry = await capture(page, "formDesignerEntry");
    await page.locator(".contract-field-governance-footer").scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    checks.formDesignerFooterOverlapEvidence = await page.evaluate(() => {
      const footer = document.querySelector(".contract-field-governance-footer");
      const sidebar = document.querySelector(".contract-form-designer-sidebar");
      const inspector = document.querySelector(".contract-form-inspector");
      if (!footer || !sidebar || !inspector) return { ready: false, blockedBySidePanels: true };
      const footerRect = footer.getBoundingClientRect();
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const y = Math.min(Math.max(footerRect.top + Math.min(28, footerRect.height / 2), 24), viewportHeight - 24);
      const leftX = Math.min(Math.max(footerRect.left + 32, 24), viewportWidth - 24);
      const rightX = Math.min(Math.max(footerRect.right - 32, 24), viewportWidth - 24);
      const leftElement = document.elementFromPoint(leftX, y);
      const rightElement = document.elementFromPoint(rightX, y);
      const leftBlocked = Boolean(leftElement && sidebar.contains(leftElement));
      const rightBlocked = Boolean(rightElement && inspector.contains(rightElement));
      return {
        ready: true,
        blockedBySidePanels: leftBlocked || rightBlocked,
        samples: {
          left: { x: Math.round(leftX), y: Math.round(y), blocked: leftBlocked },
          right: { x: Math.round(rightX), y: Math.round(y), blocked: rightBlocked },
        },
        footerRect: {
          top: Math.round(footerRect.top),
          left: Math.round(footerRect.left),
          right: Math.round(footerRect.right),
          bottom: Math.round(footerRect.bottom),
        },
        leftElementClass: leftElement instanceof HTMLElement ? leftElement.className : "",
        rightElementClass: rightElement instanceof HTMLElement ? rightElement.className : "",
      };
    });
    await page.getByRole("button", { name: "返回工作台" }).first().click();
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
    checks.menuWorkspaceAlignment = await page.evaluate(() => {
      const header = document.querySelector(".menu-config-header");
      const workspace = document.querySelector(".menu-config-workspace");
      const headerRect = header?.getBoundingClientRect();
      const workspaceRect = workspace?.getBoundingClientRect();
      if (!headerRect || !workspaceRect) return { ready: false, leftDelta: null, rightDelta: null };
      const panelSelectors = [".menu-config-workspace", ".status", ".guide-panel", ".audit-panel", ".version-panel", ".create-panel"];
      const panels = panelSelectors
        .flatMap((selector) => Array.from(document.querySelectorAll(selector)).map((node) => ({ selector, node })))
        .filter(({ node }) => {
          const rect = node.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        })
        .map(({ selector, node }) => {
          const rect = node.getBoundingClientRect();
          return {
            selector,
            left: Math.round(rect.left),
            right: Math.round(rect.right),
            width: Math.round(rect.width),
            leftDelta: Math.round(Math.abs(headerRect.left - rect.left)),
            rightDelta: Math.round(Math.abs(headerRect.right - rect.right)),
          };
        });
      return {
        ready: true,
        header: {
          left: Math.round(headerRect.left),
          right: Math.round(headerRect.right),
          width: Math.round(headerRect.width),
        },
        workspace: {
          left: Math.round(workspaceRect.left),
          right: Math.round(workspaceRect.right),
          width: Math.round(workspaceRect.width),
        },
        leftDelta: Math.round(Math.abs(headerRect.left - workspaceRect.left)),
        rightDelta: Math.round(Math.abs(headerRect.right - workspaceRect.right)),
        panels,
        maxPanelDelta: Math.max(0, ...panels.flatMap((item) => [item.leftDelta, item.rightDelta])),
      };
    });
    checks.productPageRegionAlignment.push(...await productPageRegionAlignmentEvidence(page, [
      {
        page: "menu_config",
        scope: "menu_page_regions",
        anchor: ".menu-config-header",
        regions: [
          { selector: ".menu-config-workspace", name: "menu_main_surface" },
          { selector: ".guide-panel", name: "menu_guide_feedback", optional: true },
          { selector: ".audit-panel", name: "menu_audit_feedback", optional: true },
        ],
      },
    ]));
    checks.productPageRuntimeSemantics.push(...await productPageRuntimeSemanticEvidence(page, [
      {
        page: "menu_config",
        scope: "menu_page_regions",
        checks: [
          { selector: ".menu-config-page", name: "page_shell", classes: ["sc-page"], mode: "admin" },
          { selector: ".menu-config-header", name: "page_header", classes: [PRODUCT_PAGE_REGION_CLASSES.pageHeader] },
          { selector: ".menu-config-workspace", name: "main_surface", classes: [PRODUCT_PAGE_REGION_CLASSES.mainSurface] },
        ],
      },
    ]));
    checks.productWorkspaceGaps.push(...await productWorkspaceGapEvidence(page, [
      { page: "menu_config", selector: ".menu-config-workspace", scope: "menu_two_column_workspace" },
      { page: "menu_config", selector: ".menu-config-editor", scope: "menu_editor_columns" },
    ]));
    checks.menuSearchInputCount = await page.locator(".menu-config-tree .tree-search input").count();
    checks.menuSearchSummaryText = await page.locator(".menu-config-tree .tree-search-summary span").innerText();
    checks.menuSearchClearButtonCount = await page.locator(".menu-config-tree .tree-clear-filter").count();
    checks.menuSelectedPanelCount = await page.locator(".menu-selected-panel").count();
    checks.menuSaveButtonCount = await page.getByRole("button", { name: "保存菜单配置" }).count();
    checks.menuLegacySaveButtonCount = await page.getByRole("button", { name: "保存修改" }).count();
    await page.getByRole("button", { name: "新增一级菜单" }).click();
    const menuCreatePanel = page.locator(".create-panel");
    await menuCreatePanel.waitFor({ state: "visible", timeout: 60000 });
    checks.menuWorkspaceAlignmentAfterCreateOpen = await page.evaluate(() => {
      const header = document.querySelector(".menu-config-header");
      const headerRect = header?.getBoundingClientRect();
      if (!headerRect) return { ready: false, maxPanelDelta: null, panels: [] };
      const panelSelectors = [".menu-config-workspace", ".status", ".guide-panel", ".audit-panel", ".version-panel", ".create-panel"];
      const panels = panelSelectors
        .flatMap((selector) => Array.from(document.querySelectorAll(selector)).map((node) => ({ selector, node })))
        .filter(({ node }) => {
          const rect = node.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        })
        .map(({ selector, node }) => {
          const rect = node.getBoundingClientRect();
          return {
            selector,
            left: Math.round(rect.left),
            right: Math.round(rect.right),
            width: Math.round(rect.width),
            leftDelta: Math.round(Math.abs(headerRect.left - rect.left)),
            rightDelta: Math.round(Math.abs(headerRect.right - rect.right)),
          };
        });
      return {
        ready: true,
        panels,
        maxPanelDelta: Math.max(0, ...panels.flatMap((item) => [item.leftDelta, item.rightDelta])),
      };
    });
    checks.productWorkspaceGaps.push(...await productWorkspaceGapEvidence(page, [
      { page: "menu_config", selector: ".menu-config-workspace", scope: "menu_two_column_after_create_open" },
      { page: "menu_config", selector: ".menu-config-editor", scope: "menu_editor_after_create_open" },
    ]));
    checks.menuCreatePanelCount = await menuCreatePanel.count();
    checks.menuCreatePanelTitle = await menuCreatePanel.locator(".create-panel-header strong").innerText();
    checks.menuCreatePanelCloseButtonCount = await menuCreatePanel.getByRole("button", { name: "收起新增入口" }).count();
    checks.menuCreatePanelLegacyCloseButtonCount = await menuCreatePanel.getByRole("button", { name: "关闭" }).count();
    checks.menuActionLabels = await page.locator(".menu-config-page button").evaluateAll((buttons) => (
      buttons.map((button) => button.textContent?.trim()).filter(Boolean)
    ));
    await page.getByRole("button", { name: "展开批量维护表格" }).first().click();
    checks.menuActionLabelsAfterBulkOpen = await page.locator(".menu-config-page button").evaluateAll((buttons) => (
      buttons.map((button) => button.textContent?.trim()).filter(Boolean)
    ));
    await page.locator(".menu-bulk-panel").scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    checks.menuBulkOverlapEvidence = await page.evaluate(() => {
      const bulk = document.querySelector(".menu-bulk-panel");
      const side = document.querySelector(".menu-side-panel");
      if (!bulk || !side) return { ready: false, blockedBySidePanel: true };
      const bulkRect = bulk.getBoundingClientRect();
      const sideRect = side.getBoundingClientRect();
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const x = Math.min(Math.max(bulkRect.right - 24, bulkRect.left + 24), viewportWidth - 24);
      const y = Math.min(Math.max(bulkRect.top + 96, 24), viewportHeight - 24);
      const topElement = document.elementFromPoint(x, y);
      return {
        ready: true,
        blockedBySidePanel: Boolean(topElement && side.contains(topElement)),
        sample: { x: Math.round(x), y: Math.round(y) },
        bulkRect: {
          top: Math.round(bulkRect.top),
          right: Math.round(bulkRect.right),
          bottom: Math.round(bulkRect.bottom),
        },
        sideRect: {
          top: Math.round(sideRect.top),
          right: Math.round(sideRect.right),
          bottom: Math.round(sideRect.bottom),
        },
        topElementClass: topElement instanceof HTMLElement ? topElement.className : "",
      };
    });
    checks.menuConfigVisibleTechnicalTerms = await visibleTechnicalTerms(page, ".menu-config-page");
    screenshots.menuConfig = await capture(page, "menuConfig");
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
    checks.mobileViewport = await page.evaluate(() => ({
      scrollY: Math.round(window.scrollY || document.documentElement.scrollTop || 0),
      innerHeight: window.innerHeight,
      currentConfigVisibleInPrimaryViewport: (() => {
        const rect = document.querySelector(".page-config-panel")?.getBoundingClientRect();
        if (!rect) return false;
        return rect.top >= 0 && rect.top <= Math.min(220, window.innerHeight * 0.35);
      })(),
    }));
    checks.mobileBodyWidth = await page.evaluate(() => ({
      innerWidth: window.innerWidth,
      bodyScrollWidth: document.body.scrollWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
    }));
    checks.mobileConfigurationTopbar = await page.evaluate(() => {
      const topbar = document.querySelector(".topbar");
      const platformEyebrow = document.querySelector(".topbar .eyebrow");
      return {
        platformEyebrowVisible: Boolean(platformEyebrow && getComputedStyle(platformEyebrow).display !== "none"),
        topbarClass: topbar?.className || "",
        actionCount: document.querySelectorAll(".topbar-actions button").length,
      };
    });
    checks.mobileSnapshotSummaryCount = await page.locator(".workbench-status-rail .workbench-status-snapshot").count();
    screenshots.mobileSelected = await capture(page, "mobileSelected");
    screenshots.mobileViewport = await capture(page, "mobileViewport", { fullPage: false });
    checks.artifactEvidenceFiles = await listArtifactEvidenceFiles();

    assert(checks.scanRowsBeforeSelect >= 2 && checks.scanRowsAfterSelect >= 2, "业务页面列表选择后不应丢失", checks);
    assert(checks.selectedText.includes(CONFIG_PAGE_LABEL), "选择页面后未展示当前配置上下文", checks);
    assert(
      checks.pageStructureDesktop.currentConfig.overviewLabel === CONFIG_PAGE_LABEL
      && checks.pageStructureDesktop.currentConfig.overviewLabelTruncated === false
      && checks.directStartStructure.topContext.overviewLabel === CONFIG_PAGE_LABEL
      && checks.directStartStructure.topContext.overviewLabelTruncated === false,
      "当前配置区必须完整展示业务页面名称，不能用省略号截断核心对象",
      checks,
    );
    assert(
      checks.directStartStructure.topContext.actionCount <= 2
      && checks.directStartCards.includes("表单字段与布局")
      && checks.directStartCards.includes("列表与搜索"),
      "直达态顶部只应保留范围类动作，具体配置入口必须由配置任务卡承载",
      checks,
    );
    assert(checks.cardsAfterSelect.includes("表单字段与布局") && checks.cardsAfterSelect.includes("列表与搜索"), "选择页面后配置卡片不完整", checks);
    assert(
      checks.cardPrimaryActionsAfterSelect?.some((item) => item.title === "表单字段与布局" && item.actions.includes("配置表单与布局"))
      && checks.cardPrimaryActionsAfterSelect?.some((item) => item.title === "列表与搜索" && item.actions.includes("配置列表与搜索"))
      && checks.cardPrimaryActionsAfterSelect?.some((item) => item.title === "审批规则" && item.actions.includes("配置审批规则"))
      && !(checks.cardPrimaryActionsAfterSelect || []).flatMap((item) => item.actions || []).includes("配置表单字段")
      && !(checks.cardPrimaryActionsAfterSelect || []).flatMap((item) => item.actions || []).includes("配置列表")
      && !(checks.cardPrimaryActionsAfterSelect || []).flatMap((item) => item.actions || []).includes("配置审批"),
      "配置任务卡主操作必须与任务对象口径一致",
      checks,
    );
    assert(checks.searchRows.length === 1 && checks.searchRows[0] === SWITCH_PAGE_LABEL, "业务页面搜索结果不符合用户预期", checks);
    assert(checks.switchedTitle.includes(SWITCH_PAGE_LABEL), "切换页面后标题未同步", checks);
    assert(
      checks.switchedCurrentLabelLayout.text === SWITCH_PAGE_LABEL
      && checks.switchedCurrentLabelLayout.lineCount === 1,
      "短业务页面名称在当前配置区不应被拆字换行",
      checks,
    );
    assert(checks.cardsAfterSwitch.includes("表单字段与布局") && checks.cardsAfterSwitch.includes("列表与搜索"), "切换页面后配置卡片不完整", checks);
    assert(checks.directStartCards.includes("表单字段与布局") && checks.directDeliveryStatusCount === 1, "直达已选页面缺少配置任务或交付状态", checks);
    assert(defaultDeliveryReadinessIsUserTaskOnly(checks.deliveryReadinessLabels), "默认交付状态不应展示内部审计指标", checks);
    assert(defaultDeliveryReadinessIsUserTaskOnly(checks.directDeliveryReadinessLabels), "直达态默认交付状态不应展示内部审计指标", checks);
    assert(checks.defaultSnapshotSummaryCount === 0 && checks.mobileSnapshotSummaryCount === 0, "默认交付状态不应展示配置快照审计信息", checks);
    assert(
      String(checks.versionPanelTitle || "").includes("版本")
      && checks.versionPanelCloseButtonCount > 0
      && checks.versionPanelLegacyCloseButtonCount === 0,
      "配置版本记录面板必须提供明确收起版本记录动作，不能使用关闭模糊标签",
      checks,
    );
    assert(
      checks.versionPanelActionLabels?.includes("恢复上一版本配置")
      && !["恢复上一版", "恢复此版本", "当前版本"].some((label) => checks.versionPanelActionLabels?.includes(label)),
      "配置版本记录面板的恢复动作必须携带配置对象，不能使用泛化版本动作标签",
      checks,
    );
    assert([
      ...(checks.selectedVisibleTechnicalTerms || []),
      ...(checks.directStartVisibleTechnicalTerms || []),
      ...(checks.listSearchVisibleTechnicalTerms || []),
      ...(checks.formDesignerVisibleTechnicalTerms || []),
      ...(checks.menuConfigVisibleTechnicalTerms || []),
    ].length === 0, "默认界面不应泄漏技术字段或技术参数", checks);
    assert(
      checks.listSearchTitle === "列表与搜索设置"
      && checks.listSearchTabs.join("|") === "列表列|搜索条件|默认分组"
      && checks.listSearchCanvasCount === 1,
      "列表与搜索配置入口没有打开可操作编辑面板",
      checks,
    );
    assert(
      checks.listSearchActionHintText?.includes("上移")
      && checks.listSearchActionHintText?.includes("移除")
      && checks.listSearchActionAriaCount >= 3,
      "列表与搜索字段动作必须提供可见说明和精确动作标签",
      checks,
    );
    assert(checks.listSearchReturnWorkbenchButtonCount > 0, "列表与搜索配置面必须提供明确返回工作台动作", checks);
    assert(
      checks.listSearchSaveButtonCount > 0
      && checks.listSearchLegacySaveButtonCount === 0,
      "列表与搜索保存动作必须明确表达保存列表与搜索，不能使用保存设置模糊标签",
      checks,
    );
    assert(
      checks.listSearchPanelViewport.startsInPrimaryViewport === true
      && checks.listSearchPanelViewport.startsInEditorFocusViewport === true,
      "列表与搜索配置入口打开后没有进入当前编辑主焦点",
      checks,
    );
    assert(
      checks.listSearchFooterOverlapEvidence?.ready === true
      && checks.listSearchFooterOverlapEvidence?.blockedByTabs === false
      && checks.listSearchTabsPosition !== "sticky"
      && checks.approvalFooterOverlapEvidence?.ready === true
      && checks.approvalFooterOverlapEvidence?.blockedByRulePanel === false
      && checks.approvalRulePanelPosition !== "sticky",
      "内嵌配置编辑器滚动到底部状态或操作区后，左侧辅助控制不能悬浮遮挡后续内容",
      checks,
    );
    assert(
      checks.approvalTitle === "审批规则"
      && checks.approvalRulePanelCount === 1
      && checks.approvalStepCanvasCount === 1,
      "审批配置入口没有打开规则配置画布",
      checks,
    );
    assert(checks.approvalReturnWorkbenchButtonCount > 0, "审批配置面必须提供明确返回工作台动作", checks);
    assert(checks.approvalStepMoveButtonCount > 0, "审批步骤必须提供上移和下移按钮，不能只依赖拖拽排序", checks);
    assert(
      checks.approvalStepActionHintText?.includes("上移")
      && checks.approvalStepActionHintText?.includes("下移")
      && checks.approvalStepActionAriaCount >= 3,
      "审批步骤动作必须提供可见说明和精确动作标签",
      checks,
    );
    assert(
      checks.approvalFullRuleButtonCount > 0
      && checks.approvalLegacyMoreRuleButtonCount === 0,
      "审批完整规则入口必须明确表达打开完整规则，不能使用更多规则模糊标签",
      checks,
    );
    assert(
      checks.approvalDiscardButtonCount > 0
      && checks.approvalLegacyRestoreButtonCount === 0,
      "审批未保存调整恢复动作必须使用放弃调整，不能使用还原模糊标签",
      checks,
    );
    assert(
      checks.approvalPanelViewport.startsInPrimaryViewport === true
      && checks.approvalPanelViewport.startsInEditorFocusViewport === true,
      "审批配置入口打开后没有进入当前编辑主焦点",
      checks,
    );
    assert(
      checks.formDesignerTitle === "当前页面字段配置"
      && checks.formDesignerStepText.includes(CONFIG_PAGE_LABEL)
      && checks.formDesignerShellTitle.includes(CONFIG_PAGE_LABEL)
      && checks.formDesignerReturnButtonCount > 0
      && checks.formReturnedTitle.includes(CONFIG_PAGE_LABEL),
      "表单配置入口没有形成进入设计器并返回工作台闭环",
      checks,
    );
    assert(checks.formDesignerLegacyReturnButtonCount === 0, "表单设计器返回动作必须统一为返回工作台，不能继续使用返回配置", checks);
    assert(
      checks.formDesignerDiscardButtonCount > 0
      && checks.formDesignerLegacyResetButtonCount === 0,
      "表单设计器放弃未保存调整必须使用放弃调整，不能使用重置模糊标签",
      checks,
    );
    assert(
      checks.formDesignerFieldSearchInputCount > 0
      && checks.formDesignerFieldSearchResultCount > 0,
      "表单字段配置面必须提供字段搜索和可选字段结果，避免大量字段只能滚动查找",
      checks,
    );
    assert(
      checks.formFieldCreateDialogTitle === "新增字段"
      && checks.formFieldCreateCloseLabelCount === 1
      && checks.formFieldCreateLegacyCloseLabelCount === 0,
      "表单新增字段面板关闭动作必须指向具体对象，不能使用关闭模糊标签",
      checks,
    );
    assert(
      checks.formDesignerCurrentPageLabel === CONFIG_PAGE_LABEL
      && !String(checks.formDesignerStepText || "").includes(`新建${CONFIG_PAGE_LABEL}这个页面`),
      "表单配置态当前页面必须使用业务页面名，不能复用业务新建动作标题",
      checks,
    );
    assert(checks.formDesignerBusinessActionButtons.length === 0, "表单配置态不应出现业务办理动作按钮", checks);
    assert(
      checks.formDesignerFooterOverlapEvidence?.ready === true
      && checks.formDesignerFooterOverlapEvidence?.blockedBySidePanels === false,
      "表单设计器滚动到底部操作区后，左右辅助栏不能悬浮遮挡保存和返回动作",
      checks,
    );
    assert(
      (checks.productWorkspaceGaps || []).length >= 8
      && (checks.productWorkspaceGaps || []).every((item) => item.ready === true && item.columnGapPx === 0),
      "产品页面结构分栏间隙必须纳入统一样式体系并保持为 0",
      checks,
    );
    assert(
      (checks.productPageRegionAlignment || []).length >= 4
      && (checks.productPageRegionAlignment || []).every((item) => item.ready === true && item.maxDelta <= 1),
      "产品页面 Header、Toolbar、主内容和反馈区域外边界必须统一对齐，不能出现页面结构断层",
      checks,
    );
    assert(
      (checks.productPageRuntimeSemantics || []).length >= 4
      && (checks.productPageRuntimeSemantics || []).every((item) => item.ready === true),
      "产品页面模式和区域语义必须真实渲染到运行时 DOM，不能只停留在源码或文档",
      checks,
    );
    assert(
      (checks.businessRuntimeWorkspaceGaps || []).length >= 2
      && (checks.businessRuntimeWorkspaceGaps || []).every((item) => item.ready === true)
      && (checks.businessRuntimeWorkspaceGaps || []).some((item) => item.scope === "list_page_stack" && item.rowGapPx === 12)
      && String(checks.businessRuntimeListPageClass || "").includes("sc-page")
      && String(checks.businessRuntimeFormShellClass || "").includes("sc-panel")
      && checks.businessRuntimeListToolbarCount > 0
      && (checks.businessRuntimeFormBusinessActionButtons || []).length > 0,
      "正常业务办理列表和表单页面必须纳入产品级页面结构体系，并保留业务办理动作",
      checks,
    );
    assert(checks.menuSideSections.join("|") === "新增入口|批量维护|检查发布", "菜单配置侧栏操作分组不完整", checks);
    assert(checks.menuTreeRows > 0 && !checks.menuTreeHead.includes("0 个可配置菜单"), "从配置工作台进入菜单配置后菜单目录为空", checks);
    assert(
      checks.menuWorkspaceAlignment?.ready === true
      && checks.menuWorkspaceAlignment?.leftDelta <= 1
      && checks.menuWorkspaceAlignment?.rightDelta <= 1
      && checks.menuWorkspaceAlignment?.maxPanelDelta <= 1
      && checks.menuWorkspaceAlignmentAfterCreateOpen?.ready === true
      && checks.menuWorkspaceAlignmentAfterCreateOpen?.maxPanelDelta <= 1,
      "菜单配置主工作区和状态/辅助面板外边界必须与页面头部对齐，不能整体缩进形成视觉断层",
      checks,
    );
    assert(
      checks.menuSearchInputCount > 0
      && checks.menuSearchClearButtonCount > 0
      && /^显示 \d+ \/ \d+，未保存 \d+$/.test(String(checks.menuSearchSummaryText || "")),
      "菜单配置必须提供目录搜索数量反馈和清空筛选动作",
      checks,
    );
    assert(
      checks.menuSaveButtonCount > 0
      && checks.menuLegacySaveButtonCount === 0,
      "菜单配置保存动作必须明确表达保存菜单配置，不能使用保存修改模糊标签",
      checks,
    );
    assert(
      checks.menuCreatePanelCount === 1
      && checks.menuCreatePanelTitle === "新增菜单入口"
      && checks.menuCreatePanelCloseButtonCount > 0
      && checks.menuCreatePanelLegacyCloseButtonCount === 0,
      "菜单新增入口面板必须提供明确收起新增入口动作，不能使用关闭模糊标签",
      checks,
    );
    assert(
      ["刷新菜单配置", "新增同级菜单", "新增下级菜单", "复制当前菜单入口", "查看菜单配置说明", "检查菜单生效", "查看菜单版本与回滚", "展开批量维护表格", "收起批量维护表格"]
        .every((label) => [...(checks.menuActionLabels || []), ...(checks.menuActionLabelsAfterBulkOpen || [])].includes(label))
      && !["刷新", "新增同级", "新增下级", "复制当前入口", "查看配置说明", "生效检查", "版本与回滚", "展开批量编辑表格", "展开批量调整", "收起批量调整", "展开", "收起"]
        .some((label) => [...(checks.menuActionLabels || []), ...(checks.menuActionLabelsAfterBulkOpen || [])].includes(label)),
      "菜单配置页辅助动作必须携带菜单对象，不能使用泛化动作标签",
      checks,
    );
    assert(
      checks.menuBulkOverlapEvidence?.ready === true
      && checks.menuBulkOverlapEvidence?.blockedBySidePanel === false,
      "菜单配置滚动到批量维护区后，右侧摘要栏不能悬浮遮挡批量表格",
      checks,
    );
    assert(checks.returnedTitle.includes(CONFIG_PAGE_LABEL) && checks.returnedCards.includes("菜单入口"), "菜单配置返回工作台后上下文丢失", checks);
    assert(
      checks.mobileOrder[0].top !== null
      && checks.mobileOrder[1].top !== null
      && checks.mobileOrder[0].top >= 0
      && checks.mobileOrder[0].top <= 220
      && checks.mobileOrder[0].top < checks.mobileOrder[1].top
      && checks.mobileViewport.currentConfigVisibleInPrimaryViewport === true,
      "移动端选择页面后应先展示当前配置，再展示页面目录",
      checks,
    );
    assert(checks.mobileConfigurationTopbar.platformEyebrowVisible === false, "移动端配置工作台顶栏不应展示平台副标题", checks);
    assert(checks.mobileBodyWidth.documentScrollWidth <= checks.mobileBodyWidth.innerWidth + 8, "移动端出现横向溢出", checks);
    assert(
      checks.artifactEvidenceFiles.join("|") === expectedArtifactPngFiles().join("|"),
      "验收证据目录必须只包含本次运行生成的截图，不能混入历史截图",
      checks,
    );
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
    const summary = await writeReportAndSummary(report);
    console.log(JSON.stringify(VERBOSE_OUTPUT ? report : summary, null, 2));
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
    const summary = await writeReportAndSummary(report);
    console.error(JSON.stringify(VERBOSE_OUTPUT ? report : summary, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
