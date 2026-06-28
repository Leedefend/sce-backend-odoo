import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const DEFAULT_LAYOUT_SAMPLES = [
  {
    model: "sc.general.contract",
    actionId: 669,
    pageLabel: "一般合同（公司）",
    fieldName: "subcontract_mode",
    fieldLabel: "合同分包类型",
    homeGroup: "合同基本信息",
    tempGroup: "合同方",
  },
  {
    model: "construction.contract",
    actionId: 562,
    pageLabel: "项目合同汇总",
    fieldName: "subject",
    fieldLabel: "合同标题",
    homeGroup: "合同基本信息",
    tempGroup: "合同方",
  },
];

let MODEL = "";
let ACTION_ID = 0;
let PAGE_LABEL = "";
let FIELD_NAME = "";
let FIELD_LABEL = "";
let HOME_GROUP = "";
let TEMP_GROUP = "";
let CONFIG_URL = "";
let BUSINESS_URL = "";
let CONTRACT_NAME = "";

function legacyEnvSample() {
  return {
    model: process.env.LOW_CODE_LAYOUT_MODEL || DEFAULT_LAYOUT_SAMPLES[0].model,
    actionId: Number(process.env.LOW_CODE_LAYOUT_ACTION_ID || DEFAULT_LAYOUT_SAMPLES[0].actionId),
    pageLabel: process.env.LOW_CODE_LAYOUT_PAGE_LABEL || DEFAULT_LAYOUT_SAMPLES[0].pageLabel,
    fieldName: process.env.LOW_CODE_LAYOUT_FIELD || DEFAULT_LAYOUT_SAMPLES[0].fieldName,
    fieldLabel: process.env.LOW_CODE_LAYOUT_FIELD_LABEL || DEFAULT_LAYOUT_SAMPLES[0].fieldLabel,
    homeGroup: process.env.LOW_CODE_LAYOUT_HOME_GROUP || DEFAULT_LAYOUT_SAMPLES[0].homeGroup,
    tempGroup: process.env.LOW_CODE_LAYOUT_TEMP_GROUP || DEFAULT_LAYOUT_SAMPLES[0].tempGroup,
  };
}

function layoutSamples() {
  if (process.env.LOW_CODE_LAYOUT_SAMPLES_JSON) {
    const parsed = JSON.parse(process.env.LOW_CODE_LAYOUT_SAMPLES_JSON);
    assert(Array.isArray(parsed) && parsed.length > 0, "LOW_CODE_LAYOUT_SAMPLES_JSON 必须是非空数组");
    return parsed;
  }
  const hasLegacyOverride = [
    "LOW_CODE_LAYOUT_MODEL",
    "LOW_CODE_LAYOUT_ACTION_ID",
    "LOW_CODE_LAYOUT_PAGE_LABEL",
    "LOW_CODE_LAYOUT_FIELD",
    "LOW_CODE_LAYOUT_FIELD_LABEL",
    "LOW_CODE_LAYOUT_HOME_GROUP",
    "LOW_CODE_LAYOUT_TEMP_GROUP",
  ].some((name) => Boolean(process.env[name]));
  return hasLegacyOverride ? [legacyEnvSample()] : DEFAULT_LAYOUT_SAMPLES;
}

