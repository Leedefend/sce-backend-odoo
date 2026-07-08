import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const MODEL = process.env.LOW_CODE_RUNTIME_MODEL || "sc.general.contract";
const ACTION_ID = Number(process.env.LOW_CODE_RUNTIME_ACTION_ID || 669);
const PAGE_LABEL = process.env.LOW_CODE_RUNTIME_PAGE_LABEL || "一般合同（公司）";
let FIELD_NAME = process.env.LOW_CODE_RUNTIME_FIELD || "subcontract_mode";
let FIELD_LABEL = process.env.LOW_CODE_RUNTIME_FIELD_LABEL || "合同分包类型";
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
  await ensureDesignerField(page);
}

async function ensureDesignerField(page) {
  await page.locator("[data-field-name]").first().waitFor({ state: "attached", timeout: 30000 });
  await page.waitForFunction(() => {
    const fields = Array.from(document.querySelectorAll("[data-field-name]"));
    return fields.length >= 10 && fields.every((field) => String(field.getAttribute("data-field-name") || "").trim());
  }, null, { timeout: 30000 }).catch(() => {});

  const preferred = page.locator(`[data-field-name="${FIELD_NAME}"]`).first();
  if (await preferred.count()) {
    await preferred.waitFor({ state: "attached", timeout: 30000 });
    return;
  }

  const fallback = page.locator("[data-field-name]").first();
  await fallback.waitFor({ state: "attached", timeout: 30000 });
  FIELD_NAME = String(await fallback.getAttribute("data-field-name") || "").trim();
  FIELD_LABEL = await selectedFieldLabel(page) || FIELD_LABEL;
}

async function selectField(page) {
  const field = page.locator(`[data-field-name="${FIELD_NAME}"]`).first();
  await field.waitFor({ state: "attached", timeout: 30000 });
  await field.scrollIntoViewIfNeeded().catch(() => {});
  await field.evaluate((el) => {
    const target = el.closest(".field--selectable") || el;
    target.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  });
  await page.locator(".contract-field-selection-card").waitFor({ timeout: 5000 }).catch(async () => {
    await field.click({ force: true });
    await page.locator(".contract-field-selection-card").waitFor({ timeout: 10000 });
  });
}

async function selectedFieldGroup(page) {
  return page.locator(`[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
    const section = el.closest('[data-component="FormSection"]');
    return section?.querySelector(".template-form-section-title")?.textContent?.trim() || "";
  });
}

async function selectedFieldLabel(page) {
  return page.locator(`[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
    const editor = el.querySelector(".field-label-editor");
    if (editor) return editor.value?.trim() || "";
    return el.querySelector(".label")?.textContent?.trim() || el.textContent?.trim() || "";
  });
}

async function moveGroupOptions(page) {
  await selectField(page);
  const select = page.locator(".contract-field-selection-card .contract-field-group-move select");
  await select.waitFor({ timeout: 10000 });
  return select.locator("option").evaluateAll((nodes) => (
    nodes
      .map((node) => String(node.textContent || node.value || "").trim())
      .filter(Boolean)
  ));
}

async function resolveMoveTargetGroup(page, currentGroup) {
  const options = await moveGroupOptions(page);
  const preferred = options.includes(TEMP_GROUP) ? TEMP_GROUP : "";
  const fallback = options.find((groupTitle) => groupTitle && groupTitle !== currentGroup && groupTitle !== HOME_GROUP)
    || options.find((groupTitle) => groupTitle && groupTitle !== currentGroup)
    || "";
  const targetGroup = preferred && preferred !== currentGroup ? preferred : fallback;
  assert(targetGroup, "没有可用于字段移动验收的其他分组", { currentGroup, options });
  return { targetGroup, options };
}

async function renameFieldInDesigner(page, targetLabel, stage) {
  await selectField(page);
  const input = page.locator(".contract-field-label-edit input").first();
  await input.waitFor({ timeout: 10000 });
  const responsePromise = page.waitForResponse((response) => {
    if (!response.url().includes("/api/v1/intent")) return false;
    const post = response.request().postData() || "";
    return post.includes('"ui.form_field_policy.set"') || post.includes("ui.form_field_policy.set");
  }, { timeout: 30000 });
  await input.evaluate((el, label) => {
    el.value = label;
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }, targetLabel);
  await responsePromise;
  await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
  await ensureDesignerField(page);
  await page.waitForFunction(({ fieldName, label }) => {
    const fieldNode = document.querySelector(`[data-field-name="${fieldName}"]`);
    const editor = fieldNode?.querySelector(".field-label-editor");
    return editor && editor.value?.trim() === label;
  }, { fieldName: FIELD_NAME, label: targetLabel }, { timeout: 30000 });
  const actual = await selectedFieldLabel(page);
  assert(actual === targetLabel, "配置页字段改名未生效", { stage, targetLabel, actual });
}

async function moveFieldInDesigner(page, targetGroup) {
  await selectField(page);
  const card = page.locator(".contract-field-selection-card");
  await card.waitFor({ timeout: 10000 });
  const select = card.locator(".contract-field-group-move select");
  await select.waitFor({ timeout: 10000 });
  const options = await select.locator("option").evaluateAll((nodes) => (
    nodes.map((node) => String(node.textContent || node.value || "").trim()).filter(Boolean)
  ));
  assert(options.includes(targetGroup), "移动字段目标分组不在当前可选范围内", { targetGroup, options });
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
  await ensureDesignerField(page);
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

async function assertRuntimeGroup(page, expectedGroup, stage, expectedLabel) {
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
  assert(String(evidence.dom?.label || "").includes(expectedLabel), "办理页字段标签不符合预期", {
    stage,
    label: evidence.dom?.label,
    expectedLabel,
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
    report.field = FIELD_NAME;

    const initialGroup = await selectedFieldGroup(page);
    const initialLabel = await selectedFieldLabel(page) || FIELD_LABEL;
    const restoreGroup = initialGroup || HOME_GROUP;
    report.checks.initial = { group: initialGroup, label: initialLabel };
    report.checks.restoreTarget = { group: restoreGroup };
    const tempTarget = await resolveMoveTargetGroup(page, initialGroup);
    report.checks.moveGroupOptions = tempTarget;
    if (initialGroup !== tempTarget.targetGroup) {
      await moveFieldInDesigner(page, tempTarget.targetGroup);
    }
    report.checks.afterMoveToTemp = await assertRuntimeGroup(page, tempTarget.targetGroup, "afterMoveToTemp", initialLabel);

    await openFormDesigner(page);
    await moveFieldInDesigner(page, restoreGroup);
    report.checks.afterRestoreHome = await assertRuntimeGroup(page, restoreGroup, "afterRestoreHome", initialLabel);

    const renamedLabel = `${initialLabel}验收`;
    await openFormDesigner(page);
    await renameFieldInDesigner(page, renamedLabel, "rename");
    report.checks.afterRename = await assertRuntimeGroup(page, restoreGroup, "afterRename", renamedLabel);

    await openFormDesigner(page);
    await renameFieldInDesigner(page, initialLabel, "renameRestore");
    report.checks.afterRenameRestore = await assertRuntimeGroup(page, restoreGroup, "afterRenameRestore", initialLabel);

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
