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

function isIgnorableConsoleError(message) {
  return String(message || "").includes("Failed to load resource: the server responded with a status of 404");
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded" });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator("input").nth(1).fill(PASSWORD);
  await page.getByRole("button", { name: /登录|Log in/i }).click();
  await page.waitForURL((url) => !String(url).includes("/login"), { timeout: 20000 });
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
    const text = msg.text();
    if (isIgnorableConsoleError(text)) {
      warnings.push(`console:${text}`);
      return;
    }
    errors.push(`console:${text}`);
  });

  const report = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    checks: {},
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
    const leakedDefaultTerms = await visibleForbiddenTerms(page);
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
    await page.getByRole("button", { name: "全部页面" }).click();
    await page.locator(".scan-row--selected").getByRole("button", { name: "预览页面" }).click();
    await page.waitForURL((url) => String(url).includes("/a/562"), { timeout: 20000 });
    const previewUrl = page.url();
    await page.goBack({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    report.checks.defaultConfigPage = {
      defaultCards,
      selectedName,
      leakedDefaultTerms,
      initialPageRows,
      searchedPageRows,
      formPageRows,
      previewUrl,
    };
    assert(
      defaultCards.join("|") === "表单字段与布局|列表与搜索",
      "默认配置卡片不符合用户配置边界",
      { defaultCards },
    );
    assert(selectedName === "项目合同汇总", "配置页没有恢复选中页面", { selectedName });
    assert(
      initialPageRows.includes("项目合同汇总")
        && initialPageRows.includes("合同办理")
        && searchedPageRows.length === 1
        && searchedPageRows[0] === "合同办理"
        && formPageRows.includes("项目合同汇总"),
      "业务页面搜索或类型筛选不可用",
      { initialPageRows, searchedPageRows, formPageRows },
    );
    assert(previewUrl.includes("/a/562"), "业务页面预览入口不可用", { previewUrl });
    assert(
      leakedDefaultTerms.length === 0,
      "默认配置页露出了治理或技术话术",
      { leakedDefaultTerms },
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
    };
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
      createFieldDialogText,
      createFieldLabelInputCount,
      createFieldTypeOptionCount,
      createFieldDialogClosed,
      returnButtonCount,
      legacyPanelCount,
    };
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
