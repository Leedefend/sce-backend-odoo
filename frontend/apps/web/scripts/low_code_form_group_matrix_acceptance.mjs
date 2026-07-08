import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const MODEL = process.env.LOW_CODE_MATRIX_MODEL || "sc.general.contract";
const ACTION_ID = Number(process.env.LOW_CODE_MATRIX_ACTION_ID || 669);
const PAGE_LABEL = process.env.LOW_CODE_MATRIX_PAGE_LABEL || "一般合同（公司）";
let FIELD_NAME = process.env.LOW_CODE_MATRIX_FIELD || "subcontract_mode";
let FIELD_LABEL = process.env.LOW_CODE_MATRIX_FIELD_LABEL || "合同分包类型";
const HOME_GROUP = process.env.LOW_CODE_MATRIX_HOME_GROUP || "合同基本信息";
const EXPECTED_GROUPS = String(
  process.env.LOW_CODE_MATRIX_GROUPS || "合同基本信息,合同方,金额与条款,签署与履约,办理信息",
).split(",").map((item) => item.trim()).filter(Boolean);

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
  let field = page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first();
  if (!(await field.count())) {
    field = page.locator(".field--selectable[data-field-name]").first();
    await field.waitFor({ timeout: 30000 });
    FIELD_NAME = String(await field.getAttribute("data-field-name") || "").trim();
    FIELD_LABEL = await selectedFieldLabel(page) || FIELD_LABEL;
  } else {
    await field.waitFor({ timeout: 30000 });
  }
}

async function groupTitles(page) {
  const titles = await page.locator(".native-container--group").evaluateAll((nodes) => (
    nodes.map((node) => (
      node.getAttribute("data-group-title")?.trim()
      || node.querySelector(":scope > .native-container-head h3")?.textContent?.trim()
      || node.querySelector(".template-form-section-title")?.textContent?.trim()
      || ""
    ))
      .filter(Boolean)
  ));
  return Array.from(new Set(titles));
}

async function selectedFieldGroup(page) {
  return page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
    const section = el.closest('[data-component="FormSection"]');
    return section?.querySelector(".template-form-section-title")?.textContent?.trim() || "";
  });
}

async function selectedFieldLabel(page) {
  return page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().evaluate((el) => {
    const editor = el.querySelector(".field-label-editor");
    if (editor) return editor.value?.trim() || "";
    return el.querySelector(".label")?.textContent?.trim() || el.textContent?.trim() || "";
  });
}

async function selectField(page) {
  const selector = `.field--selectable[data-field-name="${FIELD_NAME}"]`;
  await page.waitForSelector(selector, { timeout: 30000 });
  await page.evaluate((fieldSelector) => {
    const el = document.querySelector(fieldSelector);
    if (!el) throw new Error(`field not found: ${fieldSelector}`);
    el.scrollIntoView({ block: "center", inline: "nearest" });
    el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  }, selector);
  await page.locator(".contract-field-selection-card").waitFor({ timeout: 5000 }).catch(async () => {
    await page.locator(selector).first().click({ force: true });
    await page.locator(".contract-field-selection-card").waitFor({ timeout: 10000 });
  });
}

async function saveFormSettings(page, details) {
  const save = page.getByRole("button", { name: "保存表单设置" });
  assert(await save.isEnabled(), "保存表单设置按钮没有启用", details);
  await save.click();
  await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 30000 });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
  await page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().waitFor({ timeout: 30000 });
}

async function moveFieldBySelect(page, targetGroup, stage) {
  await selectField(page);
  const card = page.locator(".contract-field-selection-card");
  const select = card.locator(".contract-field-group-move select");
  await select.waitFor({ timeout: 10000 });
  const optionLabels = await select.locator("option").evaluateAll((nodes) => (
    nodes.map((node) => node.textContent?.trim()).filter(Boolean)
  ));
  assert(optionLabels.includes(targetGroup), "移动到分组选项缺失", { stage, targetGroup, optionLabels });
  await select.selectOption({ label: targetGroup });
  await page.waitForTimeout(300);
  await saveFormSettings(page, {
    stage,
    targetGroup,
    panel: await card.innerText().catch(() => ""),
  });
}