function applyLayoutSample(sample) {
  MODEL = String(sample.model || "").trim();
  ACTION_ID = Number(sample.actionId || sample.action_id || 0);
  PAGE_LABEL = String(sample.pageLabel || sample.page_label || "").trim();
  FIELD_NAME = String(sample.fieldName || sample.field_name || "").trim();
  FIELD_LABEL = String(sample.fieldLabel || sample.field_label || "").trim();
  HOME_GROUP = String(sample.homeGroup || sample.home_group || "合同基本信息").trim();
  TEMP_GROUP = String(sample.tempGroup || sample.temp_group || "合同方").trim();
  assert(MODEL && ACTION_ID && PAGE_LABEL && FIELD_NAME, "低代码布局验收样本缺少必要字段", { sample });
  CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=${encodeURIComponent(MODEL)}&action_id=${ACTION_ID}&page_label=${encodeURIComponent(PAGE_LABEL)}&open_pages=1`;
  BUSINESS_URL = `${BASE_URL}/f/${encodeURIComponent(MODEL)}/new?action_id=${ACTION_ID}&root_menu_xmlid=smart_construction_core.menu_sc_root&page_label=${encodeURIComponent(PAGE_LABEL)}`;
  CONTRACT_NAME = `view_orchestration:${MODEL}:form:action:${ACTION_ID}:view:0`;
}

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function normalizeColumns(value, fallback = 0) {
  const columns = Number(value);
  return [1, 2, 3].includes(columns) ? columns : fallback;
}

function alternateColumns(value) {
  const columns = normalizeColumns(value, 3);
  return columns === 3 ? 2 : 3;
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded" });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator("input").nth(1).fill(PASSWORD);
  await page.getByRole("button", { name: /登录|Log in/i }).click();
  await page.waitForURL((url) => !String(url).includes("/login"), { timeout: 30000 });
}

async function authToken(page) {
  return page.evaluate((dbName) => sessionStorage.getItem(`sc_auth_token:${dbName}`) || "", DB_NAME);
}

async function intentRequest(page, intent, params) {
  const token = await authToken(page);
  return page.evaluate(async ({ dbName, tokenValue, intentName, payload }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: tokenValue ? `Bearer ${tokenValue}` : "",
        "X-Trace-Id": `low-code-layout-runtime-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: payload }),
    });
    const body = await response.json().catch(() => ({}));
    return {
      status: response.status,
      ok: body.ok === true,
      data: body.data || {},
      error: body.error || {},
    };
  }, { dbName: DB_NAME, tokenValue: token, intentName: intent, payload: params });
}

async function selectedFieldLabel(page, fieldName = FIELD_NAME) {
  return page.locator(`.field--selectable[data-field-name="${fieldName}"]`).first().evaluate((el) => {
    const editor = el.querySelector(".field-label-editor");
    if (editor) return editor.value?.trim() || "";
    return el.querySelector(".label")?.textContent?.trim() || el.textContent?.trim() || "";
  });
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

async function selectField(page, fieldName = FIELD_NAME) {
  const field = page.locator(`.field--selectable[data-field-name="${fieldName}"]`).first();
  await field.scrollIntoViewIfNeeded();
  await field.evaluate((el) => {
    el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  });
  await page.locator(".contract-field-selection-card").waitFor({ timeout: 5000 }).catch(async () => {
    await field.click({ force: true });
    await page.locator(".contract-field-selection-card").waitFor({ timeout: 10000 });
  });
}

async function selectedFieldGroup(page, fieldName = FIELD_NAME) {
  return page.locator(`.field--selectable[data-field-name="${fieldName}"]`).first().evaluate((el) => {
    const section = el.closest('[data-component="FormSection"]');
    return section?.querySelector(".template-form-section-title")?.textContent?.trim() || "";
  });
}

async function saveFormSettings(page, stage, options = {}) {
  const save = page.getByRole("button", { name: "保存表单设置" });
  assert(await save.isEnabled(), "保存表单设置按钮没有启用", { stage });
  await save.click();
  await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 30000 });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
  if (options.expectFieldVisible !== false) {
    await page.locator(`.field--selectable[data-field-name="${FIELD_NAME}"]`).first().waitFor({ timeout: 30000 });
  }
}

async function ensureFieldInGroup(page, targetGroup, stage) {
  await openFormDesigner(page);
  const current = await selectedFieldGroup(page);
  if (current === targetGroup) return;
  await selectField(page);
  const select = page.locator(".contract-field-selection-card .contract-field-group-move select");
  await select.selectOption({ label: targetGroup });
  await page.waitForTimeout(300);
  await saveFormSettings(page, `${stage}:move:${current}->${targetGroup}`);
}

async function setPageColumns(page, columns, stage) {
  await openFormDesigner(page);
  const select = page.locator(".contract-form-layout-tools select").first();
  const current = normalizeColumns(await select.inputValue(), 0);
  if (current === columns) return current;
  await select.selectOption(String(columns));
  await page.waitForTimeout(300);
  await saveFormSettings(page, stage);
  return current;
}

async function setSelectedGroupColumns(page, columns, stage) {
  await selectField(page);
  const select = page.locator(".contract-field-selection-card .contract-field-group-columns select").first();
  const current = normalizeColumns(await select.inputValue(), 0);
  if (current === columns) return current;
  await select.selectOption(String(columns));
  await page.waitForTimeout(300);
  await saveFormSettings(page, stage);
  return current;
}

