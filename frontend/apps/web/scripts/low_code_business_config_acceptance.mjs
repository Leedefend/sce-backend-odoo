import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://localhost:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "low-code-business-config");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");

const CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=construction.contract&action_id=562&page_label=${encodeURIComponent("项目合同汇总")}&open_pages=1`;
const LIST_SEARCH_URL = `${CONFIG_URL}&open_list_search=1`;
const ANALYSIS_MODEL = process.env.LOW_CODE_ANALYSIS_MODEL || "sc.account.income.expense.summary";
const ANALYSIS_ACTION_ID = process.env.LOW_CODE_ANALYSIS_ACTION_ID || "681";
const ANALYSIS_MENU_ID = process.env.LOW_CODE_ANALYSIS_MENU_ID || "372";
const ANALYSIS_PAGE_LABEL = process.env.LOW_CODE_ANALYSIS_PAGE_LABEL || "账户收支统计表";
const ANALYSIS_CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=${encodeURIComponent(ANALYSIS_MODEL)}&action_id=${encodeURIComponent(ANALYSIS_ACTION_ID)}&menu_id=${encodeURIComponent(ANALYSIS_MENU_ID)}&page_label=${encodeURIComponent(ANALYSIS_PAGE_LABEL)}&open_pages=1`;
const DEFAULT_UI_FORBIDDEN_TERMS = ["已有个人配置", "个人偏好", "契约", "缺口", "治理", "legacy policy"];

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function ensureDirs() {
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
}

async function visibleForbiddenTerms(page, selector = "body") {
  const text = await page.locator(selector).innerText();
  return DEFAULT_UI_FORBIDDEN_TERMS.filter((term) => text.includes(term));
}

async function captureStep(page, name) {
  const fileName = `${name}.png`;
  const filePath = path.join(ARTIFACT_ROOT, fileName);
  await page.screenshot({ path: filePath, fullPage: true });
  return path.relative(ROOT_DIR, filePath);
}

function consoleEntry(msg) {
  const location = typeof msg.location === "function" ? msg.location() : {};
  const url = String(location.url || "");
  return {
    text: msg.text(),
    url,
    lineNumber: location.lineNumber || 0,
    columnNumber: location.columnNumber || 0,
  };
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded" });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator("input").nth(1).fill(PASSWORD);
  await page.getByRole("button", { name: /登录|Log in/i }).click();
  await page.waitForURL((url) => !String(url).includes("/login"), { timeout: 20000 });
}

async function formDesignerFieldTexts(page) {
  return page.locator(".field--selectable").evaluateAll((nodes) => (
    nodes.map((node) => node.textContent?.replace(/\s+/g, " ").trim()).filter(Boolean)
  ));
}

async function dragDesignerField(page, fromIndex, toIndex) {
  const source = page.locator(".field--selectable").nth(fromIndex).locator(".field-order-handle");
  const target = page.locator(".field--selectable").nth(toIndex);
  await source.dragTo(target);
}

async function clickFirstAvailableAnalysisField(page, tabLabels) {
  const panel = page.locator(".edit-panel").filter({ hasText: "分析视图设置" });
  for (const label of tabLabels) {
    await panel.getByRole("button", { name: new RegExp(label) }).click();
    const optionCount = await panel.locator(".field-option-pool button").count();
    if (optionCount > 0) {
      await panel.locator(".field-option-pool button").first().click();
      return { editedTab: label, optionCount };
    }
  }
  return { editedTab: "", optionCount: 0 };
}