async function moveFieldByDrag(page, targetGroup, stage) {
  const groups = await page.locator(".native-container--group").evaluateAll((nodes) => (
    nodes.map((node, index) => {
      const stable = node.getAttribute("data-group-title")?.trim() || "";
      const title = stable
        || node.querySelector(":scope > .native-container-head")?.textContent?.replace(/\+/g, " ").replace(/\s+/g, " ").trim()
        || node.querySelector(".template-form-section-title")?.textContent?.trim()
        || "";
      return { index, title };
    }).filter((item) => item.title)
  ));
  const target = groups.find((item) => item.title === targetGroup);
  assert(target, "拖拽目标分组缺失", { stage, targetGroup, groups });

  const sourceSelector = `.field--selectable[data-field-name="${FIELD_NAME}"]`;
  await page.waitForSelector(sourceSelector, { timeout: 30000 });
  const source = page.locator(sourceSelector).first();
  const targetGroupNode = page.locator(".native-container--group").nth(target.index);
  const targetField = targetGroupNode.locator(".field--selectable").first();
  const targetStrip = targetGroupNode.locator(':scope > [data-drop-zone="field-group"]').first();
  const dropTarget = await targetField.count() ? targetField : targetStrip;
  await source.scrollIntoViewIfNeeded().catch(async () => {
    await page.locator(sourceSelector).first().waitFor({ timeout: 30000 });
  });
  await dropTarget.scrollIntoViewIfNeeded();
  await source.dragTo(dropTarget);
  await page.waitForTimeout(300);
  const moved = await selectedFieldGroup(page).catch(() => "");
  if (moved !== targetGroup) {
    await page.evaluate(({ fieldName, groupTitle }) => {
      const sourceNode = document.querySelector(`.field--selectable[data-field-name="${fieldName}"]`);
      const targetNode = Array.from(document.querySelectorAll(".native-container--group")).find((node) => (
        node.getAttribute("data-group-title")?.trim()
        || node.querySelector(":scope > .native-container-head h3")?.textContent?.trim()
        || node.querySelector(".template-form-section-title")?.textContent?.trim()
        || ""
      ) === groupTitle);
      if (!sourceNode || !targetNode) return;
      const dataTransfer = new DataTransfer();
      ["dragstart", "dragenter", "dragover", "drop", "dragend"].forEach((type) => {
        const target = type === "dragstart" || type === "dragend" ? sourceNode : targetNode;
        target.dispatchEvent(new DragEvent(type, {
          bubbles: true,
          cancelable: true,
          dataTransfer,
        }));
      });
    }, { fieldName: FIELD_NAME, groupTitle: targetGroup });
  }
  await page.waitForTimeout(500);
  await saveFormSettings(page, { stage, targetGroup, groups });
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
      // Ignore unrelated intent responses.
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

async function assertGroupEverywhere(page, expectedGroup, stage, expectedLabel) {
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
    expectedLabel,
    label: evidence.dom?.label,
  });
  return { configGroup, runtimeGroup, dom: evidence.dom };
}

async function ensureFieldInGroup(page, group, stage, expectedLabel) {
  await openFormDesigner(page);
  const current = await selectedFieldGroup(page);
  if (current !== group) {
    await moveFieldBySelect(page, group, `${stage}:setup:${current}->${group}`);
  }
  return assertGroupEverywhere(page, group, `${stage}:setup-verify:${group}`, expectedLabel);
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
    expectedGroups: EXPECTED_GROUPS,
    matrix: [],
    drag: null,
  };
  try {
    await login(page);
    await openFormDesigner(page);
    report.field = FIELD_NAME;
    const initialGroup = await selectedFieldGroup(page);
    const initialLabel = await selectedFieldLabel(page) || FIELD_LABEL;
    const baselineGroup = EXPECTED_GROUPS.includes(initialGroup) ? initialGroup : HOME_GROUP;
    const restoreGroup = initialGroup || baselineGroup;
    report.initialLabel = initialLabel;
    report.initialGroup = initialGroup;
    report.baselineGroup = baselineGroup;
    report.restoreGroup = restoreGroup;
    const actualGroups = await groupTitles(page);
    const missingGroups = EXPECTED_GROUPS.filter((group) => !actualGroups.includes(group));
    assert(!missingGroups.length, "配置页分组不完整", { expectedGroups: EXPECTED_GROUPS, actualGroups, missingGroups });

    await ensureFieldInGroup(page, baselineGroup, "baseline", initialLabel);
    const dragTarget = EXPECTED_GROUPS.find((group) => group !== baselineGroup);
    if (dragTarget) {
      await openFormDesigner(page);
      await moveFieldByDrag(page, dragTarget, `${baselineGroup}->${dragTarget}:drag`);
      report.drag = await assertGroupEverywhere(page, dragTarget, `${baselineGroup}->${dragTarget}:drag-verify`, initialLabel);
    }

    for (const sourceGroup of EXPECTED_GROUPS) {
      await ensureFieldInGroup(page, sourceGroup, `pair-source:${sourceGroup}`, initialLabel);
      for (const targetGroup of EXPECTED_GROUPS) {
        if (sourceGroup === targetGroup) continue;
        await openFormDesigner(page);
        await moveFieldBySelect(page, targetGroup, `${sourceGroup}->${targetGroup}:select`);
        const check = await assertGroupEverywhere(page, targetGroup, `${sourceGroup}->${targetGroup}:verify`, initialLabel);
        report.matrix.push({
          sourceGroup,
          targetGroup,
          method: "select",
          configGroup: check.configGroup,
          runtimeGroup: check.runtimeGroup,
          domGroup: check.dom.title,
        });
      }
    }

    await ensureFieldInGroup(page, restoreGroup, "restore", initialLabel);
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
process.exit(process.exitCode || 0);