async function setSelectedFieldSize(page, size, stage) {
  await selectField(page);
  const select = page.locator(".contract-field-selection-card .contract-field-size-control select").first();
  const current = String(await select.inputValue() || "normal");
  if (current === size) return current;
  await select.selectOption(size);
  await page.waitForTimeout(300);
  await saveFormSettings(page, stage);
  return current;
}

async function setSelectedGroupVisibility(page, visible, stage) {
  await selectField(page);
  const value = visible ? "show" : "hide";
  const input = page.locator(`.contract-field-selection-card .contract-field-group-visibility input[value="${value}"]`).first();
  const checked = await input.isChecked();
  if (checked) return;
  await input.click();
  await page.waitForTimeout(300);
  await saveFormSettings(page, stage, { expectFieldVisible: visible });
}

async function alternateMoveGroupOption(page, currentGroup) {
  await selectField(page);
  const select = page.locator(".contract-field-selection-card .contract-field-group-move select");
  await select.waitFor({ timeout: 10000 });
  const options = await select.locator("option").evaluateAll((nodes) => (
    nodes.map((node) => node.textContent?.trim()).filter(Boolean)
  ));
  const target = options.find((item) => item && item !== currentGroup) || "";
  assert(target, "没有可用于分组显示验收的其他分组", { currentGroup, options });
  return target;
}

function collectRuntimeContract(body) {
  const tree = body?.data?.layoutContract?.containerTree || [];
  const evidence = {
    fieldPaths: [],
    groups: [],
    governance: {
      formColumns: 0,
      groupColumns: {},
      fieldGroups: {},
      fieldLabels: {},
    },
  };
  const applyGovernance = (value) => {
    if (!value || typeof value !== "object" || Array.isArray(value)) return;
    evidence.governance.formColumns = normalizeColumns(value.form_columns ?? value.formColumns, evidence.governance.formColumns);
    const groupColumns = value.group_columns || value.groupColumns;
    if (groupColumns && typeof groupColumns === "object" && !Array.isArray(groupColumns)) {
      for (const [key, raw] of Object.entries(groupColumns)) {
        const columns = normalizeColumns(raw, 0);
        if (key && columns) evidence.governance.groupColumns[key] = columns;
      }
    }
    const fieldGroups = value.field_groups || value.fieldGroups;
    if (fieldGroups && typeof fieldGroups === "object" && !Array.isArray(fieldGroups)) {
      evidence.governance.fieldGroups = { ...evidence.governance.fieldGroups, ...fieldGroups };
    }
    const fieldLabels = value.field_labels || value.fieldLabels;
    if (fieldLabels && typeof fieldLabels === "object" && !Array.isArray(fieldLabels)) {
      evidence.governance.fieldLabels = { ...evidence.governance.fieldLabels, ...fieldLabels };
    }
  };
  const rootGovernance = body?.data?.governance?.view_orchestration || body?.data?.governance?.viewOrchestration;
  applyGovernance(rootGovernance);
  const formGovernance = rootGovernance?.views?.form;
  applyGovernance(formGovernance);
  const walk = (nodes, path) => {
    for (const node of Array.isArray(nodes) ? nodes : []) {
      if (!node || typeof node !== "object") continue;
      applyGovernance(node.sourceAuthority?.governance_source || node.sourceAuthority?.governanceSource);
      const type = String(node.type || node.containerType || "").toLowerCase();
      const title = String(node.string || node.label || node.title || "").trim();
      const attrs = node.attributes && typeof node.attributes === "object" ? node.attributes : {};
      const columns = normalizeColumns(node.cols ?? node.columns ?? attrs.col ?? attrs.columns, 0);
      const nextPath = path.concat(type === "group" && title ? [title] : []);
      if (type === "group") {
        evidence.groups.push({ title, columns, fieldNames: [] });
      }
      if (type === "field" && String(node.name || node.field || "") === FIELD_NAME) {
        evidence.fieldPaths.push({
          path,
          fieldSize: String(node.field_size || node.fieldSize || node.size || ""),
          className: String(node.class || node.className || ""),
        });
      }
      for (const key of ["children", "pages", "tabs", "nodes", "items", "groups"]) walk(node[key], nextPath);
    }
  };
  walk(tree, []);
  return evidence;
}

