import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const MODEL = process.env.LOW_CODE_RUNTIME_MODEL || "sc.general.contract";
const ACTION_ID = Number(process.env.LOW_CODE_RUNTIME_ACTION_ID || 669);
const PAGE_LABEL = process.env.LOW_CODE_RUNTIME_PAGE_LABEL || "一般合同（公司）";
const FIELD_NAME = process.env.LOW_CODE_RUNTIME_FIELD || "subcontract_mode";
const FIELD_LABEL = process.env.LOW_CODE_RUNTIME_FIELD_LABEL || "合同分包类型";
const HOME_GROUP = process.env.LOW_CODE_RUNTIME_HOME_GROUP || "合同基本信息";
const TEMP_GROUP = process.env.LOW_CODE_RUNTIME_TEMP_GROUP || "合同方";

const CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=${encodeURIComponent(MODEL)}&action_id=${ACTION_ID}&page_label=${encodeURIComponent(PAGE_LABEL)}&open_pages=1`;
const BUSINESS_URL = `${BASE_URL}/f/${encodeURIComponent(MODEL)}/new?action_id=${ACTION_ID}&root_menu_xmlid=smart_construction_core.menu_sc_root&page_label=${encodeURIComponent(PAGE_LABEL)}`;

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded" });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator("input").nth(1).fill(PASSWORD);
  await page.getByRole("button", { name: /登录|Log in/i }).click();
  await page.waitForURL((url) => !String(url).includes("/login"), { timeout: 30000 });
}

async function openFormDesigner(page) {
  await page.goto(`${CONFIG_URL}&_t=${Date.now()}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".config-card", { timeout: 30000 });
  await page.getByRole("button", { name: "配置表单字段" }).first().click();
  await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
  await page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().waitFor({ timeout: 30000 });
}

async function selectedFieldGroup(page) {
  return page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
    const section = el.closest('[data-component="FormSection"]');
    return section?.querySelector(".template-form-section-title")?.textContent?.trim() || "";
  });
}

async function moveFieldInDesigner(page, targetGroup) {
  const field = page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first();
  await field.scrollIntoViewIfNeeded();
  await field.click({ force: true });
  const card = page.locator(".contract-field-selection-card");
  await card.waitFor({ timeout: 10000 });
  const select = card.locator(".contract-field-group-move select");
  await select.waitFor({ timeout: 10000 });
  await select.selectOption({ label: targetGroup });
  await page.waitForTimeout(300);
  assert(
    await page.getByRole("button", { name: "保存表单设置" }).isEnabled(),
    "移动字段后保存按钮没有启用",
    { targetGroup, panel: await card.innerText().catch(() => "") },
  );
  await page.getByRole("button", { name: "保存表单设置" }).click();
  await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 30000 });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
  await page.locator(`[data-field-name="${FIELD_NAME}"]`).first().waitFor({ timeout: 30000 });
}

async function businessRuntimeEvidence(page) {
  const evidence = { contractPaths: [], dom: null };
  const handler = async (response) => {
    if (!response.url().includes("/api/v1/intent")) return;
    try {
      const post = response.request().postData() || "";
      const intent = JSON.parse(post).intent || "";
      if (intent !== "ui.contract.v2") return;
      const body = await response.json();
      const tree = body?.data?.layoutContract?.containerTree || [];
      const paths = [];
      const walk = (nodes, path) => {
        for (const node of Array.isArray(nodes) ? nodes : []) {
          if (!node || typeof node !== "object") continue;
          const type = String(node.type || node.containerType || "").toLowerCase();
          const title = String(node.string || node.label || node.title || "").trim();
          const nextPath = path.concat(type === "group" && title ? [title] : []);
          if (type === "field" && String(node.name || node.field || "") === FIELD_NAME) paths.push(nextPath);
          for (const key of ["children", "pages", "tabs", "nodes", "items"]) walk(node[key], nextPath);
        }
      };
      walk(tree, []);
      evidence.contractPaths = paths;
    } catch {
      // Other intent responses are not relevant here.
    }
  };
  page.on("response", handler);
  try {
    await page.goto(`${BUSINESS_URL}&_t=${Date.now()}`, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
    await page.locator(`[data-field-name="${FIELD_NAME}"]`).first().waitFor({ timeout: 30000 });
    evidence.dom = await page.locator(`[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
      const section = el.closest('[data-component="FormSection"]');
      return {
        title: section?.querySelector(".template-form-section-title")?.textContent?.trim() || "",
        label: el.querySelector(".label, .field-label-editor")?.textContent?.trim() || el.textContent?.trim() || "",
        allTitles: Array.from(document.querySelectorAll(".template-form-section-title"))
          .map((item) => item.textContent?.trim())
          .filter(Boolean),
      };
    });
  } finally {
    page.off("response", handler);
  }
  return evidence;
}

async function assertRuntimeGroup(page, expectedGroup, stage) {
  const configGroup = await selectedFieldGroup(page);
  assert(configGroup === expectedGroup, "配置页字段分组不符合预期", { stage, expectedGroup, configGroup });
  const evidence = await businessRuntimeEvidence(page);
  const runtimeGroup = evidence.contractPaths?.[0]?.[0] || "";
  const domGroup = evidence.dom?.title || "";
  assert(runtimeGroup === expectedGroup, "办理页 ui.contract.v2 字段分组不符合预期", {
    stage,
    expectedGroup,
    runtimeGroup,
    contractPaths: evidence.contractPaths,
  });
  assert(domGroup === expectedGroup, "办理页 DOM 字段分组不符合预期", {
    stage,
    expectedGroup,
    domGroup,
    dom: evidence.dom,
  });
  assert(String(evidence.dom?.label || "").includes(FIELD_LABEL), "办理页字段标签不符合预期", {
    stage,
    label: evidence.dom?.label,
    expectedLabel: FIELD_LABEL,
  });
  return { configGroup, runtimeGroup, dom: evidence.dom };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const report = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    model: MODEL,
    actionId: ACTION_ID,
    field: FIELD_NAME,
    checks: {},
  };
  try {
    await login(page);
    await openFormDesigner(page);

    const initialGroup = await selectedFieldGroup(page);
    if (initialGroup !== TEMP_GROUP) {
      await moveFieldInDesigner(page, TEMP_GROUP);
    }
    report.checks.afterMoveToTemp = await assertRuntimeGroup(page, TEMP_GROUP, "afterMoveToTemp");

    await openFormDesigner(page);
    await moveFieldInDesigner(page, HOME_GROUP);
    report.checks.afterRestoreHome = await assertRuntimeGroup(page, HOME_GROUP, "afterRestoreHome");

    report.ok = true;
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.ok = false;
    report.failure = {
      message: error?.message || String(error),
      details: error?.details || {},
    };
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 2;
  } finally {
    await browser.close();
  }
}

await main();