async function main() {
  await ensureDirs();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  const warnings = [];
  page.on("pageerror", (err) => errors.push(`pageerror:${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const entry = consoleEntry(msg);
    errors.push({ type: "console", ...entry });
  });

  const report = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    checks: {},
    artifacts: {},
    errors,
    warnings,
  };

  try {
    await login(page);

    await page.goto(CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const defaultCards = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const selectedName = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const defaultPageText = await page.locator("body").innerText();
    const pageTypeLabels = await page.locator(".page-type-tabs button").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const leakedDefaultTerms = await visibleForbiddenTerms(page);
    const defaultVersionButtonCount = await page.getByRole("button", { name: "版本记录" }).count();
    await page.getByRole("button", { name: "版本记录" }).first().click();
    await page.waitForSelector(".version-panel", { timeout: 10000 });
    const defaultVersionTitle = await page.locator(".version-panel h2").innerText();
    const defaultVersionDescription = await page.locator(".version-panel .edit-panel-head p").innerText();
    const defaultVersionPanelText = await page.locator(".version-panel").innerText();
    const defaultVersionRowCount = await page.locator(".version-panel .version-row").count();
    const defaultHistoricalVersionRowCount = await page.locator(".version-panel .version-row button:not([disabled])").count();
    const leakedDefaultVersionTerms = await visibleForbiddenTerms(page, ".version-panel");
    await page.locator(".version-panel").getByRole("button", { name: "关闭" }).click();
    await page.waitForSelector(".version-panel", { state: "detached", timeout: 10000 });
    const initialPageRows = await page.locator(".scan-row-main strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByPlaceholder("输入页面名称").fill("合同办理");
    const searchedPageRows = await page.locator(".scan-row-main strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByPlaceholder("输入页面名称").fill("");
    await page.getByRole("button", { name: "表单页面" }).click();
    const formPageRows = await page.locator(".scan-row-main strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByRole("button", { name: "分析页面" }).click();
    const analysisPageRows = await page.locator(".scan-row-main strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByRole("button", { name: "全部页面" }).click();
    const alternateRow = page.locator(".scan-row").filter({ hasText: "合同办理" }).first();
    await alternateRow.getByRole("button", { name: "选择" }).click();
    await page.waitForFunction(() => {
      const selected = document.querySelector(".scan-row--selected .scan-row-main strong");
      return selected?.textContent?.trim() === "合同办理";
    });
    const selectedAfterSwitch = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const titleAfterSwitch = await page.locator(".business-config-header h1").innerText();
    const cardsAfterSwitch = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const originalRow = page.locator(".scan-row").filter({ hasText: "项目合同汇总" }).first();
    await originalRow.getByRole("button", { name: "选择" }).click();
    await page.waitForFunction(() => {
      const selected = document.querySelector(".scan-row--selected .scan-row-main strong");
      return selected?.textContent?.trim() === "项目合同汇总";
    });
    const selectedAfterRestore = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    await page.getByRole("button", { name: "高级设置" }).click();
    await page.waitForSelector(".scope-panel", { timeout: 10000 });
    const advancedScopeLabels = await page.locator(".scope-panel label span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const advancedText = await page.locator("body").innerText();
    const advancedPanelVisible = await page.locator(".scan-panel--admin").count();
    const snapshotDownloadButtonCount = await page.getByRole("button", { name: "下载当前快照" }).count();
    const snapshotCompareButtonCount = await page.getByRole("button", { name: "对比快照" }).count();
    await page.getByRole("button", { name: "高级设置" }).click();
    await page.waitForSelector(".scope-panel", { state: "detached", timeout: 10000 });
    await page.locator(".scan-row--selected").getByRole("button", { name: "预览页面" }).click();
    await page.waitForURL((url) => String(url).includes("/a/562"), { timeout: 20000 });
    const previewUrl = page.url();
    await page.goBack({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    report.checks.defaultConfigPage = {
      defaultCards,
      selectedName,
      pageTypeLabels,
      leakedDefaultTerms,
      defaultHasUnwiredCopy: defaultPageText.includes("编辑入口待接入"),
      defaultVersionButtonCount,
      defaultVersionTitle,
      defaultVersionDescription,
      defaultVersionPanelText,
      defaultVersionRowCount,
      defaultHistoricalVersionRowCount,
      leakedDefaultVersionTerms,
      initialPageRows,
      searchedPageRows,
      formPageRows,
      analysisPageRows,
      selectedAfterSwitch,
      titleAfterSwitch,
      cardsAfterSwitch,
      selectedAfterRestore,
      advancedScopeLabels,
      advancedPanelVisible,
      advancedHasUnwiredCopy: advancedText.includes("编辑入口待接入"),
      advancedHasGovernanceText: advancedText.includes("高级治理视图") && advancedText.includes("治理结论"),
      snapshotDownloadButtonCount,
      snapshotCompareButtonCount,
      previewUrl,
    };
    report.artifacts.defaultConfigPage = await captureStep(page, "default-config-page");
    assert(
      defaultCards.join("|") === "表单字段与布局|列表与搜索",
      "默认配置卡片不符合用户配置边界",
      { defaultCards },
    );
    assert(selectedName === "项目合同汇总", "配置页没有恢复选中页面", { selectedName });
    assert(
      pageTypeLabels.join("|") === "全部页面|表单页面|列表页面|分析页面",
      "页面类型筛选不完整",
      { pageTypeLabels },
    );
    assert(
      initialPageRows.includes("项目合同汇总")
        && initialPageRows.includes("合同办理")
        && searchedPageRows.length === 1
        && searchedPageRows[0] === "合同办理"
        && formPageRows.includes("项目合同汇总"),
      "业务页面搜索或类型筛选不可用",
      { initialPageRows, searchedPageRows, formPageRows },
    );
    assert(!defaultPageText.includes("编辑入口待接入"), "默认配置页出现未接入编辑入口", { defaultPageText });
    assert(
      selectedAfterSwitch === "合同办理"
        && titleAfterSwitch.includes("合同办理")
        && cardsAfterSwitch.includes("表单字段与布局")
        && cardsAfterSwitch.includes("列表与搜索")
        && selectedAfterRestore === "项目合同汇总",
      "业务页面选择或恢复不可用",
      { selectedAfterSwitch, titleAfterSwitch, cardsAfterSwitch, selectedAfterRestore },
    );
    assert(
      advancedScopeLabels.join("|") === "业务对象|页面ID|视图ID|角色编码"
        && advancedPanelVisible === 1
        && advancedText.includes("高级治理视图")
        && advancedText.includes("治理结论")
        && snapshotDownloadButtonCount === 1
        && snapshotCompareButtonCount === 1,
      "高级设置边界不可用",
      { advancedScopeLabels, advancedPanelVisible, snapshotDownloadButtonCount, snapshotCompareButtonCount },
    );
    assert(!advancedText.includes("编辑入口待接入"), "高级设置中出现未接入编辑入口", { advancedText });
    assert(previewUrl.includes("/a/562"), "业务页面预览入口不可用", { previewUrl });
    assert(
      leakedDefaultTerms.length === 0,
      "默认配置页露出了治理或技术话术",
      { leakedDefaultTerms },
    );
    assert(
      defaultVersionButtonCount >= 2
        && defaultVersionTitle.includes("配置版本")
        && defaultVersionDescription.includes("配置保存记录")
        && (defaultVersionRowCount > 0
          ? defaultVersionPanelText.includes("当前版本")
          : defaultVersionPanelText.includes("当前页面暂无版本记录"))
        && (
          defaultHistoricalVersionRowCount === 0
          || defaultVersionPanelText.includes("与当前相比")
          || defaultVersionPanelText.includes("与当前一致")
        )
        && leakedDefaultVersionTerms.length === 0,
      "默认版本记录面板不可用或露出了治理话术",
      {
        defaultVersionButtonCount,
        defaultVersionTitle,
        defaultVersionDescription,
        defaultVersionPanelText,
        defaultVersionRowCount,
        defaultHistoricalVersionRowCount,
        leakedDefaultVersionTerms,
      },
    );

    await page.goto(ANALYSIS_CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const analysisSelectedName = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const analysisCards = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByRole("button", { name: "配置分析视图" }).click();
    await page.waitForSelector(".edit-panel", { timeout: 20000 });
    const analysisPanel = page.locator(".edit-panel").filter({ hasText: "分析视图设置" });
    const analysisTitle = await analysisPanel.locator("h2").innerText();
    const leakedAnalysisTerms = await visibleForbiddenTerms(page, ".edit-panel");
    const analysisTabs = await analysisPanel.locator(".list-search-tabs button span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const analysisOptionSummary = await analysisPanel.locator(".field-option-summary").innerText();
    const analysisInitialChipCount = await analysisPanel.locator(".field-chip").count();
    const analysisEditAttempt = await clickFirstAvailableAnalysisField(page, analysisTabs);
    const analysisChangedChipCount = await analysisPanel.locator(".field-chip").count();
    const analysisDirtyVisible = await analysisPanel.locator(".edit-dirty").count();
    const analysisSaveEnabledAfterEdit = await analysisPanel.getByRole("button", { name: "保存设置" }).isEnabled();
    const analysisResetEnabledAfterEdit = await analysisPanel.getByRole("button", { name: "放弃调整" }).isEnabled();
    if (analysisEditAttempt.optionCount > 0) {
      await analysisPanel.getByRole("button", { name: "放弃调整" }).click();
    }
    const analysisResetChipCount = await analysisPanel.locator(".field-chip").count();
    report.checks.analysisPanel = {
      analysisSelectedName,
      analysisCards,
      analysisTitle,
      leakedAnalysisTerms,
      analysisTabs,
      analysisOptionSummary,
      analysisInitialChipCount,
      analysisEditAttempt,
      analysisChangedChipCount,
      analysisDirtyVisible,
      analysisSaveEnabledAfterEdit,
      analysisResetEnabledAfterEdit,
      analysisResetChipCount,
      url: page.url(),
    };
    report.artifacts.analysisPanel = await captureStep(page, "analysis-panel");
    assert(analysisSelectedName === ANALYSIS_PAGE_LABEL, "分析配置页没有选中目标页面", {
      analysisSelectedName,
      expected: ANALYSIS_PAGE_LABEL,
    });
    assert(analysisCards.includes("分析视图"), "分析页面没有展示分析视图配置卡片", { analysisCards });
    assert(analysisTitle === "分析视图设置", "分析视图面板标题不正确", { analysisTitle });
    assert(
      analysisTabs.join("|") === "透视指标|透视维度|图表指标|图表维度",
      "分析视图配置类型切换不完整",
      { analysisTabs },
    );
    assert(analysisOptionSummary.includes("可添加字段"), "分析视图字段池说明不正确", { analysisOptionSummary });
    assert(
      leakedAnalysisTerms.length === 0,
      "分析视图默认面板露出了治理或技术话术",
      { leakedAnalysisTerms },
    );
    assert(
      analysisEditAttempt.optionCount > 0
        && analysisChangedChipCount === analysisInitialChipCount + 1
        && analysisDirtyVisible > 0
        && analysisSaveEnabledAfterEdit
        && analysisResetEnabledAfterEdit
        && analysisResetChipCount === analysisInitialChipCount,
      "分析视图草稿编辑或放弃调整不可用",
      {
        analysisInitialChipCount,
        analysisEditAttempt,
        analysisChangedChipCount,
        analysisDirtyVisible,
        analysisSaveEnabledAfterEdit,
        analysisResetEnabledAfterEdit,
        analysisResetChipCount,
      },
    );

    await page.goto(LIST_SEARCH_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".edit-panel", { timeout: 20000 });
    const listSearchTitle = await page.locator(".edit-panel h2").innerText();
    const leakedListSearchTerms = await visibleForbiddenTerms(page, ".edit-panel");
    const saveButtonCount = await page.getByRole("button", { name: "保存设置" }).count();
    const oldSaveButtonCount = await page.getByRole("button", { name: "保存业务默认" }).count();
    const optionSummary = await page.locator(".field-option-summary").first().innerText();
    const initialListChipCount = await page.locator(".field-chip-editor").first().locator(".field-chip").count();
    const firstOption = page.locator(".field-option-pool button").first();
    const optionCount = await page.locator(".field-option-pool button").count();
    if (optionCount > 0) {
      await firstOption.click();
    }
    const changedListChipCount = await page.locator(".field-chip-editor").first().locator(".field-chip").count();
    const dirtyVisible = await page.locator(".edit-dirty").count();
    const saveEnabledAfterEdit = await page.getByRole("button", { name: "保存设置" }).isEnabled();
    const resetEnabledAfterEdit = await page.getByRole("button", { name: "放弃调整" }).isEnabled();
    if (optionCount > 0) {
      await page.getByRole("button", { name: "放弃调整" }).click();
    }
    const resetListChipCount = await page.locator(".field-chip-editor").first().locator(".field-chip").count();
    const listSearchTabs = await page.locator(".list-search-tabs button span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await page.getByRole("button", { name: /搜索条件/ }).click();
    const filterEditorTitle = await page.locator(".field-chip-editor header strong").innerText();
    const filterOptionSummary = await page.locator(".field-option-summary").innerText();
    await page.getByRole("button", { name: /默认分组/ }).click();
    const groupEditorTitle = await page.locator(".field-chip-editor header strong").innerText();
    const groupOptionSummary = await page.locator(".field-option-summary").innerText();
    await page.getByRole("button", { name: /列表列/ }).click();
    await page.locator(".field-option-search").fill("合同");
    const searchedListOptionLabels = await page.locator(".field-option-pool button").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const searchedListOptionCount = searchedListOptionLabels.length;
    await page.locator(".field-option-search").fill("");
    report.checks.listSearchPanel = {
      listSearchTitle,
      saveButtonCount,
      oldSaveButtonCount,
      optionSummary,
      leakedListSearchTerms,
      optionCount,
      initialListChipCount,
      changedListChipCount,
      dirtyVisible,
      saveEnabledAfterEdit,
      resetEnabledAfterEdit,
      resetListChipCount,
      listSearchTabs,
      filterEditorTitle,
      filterOptionSummary,
      groupEditorTitle,
      groupOptionSummary,
      searchedListOptionCount,
      searchedListOptionLabels,
    };
    report.artifacts.listSearchPanel = await captureStep(page, "list-search-panel");
    assert(listSearchTitle === "列表与搜索设置", "列表与搜索面板标题不正确", { listSearchTitle });
    assert(saveButtonCount === 1 && oldSaveButtonCount === 0, "列表与搜索保存按钮文案不正确", {
      saveButtonCount,
      oldSaveButtonCount,
    });
    assert(optionSummary.includes("可添加字段"), "列表与搜索字段池说明不正确", { optionSummary });
    assert(
      leakedListSearchTerms.length === 0,
      "列表与搜索默认面板露出了治理或技术话术",
      { leakedListSearchTerms },
    );
    assert(optionCount > 0, "列表与搜索没有可添加字段", { optionCount });
    assert(
      listSearchTabs.join("|") === "列表列|搜索条件|默认分组"
        && filterEditorTitle === "搜索筛选字段"
        && filterOptionSummary.includes("可添加字段")
        && groupEditorTitle === "搜索分组字段"
        && groupOptionSummary.includes("可添加字段"),
      "列表与搜索配置类型切换不可用",
      { listSearchTabs, filterEditorTitle, filterOptionSummary, groupEditorTitle, groupOptionSummary },
    );
    assert(
      searchedListOptionCount > 0 && searchedListOptionLabels.every((label) => label.includes("合同")),
      "列表与搜索字段池搜索不可用",
      { searchedListOptionCount, searchedListOptionLabels },
    );
    assert(
      changedListChipCount === initialListChipCount + 1
        && dirtyVisible > 0
        && saveEnabledAfterEdit
        && resetEnabledAfterEdit
        && resetListChipCount === initialListChipCount,
      "列表与搜索草稿编辑或放弃调整不可用",
      {
        initialListChipCount,
        changedListChipCount,
        dirtyVisible,
        saveEnabledAfterEdit,
        resetEnabledAfterEdit,
        resetListChipCount,
      },
    );

    await page.goto(CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    await page.getByRole("button", { name: "进入拖拽设计" }).click();
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    const designTitle = await page.locator(".contract-form-settings h4").innerText();
    const leakedFormDesignerTerms = await visibleForbiddenTerms(page, ".contract-form-settings");
    const designFieldCountText = await page.locator(".contract-form-settings-field-count").innerText();
    const designFieldCount = Number((designFieldCountText.match(/\d+/) || ["0"])[0]);
    const dragHandleCount = await page.locator(".field-order-handle").count();
    const selectableField = page.locator(".field--selectable").first();
    const selectableFieldCount = await page.locator(".field--selectable").count();
    const returnButtonCount = await page.getByRole("button", { name: "返回配置" }).count();
    const legacyPanelCount = await page.locator(".contract-lowcode-objects").count();
    await selectableField.click();
    const selectedFieldCount = await page.locator(".field--selected").count();
    const selectedPanelText = await page.locator(".contract-field-selection-card").innerText();
    await page.locator(".contract-field-selection-card").getByText("隐藏", { exact: true }).click();
    const formDirtyAfterHide = await page.locator(".contract-field-governance-dirty").count();
    const saveFormEnabledAfterHide = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    const resetFormEnabledAfterHide = await page.getByRole("button", { name: "重置" }).isEnabled();
    await page.getByRole("button", { name: "重置" }).click();
    const formDirtyAfterReset = await page.locator(".contract-field-governance-dirty").count();
    const saveFormEnabledAfterReset = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await page.locator(".field--selectable").nth(1).click();
    const selectedPanelBeforeMove = await page.locator(".contract-field-selection-card").innerText();
    await page.locator(".contract-field-selection-card button[title='上移']").click();
    const formDirtyAfterMove = await page.locator(".contract-field-governance-dirty").count();
    const saveFormEnabledAfterMove = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await page.getByRole("button", { name: "重置" }).click();
    const formDirtyAfterMoveReset = await page.locator(".contract-field-governance-dirty").count();
    const saveFormEnabledAfterMoveReset = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    const formOrderBeforeDragPersist = await formDesignerFieldTexts(page);
    await dragDesignerField(page, 0, 3);
    await page.waitForFunction((before) => {
      const rows = Array.from(document.querySelectorAll(".field--selectable"))
        .map((node) => node.textContent?.replace(/\s+/g, " ").trim())
        .filter(Boolean);
      return rows.length >= 4 && rows[0] !== before[0] && rows[3] === before[0];
    }, formOrderBeforeDragPersist);
    const formOrderAfterDrag = await formDesignerFieldTexts(page);
    const saveFormEnabledAfterDrag = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await page.getByRole("button", { name: "保存表单设置" }).click();
    await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    const formOrderAfterPersistReload = await formDesignerFieldTexts(page);
    await dragDesignerField(page, 3, 0);
    await page.waitForFunction((before) => {
      const rows = Array.from(document.querySelectorAll(".field--selectable"))
        .map((node) => node.textContent?.replace(/\s+/g, " ").trim())
        .filter(Boolean);
      return rows.length >= 4 && rows[0] === before[0];
    }, formOrderBeforeDragPersist);
    const saveFormEnabledAfterRestoreDrag = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await page.getByRole("button", { name: "保存表单设置" }).click();
    await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    const formOrderAfterRestoreReload = await formDesignerFieldTexts(page);
    await page.locator(".field--selectable").first().click();
    await page.waitForSelector(".contract-field-selection-card", { timeout: 10000 });
    await page.locator(".contract-field-selection-card").getByRole("button", { name: "新增字段" }).click();
    await page.waitForSelector(".contract-field-create-dialog", { timeout: 10000 });
    const createFieldDialogText = await page.locator(".contract-field-create-dialog").innerText();
    const createFieldLabelInputCount = await page.locator(".contract-field-create-dialog input[required]").count();
    const createFieldTypeOptionCount = await page.locator(".contract-field-create-dialog select option").count();
    await page.locator(".contract-field-create-dialog").getByRole("button", { name: "取消" }).click();
    const createFieldDialogClosed = await page.locator(".contract-field-create-dialog").count() === 0;
    report.checks.formDesigner = {
      designTitle,
      leakedFormDesignerTerms,
      designFieldCount,
      selectableFieldCount,
      dragHandleCount,
      selectedFieldCount,
      selectedPanelText,
      formDirtyAfterHide,
      saveFormEnabledAfterHide,
      resetFormEnabledAfterHide,
      formDirtyAfterReset,
      saveFormEnabledAfterReset,
      selectedPanelBeforeMove,
      formDirtyAfterMove,
      saveFormEnabledAfterMove,
      formDirtyAfterMoveReset,
      saveFormEnabledAfterMoveReset,
      formOrderBeforeDragPersist,
      formOrderAfterDrag,
      saveFormEnabledAfterDrag,
      formOrderAfterPersistReload,
      saveFormEnabledAfterRestoreDrag,
      formOrderAfterRestoreReload,
      createFieldDialogText,
      createFieldLabelInputCount,
      createFieldTypeOptionCount,
      createFieldDialogClosed,
      returnButtonCount,
      legacyPanelCount,
    };
    report.artifacts.formDesigner = await captureStep(page, "form-designer");
    assert(designTitle === "当前页面设计", "表单设计器标题不正确", { designTitle });
    assert(
      leakedFormDesignerTerms.length === 0,
      "表单设计器默认面板露出了治理或技术话术",
      { leakedFormDesignerTerms },
    );
    assert(designFieldCount > 0, "表单设计器没有显示可配置字段数量", { designFieldCountText });
    assert(selectableFieldCount > 0, "表单设计器没有可点选字段", { selectableFieldCount });
    assert(dragHandleCount > 0, "表单设计器没有可拖拽字段把手", { dragHandleCount });
    assert(selectedFieldCount > 0 && selectedPanelText.includes("已选字段"), "表单字段点选后没有进入配置状态", {
      selectedFieldCount,
      selectedPanelText,
    });
    assert(
      formDirtyAfterHide > 0
        && saveFormEnabledAfterHide
        && resetFormEnabledAfterHide
        && formDirtyAfterReset === 0
        && !saveFormEnabledAfterReset,
      "表单字段显示隐藏草稿或重置不可用",
      {
        formDirtyAfterHide,
        saveFormEnabledAfterHide,
        resetFormEnabledAfterHide,
        formDirtyAfterReset,
        saveFormEnabledAfterReset,
      },
    );
    assert(
      selectedPanelBeforeMove.includes("已选字段")
        && formDirtyAfterMove > 0
        && saveFormEnabledAfterMove
        && formDirtyAfterMoveReset === 0
        && !saveFormEnabledAfterMoveReset,
      "表单字段顺序调整或重置不可用",
      {
        selectedPanelBeforeMove,
        formDirtyAfterMove,
        saveFormEnabledAfterMove,
        formDirtyAfterMoveReset,
        saveFormEnabledAfterMoveReset,
      },
    );
    assert(
      saveFormEnabledAfterDrag
        && formOrderAfterDrag[0] === formOrderBeforeDragPersist[1]
        && formOrderAfterDrag[3] === formOrderBeforeDragPersist[0]
        && formOrderAfterPersistReload[0] === formOrderAfterDrag[0]
        && formOrderAfterPersistReload[3] === formOrderAfterDrag[3]
        && saveFormEnabledAfterRestoreDrag
        && formOrderAfterRestoreReload[0] === formOrderBeforeDragPersist[0]
        && formOrderAfterRestoreReload[1] === formOrderBeforeDragPersist[1],
      "表单字段拖拽保存刷新后没有保持，或恢复原顺序失败",
      {
        formOrderBeforeDragPersist,
        formOrderAfterDrag,
        saveFormEnabledAfterDrag,
        formOrderAfterPersistReload,
        saveFormEnabledAfterRestoreDrag,
        formOrderAfterRestoreReload,
      },
    );
    assert(
      createFieldDialogText.includes("字段标题")
        && createFieldDialogText.includes("字段类型")
        && createFieldDialogText.includes("创建字段")
        && createFieldLabelInputCount === 1
        && createFieldTypeOptionCount >= 6
        && createFieldDialogClosed,
      "新增字段弹窗不可用",
      { createFieldDialogText, createFieldLabelInputCount, createFieldTypeOptionCount, createFieldDialogClosed },
    );
    assert(returnButtonCount >= 1, "表单设计器缺少返回配置入口", { returnButtonCount });
    assert(legacyPanelCount === 0, "默认表单设计器不应显示技术配置面板", { legacyPanelCount });

    await page.getByRole("button", { name: "检查效果" }).click();
    await page.waitForSelector(".contract-field-governance-audit", { timeout: 20000 });
    const auditText = await page.locator(".contract-field-governance-audit").innerText();
    const leakedAuditTerms = await visibleForbiddenTerms(page, ".contract-form-settings");
    report.checks.formAudit = { auditText, leakedAuditTerms };
    assert(auditText.includes("检查通过") || auditText.includes("字段被旧规则覆盖"), "表单检查结果不是用户语言", { auditText });
    assert(leakedAuditTerms.length === 0, "默认表单检查不应显示治理或技术话术", { auditText, leakedAuditTerms });

    await page.getByRole("button", { name: "返回配置" }).first().click();
    await page.waitForURL((url) => String(url).includes("/admin/business-config"), { timeout: 20000 });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    await page.waitForSelector(".config-card h2", { timeout: 20000 });
    const returnedTitle = await page.locator(".business-config-header h1").innerText();
    const returnedSelected = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const returnedCards = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const returnedUrl = new URL(page.url());
    const returnedQuery = {
      model: returnedUrl.searchParams.get("model"),
      actionId: returnedUrl.searchParams.get("action_id"),
      openPages: returnedUrl.searchParams.get("open_pages"),
      openFormConfig: returnedUrl.searchParams.get("open_form_config"),
      pageLabel: returnedUrl.searchParams.get("page_label"),
    };
    report.checks.returnPath = { returnedTitle, returnedSelected, returnedCards, url: page.url(), returnedQuery };
    report.artifacts.returnPath = await captureStep(page, "return-path");
    assert(returnedTitle.includes("项目合同汇总"), "返回配置后标题丢失", { returnedTitle });
    assert(returnedSelected === "项目合同汇总", "返回配置后选中页面丢失", { returnedSelected });
    assert(
      returnedQuery.model === "construction.contract"
        && returnedQuery.actionId === "562"
        && returnedQuery.openPages === "1"
        && returnedQuery.pageLabel === "项目合同汇总",
      "返回配置后页面上下文丢失",
      returnedQuery,
    );
    assert(
      returnedCards.includes("表单字段与布局") && returnedCards.includes("列表与搜索"),
      "返回配置后配置卡片丢失",
      { returnedCards },
    );

    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const mobileMetrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
    }));
    const mobileSelectedRowBox = await page.locator(".scan-row--selected").boundingBox();
    const mobileActionsBox = await page.locator(".scan-row--selected .scan-row-actions").boundingBox();
    report.checks.mobileConfigPage = {
      mobileMetrics,
      mobileSelectedRowBox,
      mobileActionsBox,
    };
    report.artifacts.mobileConfigPage = await captureStep(page, "mobile-config-page");
    assert(
      mobileMetrics.scrollWidth <= mobileMetrics.innerWidth + 1
        && mobileSelectedRowBox
        && mobileSelectedRowBox.width <= mobileMetrics.innerWidth,
      "移动宽度下低代码配置页出现横向溢出",
      { mobileMetrics, mobileSelectedRowBox, mobileActionsBox },
    );

    assert(errors.length === 0, "浏览器出现未预期错误", { errors });
    assert(warnings.length === 0, "浏览器出现未预期警告", { warnings });

    report.ok = true;
  } catch (err) {
    report.ok = false;
    report.failure = {
      message: err instanceof Error ? err.message : String(err),
      details: err?.details || {},
    };
  } finally {
    await browser.close();
  }

  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  if (!report.ok) {
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(report, null, 2));
}

await main();