function collectSavedContract(data) {
  const formSpec = data?.contract_json?.view_orchestration?.views?.form || {};
  const evidence = {
    name: String(data?.name || ""),
    status: String(data?.status || ""),
    versionNo: Number(data?.version_no || 0),
    formColumns: normalizeColumns(formSpec.columns ?? formSpec.cols, 0),
    groupColumns: {},
    groupVisible: {},
    field: {},
  };
  const sections = Array.isArray(formSpec.sections) ? formSpec.sections : [];
  for (const section of sections) {
    if (!section || typeof section !== "object") continue;
    const title = String(section.title || section.label || section.name || "").trim();
    if (!title) continue;
    const columns = normalizeColumns(section.columns ?? section.cols, 0);
    if (columns) evidence.groupColumns[title] = columns;
    evidence.groupVisible[title] = section.visible !== false;
  }
  const layout = Array.isArray(formSpec.layout) ? formSpec.layout : [];
  for (const group of layout) {
    if (!group || typeof group !== "object") continue;
    const title = String(group.string || group.label || group.title || group.name || "").trim();
    if (!title) continue;
    const columns = normalizeColumns(group.columns ?? group.cols ?? group.col, 0);
    if (columns) evidence.groupColumns[title] = columns;
    evidence.groupVisible[title] = group.visible !== false;
  }
  const fields = Array.isArray(formSpec.fields) ? formSpec.fields : [];
  const row = fields.find((item) => item && typeof item === "object" && String(item.name || item.field || "") === FIELD_NAME) || {};
  evidence.field = {
    name: String(row.name || row.field || ""),
    label: String(row.label || row.string || ""),
    visible: row.visible !== false,
    groupTitle: String(row.group_title || row.groupTitle || ""),
    fieldSize: String(row.field_size || row.fieldSize || row.size || ""),
    className: String(row.class || row.className || ""),
  };
  return evidence;
}

async function savedContractEvidence(page) {
  const response = await intentRequest(page, "ui.business_config.contract.get", {
    name: CONTRACT_NAME,
    model: MODEL,
    view_type: "form",
    action_id: ACTION_ID,
    view_id: 0,
  });
  assert(response.ok, "读取表单配置契约失败", { status: response.status, error: response.error, contractName: CONTRACT_NAME });
  return collectSavedContract(response.data);
}

async function readSavedContract(page) {
  const response = await intentRequest(page, "ui.business_config.contract.get", {
    name: CONTRACT_NAME,
    model: MODEL,
    view_type: "form",
    action_id: ACTION_ID,
    view_id: 0,
  });
  assert(response.ok, "读取表单配置契约失败", { status: response.status, error: response.error, contractName: CONTRACT_NAME });
  return response.data;
}

async function patchSavedContract(page, mutator, stage) {
  const current = await readSavedContract(page);
  const contractJson = JSON.parse(JSON.stringify(current.contract_json || {}));
  delete contractJson.legacy_lowcode_draft;
  mutator(contractJson);
  const response = await intentRequest(page, "ui.business_config.contract.save", {
    name: CONTRACT_NAME,
    model: MODEL,
    view_type: "form",
    action_id: ACTION_ID,
    view_id: 0,
    publish: true,
    contract_json: contractJson,
  });
  assert(response.ok, "保存表单配置契约失败", { stage, status: response.status, error: response.error });
}

function mutateFormSpec(contractJson, mutator) {
  const orchestration = contractJson.view_orchestration && typeof contractJson.view_orchestration === "object"
    ? contractJson.view_orchestration
    : {};
  const views = orchestration.views && typeof orchestration.views === "object" ? orchestration.views : {};
  const formSpec = views.form && typeof views.form === "object" ? views.form : {};
  mutator(formSpec);
  views.form = formSpec;
  orchestration.views = views;
  contractJson.view_orchestration = orchestration;
}

