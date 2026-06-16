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
  page.on("pageerror", (err) => errors.push(`pageerror:${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`console:${msg.text()}`);
  });

  const report = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    checks: {},
    errors,
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
    const leakedDefaultTerms = ["已有个人配置", "契约", "缺口", "治理"].filter((term) => defaultPageText.includes(term));
    report.checks.defaultConfigPage = { defaultCards, selectedName, leakedDefaultTerms };
    assert(
      defaultCards.join("|") === "表单字段与布局|列表与搜索",
      "默认配置卡片不符合用户配置边界",
      { defaultCards },
    );
    assert(selectedName === "项目合同汇总", "配置页没有恢复选中页面", { selectedName });
    assert(
      leakedDefaultTerms.length === 0,
      "默认配置页露出了治理或技术话术",
      { leakedDefaultTerms },
    );

    await page.goto(LIST_SEARCH_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".edit-panel", { timeout: 20000 });
    const listSearchTitle = await page.locator(".edit-panel h2").innerText();
    const saveButtonCount = await page.getByRole("button", { name: "保存设置" }).count();
    const oldSaveButtonCount = await page.getByRole("button", { name: "保存业务默认" }).count();
    const optionSummary = await page.locator(".field-option-summary").first().innerText();
    report.checks.listSearchPanel = {
      listSearchTitle,
      saveButtonCount,
      oldSaveButtonCount,
      optionSummary,
    };
    assert(listSearchTitle === "列表与搜索设置", "列表与搜索面板标题不正确", { listSearchTitle });
    assert(saveButtonCount === 1 && oldSaveButtonCount === 0, "列表与搜索保存按钮文案不正确", {
      saveButtonCount,
      oldSaveButtonCount,
    });
    assert(optionSummary.includes("可添加字段"), "列表与搜索字段池说明不正确", { optionSummary });

    await page.goto(CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    await page.getByRole("button", { name: "进入拖拽设计" }).click();
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    const designTitle = await page.locator(".contract-form-settings h4").innerText();
    const designFieldCountText = await page.locator(".contract-form-settings-field-count").innerText();
    const designFieldCount = Number((designFieldCountText.match(/\d+/) || ["0"])[0]);
    const returnButtonCount = await page.getByRole("button", { name: "返回配置" }).count();
    const legacyPanelCount = await page.locator(".contract-lowcode-objects").count();
    report.checks.formDesigner = { designTitle, designFieldCount, returnButtonCount, legacyPanelCount };
    assert(designTitle === "当前页面设计", "表单设计器标题不正确", { designTitle });
    assert(designFieldCount > 0, "表单设计器没有显示可配置字段数量", { designFieldCountText });
    assert(returnButtonCount >= 1, "表单设计器缺少返回配置入口", { returnButtonCount });
    assert(legacyPanelCount === 0, "默认表单设计器不应显示技术配置面板", { legacyPanelCount });

    await page.getByRole("button", { name: "检查效果" }).click();
    await page.waitForSelector(".contract-field-governance-audit", { timeout: 20000 });
    const auditText = await page.locator(".contract-field-governance-audit").innerText();
    const hasLegacyPolicyText = (await page.locator("body").innerText()).includes("legacy policy");
    report.checks.formAudit = { auditText, hasLegacyPolicyText };
    assert(auditText.includes("检查通过") || auditText.includes("字段被旧规则覆盖"), "表单检查结果不是用户语言", { auditText });
    assert(!hasLegacyPolicyText, "默认表单检查不应显示 legacy policy", { auditText });

    await page.getByRole("button", { name: "返回配置" }).first().click();
    await page.waitForURL((url) => String(url).includes("/admin/business-config"), { timeout: 20000 });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const returnedTitle = await page.locator(".business-config-header h1").innerText();
    const returnedSelected = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    report.checks.returnPath = { returnedTitle, returnedSelected, url: page.url() };
    assert(returnedTitle.includes("项目合同汇总"), "返回配置后标题丢失", { returnedTitle });
    assert(returnedSelected === "项目合同汇总", "返回配置后选中页面丢失", { returnedSelected });

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