function ensureLayoutGroup(formSpec, title, columns = 0) {
  if (!Array.isArray(formSpec.layout)) formSpec.layout = [];
  let group = formSpec.layout.find((item) => (
    item && typeof item === "object" && String(item.string || item.label || item.title || item.name || "") === title
  ));
  if (!group) {
    group = {
      type: "group",
      string: title,
      visible: true,
      children: [],
    };
    formSpec.layout.unshift(group);
  }
  group.visible = true;
  if (columns) {
    group.columns = columns;
    group.cols = columns;
  }
  if (!Array.isArray(group.children)) group.children = [];
  return group;
}

function ensureSection(formSpec, title, columns = 0) {
  if (!Array.isArray(formSpec.sections)) formSpec.sections = [];
  let section = formSpec.sections.find((item) => (
    item && typeof item === "object" && String(item.title || item.label || item.name || "") === title
  ));
  if (!section) {
    section = {
      name: `business_config_section_${formSpec.sections.length + 1}`,
      title,
      visible: true,
      fields: [],
      sequence: (formSpec.sections.length + 1) * 10,
    };
    formSpec.sections.unshift(section);
  }
  section.visible = true;
  if (columns) section.columns = columns;
  if (!Array.isArray(section.fields)) section.fields = [];
  return section;
}

async function setGroupVisibilityByContract(page, groupTitle, visible, stage) {
  await patchSavedContract(page, (contractJson) => {
    mutateFormSpec(contractJson, (formSpec) => {
      for (const section of Array.isArray(formSpec.sections) ? formSpec.sections : []) {
        if (section && typeof section === "object" && String(section.title || section.label || section.name || "") === groupTitle) {
          section.visible = visible;
        }
      }
      for (const group of Array.isArray(formSpec.layout) ? formSpec.layout : []) {
        if (group && typeof group === "object" && String(group.string || group.label || group.title || group.name || "") === groupTitle) {
          group.visible = visible;
        }
      }
      for (const field of Array.isArray(formSpec.fields) ? formSpec.fields : []) {
        if (!field || typeof field !== "object") continue;
        if (String(field.group_title || field.groupTitle || "") === groupTitle) {
          field.visible = visible;
        }
      }
    });
  }, stage);
}

async function ensureProbeFieldVisibleByContract(page) {
  await patchSavedContract(page, (contractJson) => {
    mutateFormSpec(contractJson, (formSpec) => {
      for (const section of Array.isArray(formSpec.sections) ? formSpec.sections : []) {
        if (!section || typeof section !== "object") continue;
        section.visible = true;
        const title = String(section.title || section.label || section.name || "");
        const fields = Array.isArray(section.fields) ? section.fields.map((item) => String(item || "").trim()).filter(Boolean) : [];
        section.fields = fields.filter((name) => name !== FIELD_NAME);
        if (title === HOME_GROUP && !section.fields.includes(FIELD_NAME)) section.fields.push(FIELD_NAME);
      }
      let fieldLayoutNode = null;
      for (const group of Array.isArray(formSpec.layout) ? formSpec.layout : []) {
        if (!group || typeof group !== "object") continue;
        group.visible = true;
        const children = Array.isArray(group.children) ? group.children : [];
        group.children = children.filter((child) => {
          if (child && typeof child === "object" && String(child.name || child.field || "") === FIELD_NAME) {
            fieldLayoutNode = child;
            return false;
          }
          return true;
        });
      }
      const homeGroup = (Array.isArray(formSpec.layout) ? formSpec.layout : []).find((group) => (
        group && typeof group === "object" && String(group.string || group.label || group.title || group.name || "") === HOME_GROUP
      )) || ensureLayoutGroup(formSpec, HOME_GROUP);
      const children = Array.isArray(homeGroup.children) ? homeGroup.children : [];
      children.push(fieldLayoutNode || { type: "field", name: FIELD_NAME });
      homeGroup.children = children;
      const homeSection = ensureSection(formSpec, HOME_GROUP);
      homeSection.fields = (Array.isArray(homeSection.fields) ? homeSection.fields : []).filter((name) => name !== FIELD_NAME);
      homeSection.fields.push(FIELD_NAME);
      for (const field of Array.isArray(formSpec.fields) ? formSpec.fields : []) {
        if (!field || typeof field !== "object") continue;
        field.visible = true;
        if (String(field.name || field.field || "") === FIELD_NAME) field.group_title = HOME_GROUP;
      }
    });
  }, "preflight-probe-field-visible");
}

async function businessRuntimeEvidence(page) {
  const evidence = { contract: null, dom: null };
  const handler = async (response) => {
    if (!response.url().includes("/api/v1/intent")) return;
    try {
      const post = response.request().postData() || "";
      const intent = JSON.parse(post).intent || "";
      if (intent !== "ui.contract.v2") return;
      evidence.contract = collectRuntimeContract(await response.json());
    } catch {
      // Ignore unrelated or already consumed responses.
    }
  };
  page.on("response", handler);
  try {
    await page.goto(`${BUSINESS_URL}&_t=${Date.now()}`, { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
    const field = page.locator(`[data-field-name="${FIELD_NAME}"]`).first();
    const fieldCount = await field.count();
    evidence.dom = await page.evaluate(({ fieldName, tempGroup }) => {
      const fieldNode = document.querySelector(`[data-field-name="${fieldName}"]`);
      const section = fieldNode?.closest('[data-component="FormSection"]') || null;
      const grid = section?.querySelector(".template-form-section-grid") || null;
      const gridColumns = grid ? getComputedStyle(grid).gridTemplateColumns.split(" ").filter(Boolean).length : 0;
      return {
        fieldExists: Boolean(fieldNode),
        fieldClass: fieldNode?.getAttribute("class") || "",
        fieldText: fieldNode?.textContent?.trim() || "",
        groupTitle: section?.querySelector(".template-form-section-title")?.textContent?.trim() || "",
        groupColumns: gridColumns,
        allGroupTitles: Array.from(document.querySelectorAll(".template-form-section-title"))
          .map((item) => item.textContent?.trim())
          .filter(Boolean),
        tempGroupVisible: Array.from(document.querySelectorAll(".template-form-section-title"))
          .some((item) => item.textContent?.trim() === tempGroup),
      };
    }, { fieldName: FIELD_NAME, tempGroup: TEMP_GROUP });
    if (fieldCount) await field.first().waitFor({ timeout: 30000 }).catch(() => {});
  } finally {
    page.off("response", handler);
  }
  return evidence;
}

function groupContractColumns(evidence, title) {
  const governed = normalizeColumns(evidence.contract?.governance?.groupColumns?.[title], 0);
  if (governed) return governed;
  const formColumns = normalizeColumns(evidence.contract?.governance?.formColumns, 0);
  if (formColumns) return formColumns;
  const row = evidence.contract?.groups?.find((item) => item.title === title);
  return normalizeColumns(row?.columns, 0);
}

async function assertRuntimeLayout(page, expected, stage) {
  const evidence = await businessRuntimeEvidence(page);
  evidence.savedContract = await savedContractEvidence(page);
  if (expected.fieldVisible === false) {
    assert(evidence.savedContract.field.visible === false, "保存契约隐藏分组后字段仍然可见", { stage, evidence });
    assert(evidence.dom?.fieldExists === false, "办理页隐藏分组后字段仍然可见", { stage, evidence });
    return evidence;
  }
  assert(evidence.dom?.fieldExists, "办理页字段不存在", { stage, evidence });
  assert(String(evidence.dom?.fieldText || "").trim(), "办理页字段名称为空", { stage, evidence });
  if (expected.groupTitle) {
    assert(evidence.savedContract.field.groupTitle === expected.groupTitle, "保存契约字段分组不符合预期", { stage, expected, evidence });
    assert(evidence.dom?.groupTitle === expected.groupTitle, "办理页字段分组不符合预期", { stage, expected, evidence });
  }
  if (expected.groupColumns) {
    const contractColumns = normalizeColumns(
      evidence.savedContract.groupColumns?.[expected.groupTitle || evidence.dom?.groupTitle] || evidence.savedContract.formColumns,
      0,
    );
    assert(contractColumns === expected.groupColumns, "保存契约分组列数不符合预期", { stage, expected, contractColumns, evidence });
    assert(evidence.dom?.groupColumns === expected.groupColumns, "办理页 DOM 分组列数不符合预期", { stage, expected, evidence });
  }
  if (expected.fieldSize) {
    assert(evidence.savedContract.field.fieldSize === expected.fieldSize || evidence.savedContract.field.className.includes(`field--${expected.fieldSize}`), "保存契约字段尺寸不符合预期", {
      stage,
      expected,
      evidence,
    });
    const expectedClass = expected.fieldSize === "full" ? "field--full" : `field--${expected.fieldSize}`;
    assert(String(evidence.dom?.fieldClass || "").includes(expectedClass), "办理页 DOM 字段尺寸不符合预期", {
      stage,
      expectedClass,
      evidence,
    });
  }
  return evidence;
}

async function runLayoutSample(browser, sample, sampleIndex) {
  applyLayoutSample(sample);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: "zh-CN" });
  const report = {
    ok: false,
    sampleIndex,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    model: MODEL,
    actionId: ACTION_ID,
    pageLabel: PAGE_LABEL,
    field: FIELD_NAME,
    homeGroup: HOME_GROUP,
    checks: {},
  };
  let baselinePageColumns = 3;
  let baselineGroupColumns = 3;
  let baselineFieldSize = "normal";
  let baselineReady = false;
  async function restoreBaseline(reason) {
    if (!baselineReady) return { skipped: true, reason: "baseline-not-ready" };
    await patchSavedContract(page, (contractJson) => {
      mutateFormSpec(contractJson, (formSpec) => {
        formSpec.columns = baselinePageColumns;
        for (const section of Array.isArray(formSpec.sections) ? formSpec.sections : []) {
          if (!section || typeof section !== "object") continue;
          section.visible = true;
          const title = String(section.title || section.label || section.name || "");
          const fields = Array.isArray(section.fields) ? section.fields.map((item) => String(item || "").trim()).filter(Boolean) : [];
          section.fields = fields.filter((name) => name !== FIELD_NAME);
          if (title === HOME_GROUP && !section.fields.includes(FIELD_NAME)) section.fields.push(FIELD_NAME);
          section.columns = String(section.title || section.label || section.name || "") === HOME_GROUP
            ? baselineGroupColumns
            : baselinePageColumns;
        }
        let fieldLayoutNode = null;
        for (const group of Array.isArray(formSpec.layout) ? formSpec.layout : []) {
          if (!group || typeof group !== "object") continue;
          const title = String(group.string || group.label || group.title || group.name || "");
          group.visible = true;
          group.columns = title === HOME_GROUP ? baselineGroupColumns : baselinePageColumns;
          group.cols = title === HOME_GROUP ? baselineGroupColumns : baselinePageColumns;
          const children = Array.isArray(group.children) ? group.children : [];
          group.children = children.filter((child) => {
            if (child && typeof child === "object" && String(child.name || child.field || "") === FIELD_NAME) {
              fieldLayoutNode = child;
              return false;
            }
            return true;
          });
          for (const child of children) {
            if (child && typeof child === "object" && String(child.name || child.field || "") === FIELD_NAME) {
              if (baselineFieldSize === "normal") {
                delete child.field_size;
                delete child.fieldSize;
                delete child.class;
              } else {
                child.field_size = baselineFieldSize;
                child.class = baselineFieldSize === "full" ? "field--full" : `field--${baselineFieldSize}`;
              }
            }
          }
        }
        if (!fieldLayoutNode) fieldLayoutNode = { type: "field", name: FIELD_NAME };
        if (baselineFieldSize === "normal") {
          delete fieldLayoutNode.field_size;
          delete fieldLayoutNode.fieldSize;
          delete fieldLayoutNode.class;
        } else {
          fieldLayoutNode.field_size = baselineFieldSize;
          fieldLayoutNode.class = baselineFieldSize === "full" ? "field--full" : `field--${baselineFieldSize}`;
        }
        const homeGroup = (Array.isArray(formSpec.layout) ? formSpec.layout : []).find((group) => (
          group && typeof group === "object" && String(group.string || group.label || group.title || group.name || "") === HOME_GROUP
        )) || ensureLayoutGroup(formSpec, HOME_GROUP, baselineGroupColumns || baselinePageColumns);
        const children = Array.isArray(homeGroup.children) ? homeGroup.children : [];
        if (!children.some((child) => child && typeof child === "object" && String(child.name || child.field || "") === FIELD_NAME)) {
          children.push(fieldLayoutNode);
        }
        homeGroup.children = children;
        const homeSection = ensureSection(formSpec, HOME_GROUP, baselineGroupColumns || baselinePageColumns);
        homeSection.fields = (Array.isArray(homeSection.fields) ? homeSection.fields : []).filter((name) => name !== FIELD_NAME);
        homeSection.fields.push(FIELD_NAME);
        for (const field of Array.isArray(formSpec.fields) ? formSpec.fields : []) {
          if (!field || typeof field !== "object") continue;
          field.visible = true;
          if (String(field.name || field.field || "") === FIELD_NAME) {
            field.group_title = HOME_GROUP;
            if (baselineFieldSize === "normal") {
              delete field.field_size;
              delete field.fieldSize;
              delete field.class;
            } else {
              field.field_size = baselineFieldSize;
              field.class = baselineFieldSize === "full" ? "field--full" : `field--${baselineFieldSize}`;
            }
          }
        }
      });
    }, `${reason}:restore-contract`);
    return { ok: true, baselinePageColumns, baselineGroupColumns, baselineFieldSize };
  }
  try {
    await login(page);
    await ensureProbeFieldVisibleByContract(page);
    await ensureFieldInGroup(page, HOME_GROUP, "baseline");

    await openFormDesigner(page);
    report.field = FIELD_NAME;
    baselinePageColumns = normalizeColumns(await page.locator(".contract-form-layout-tools select").first().inputValue(), 3);
    await selectField(page);
    baselineGroupColumns = normalizeColumns(await page.locator(".contract-field-selection-card .contract-field-group-columns select").first().inputValue(), baselinePageColumns);
    baselineFieldSize = String(await page.locator(".contract-field-selection-card .contract-field-size-control select").first().inputValue() || "normal");
    baselineReady = true;
    if (baselineGroupColumns !== baselinePageColumns) {
      await setSelectedGroupColumns(page, baselinePageColumns, "page-columns-setup-clear-group-override");
    }

    const targetPageColumns = alternateColumns(baselinePageColumns);
    await setPageColumns(page, targetPageColumns, "page-columns");
    report.checks.pageColumns = await assertRuntimeLayout(page, {
      groupTitle: HOME_GROUP,
      groupColumns: targetPageColumns,
    }, "page-columns");

    await openFormDesigner(page);
    await setSelectedGroupColumns(page, 1, "group-columns");
    report.checks.groupColumns = await assertRuntimeLayout(page, {
      groupTitle: HOME_GROUP,
      groupColumns: 1,
    }, "group-columns");

    await openFormDesigner(page);
    await setSelectedFieldSize(page, "full", "field-size");
    report.checks.fieldSize = await assertRuntimeLayout(page, {
      groupTitle: HOME_GROUP,
      groupColumns: 1,
      fieldSize: "full",
    }, "field-size");

    await openFormDesigner(page);
    await setSelectedGroupVisibility(page, false, "group-hide");
    report.checks.groupHidden = await assertRuntimeLayout(page, { fieldVisible: false }, "group-hide");
    await setGroupVisibilityByContract(page, HOME_GROUP, true, "group-show");
    report.checks.groupRestored = await assertRuntimeLayout(page, {
      groupTitle: HOME_GROUP,
    }, "group-show");

    report.checks.restoreOperation = await restoreBaseline("final");
    report.checks.restored = await assertRuntimeLayout(page, {
      groupTitle: HOME_GROUP,
      groupColumns: baselineGroupColumns,
    }, "restore");

    report.ok = true;
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.ok = false;
    report.failure = {
      message: error?.message || String(error),
      details: error?.details || {},
    };
    try {
      report.restoreAfterFailure = await restoreBaseline("failure");
    } catch (restoreError) {
      report.restoreAfterFailure = {
        ok: false,
        message: restoreError?.message || String(restoreError),
        details: restoreError?.details || {},
      };
    }
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 2;
  } finally {
    await page.close();
  }
  return report;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const samples = layoutSamples();
  const aggregate = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    sampleCount: samples.length,
    samples: [],
  };
  try {
    for (let index = 0; index < samples.length; index += 1) {
      const report = await runLayoutSample(browser, samples[index], index);
      aggregate.samples.push(report);
      if (!report.ok) process.exitCode = 2;
    }
    aggregate.ok = aggregate.samples.length === samples.length && aggregate.samples.every((report) => report.ok);
    if (!aggregate.ok) process.exitCode = 2;
    console.log(JSON.stringify(aggregate, null, 2));
  } finally {
    await browser.close();
  }
}

await main();
