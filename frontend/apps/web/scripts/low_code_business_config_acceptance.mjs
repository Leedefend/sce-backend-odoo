import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://localhost:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const CONFIG_MODEL = "construction.contract";
const CONFIG_ACTION_ID = 562;

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "low-code-business-config");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");

const CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=${encodeURIComponent(CONFIG_MODEL)}&action_id=${CONFIG_ACTION_ID}&page_label=${encodeURIComponent("项目合同汇总")}&open_pages=1`;
const LIST_SEARCH_URL = `${CONFIG_URL}&open_list_search=1`;
const ANALYSIS_MODEL = process.env.LOW_CODE_ANALYSIS_MODEL || "sc.account.income.expense.summary";
const ANALYSIS_ACTION_ID = process.env.LOW_CODE_ANALYSIS_ACTION_ID || "681";
const ANALYSIS_MENU_ID = process.env.LOW_CODE_ANALYSIS_MENU_ID || "372";
const ANALYSIS_PAGE_LABEL = process.env.LOW_CODE_ANALYSIS_PAGE_LABEL || "账户收支统计表";
const ANALYSIS_CONFIG_URL = `${BASE_URL}/admin/business-config?root_menu_xmlid=smart_construction_core.menu_sc_root&db=${encodeURIComponent(DB_NAME)}&model=${encodeURIComponent(ANALYSIS_MODEL)}&action_id=${encodeURIComponent(ANALYSIS_ACTION_ID)}&menu_id=${encodeURIComponent(ANALYSIS_MENU_ID)}&page_label=${encodeURIComponent(ANALYSIS_PAGE_LABEL)}&open_pages=1`;
const DEFAULT_UI_FORBIDDEN_TERMS = ["已有个人配置", "个人偏好", "契约", "缺口", "治理", "边界", "legacy policy"];
const ADVANCED_UI_FORBIDDEN_TERMS = [
  ...DEFAULT_UI_FORBIDDEN_TERMS,
  "industry_policy_runtime",
  "business_contract",
  "ui_only",
  "user_preference_boundary",
];
const LOW_CODE_BOUNDARY_SCAN_ROOTS = [
  "frontend/apps/web/src",
  "addons/smart_core",
  "addons/smart_construction_core",
];
const LOW_CODE_BOUNDARY_SCAN_EXTENSIONS = new Set([".mjs", ".py", ".ts", ".vue"]);
const LOW_CODE_BOUNDARY_MIN_CHECKED_FILES = 800;
const LOW_CODE_BOUNDARY_MIN_FILES_BY_ROOT = {
  "frontend/apps/web/src": 250,
  "addons/smart_core": 240,
  "addons/smart_construction_core": 300,
};
const LOW_CODE_BOUNDARY_EXCLUDED_SEGMENTS = new Set([
  "__pycache__",
  "data",
  "dist",
  "node_modules",
  "tests",
  "views",
]);
const LOW_CODE_BOUNDARY_ALLOW_FILES = new Set([
  "frontend/apps/web/src/app/businessConfigBoundaries.ts",
  "addons/smart_core/utils/backend_contract_boundaries.py",
]);
const FRONTEND_BOUNDARY_FILE = "frontend/apps/web/src/app/businessConfigBoundaries.ts";
const BACKEND_BOUNDARY_FILE = "addons/smart_core/utils/backend_contract_boundaries.py";
const LOW_CODE_LEGACY_WRITE_GUARD_FILES = [
  "frontend/apps/web/src/pages/ContractFormPage.vue",
  "frontend/apps/web/scripts/low_code_business_config_acceptance.mjs",
];

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

async function discoverLowCodeBoundaryFiles() {
  const out = [];
  async function walk(relativeDir) {
    const absoluteDir = path.join(ROOT_DIR, relativeDir);
    let entries = [];
    try {
      entries = await fs.readdir(absoluteDir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const relativePath = path.join(relativeDir, entry.name).split(path.sep).join("/");
      if (entry.isDirectory()) {
        if (LOW_CODE_BOUNDARY_EXCLUDED_SEGMENTS.has(entry.name)) continue;
        await walk(relativePath);
        continue;
      }
      if (!entry.isFile()) continue;
      if (!LOW_CODE_BOUNDARY_SCAN_EXTENSIONS.has(path.extname(entry.name))) continue;
      out.push(relativePath);
    }
  }
  for (const root of LOW_CODE_BOUNDARY_SCAN_ROOTS) {
    await walk(root);
  }
  return out.sort();
}

function classifyLowCodeBoundaryLeak(value, relativePath) {
  const text = String(value || "");
  if (relativePath.startsWith("frontend/apps/web/src/") && /ui\.(?:business\.config\.contract|form\.field\.policy|form\.custom\.field\.wizard|menu\.config\.policy)|sc\.approval\.policy/.test(text)) {
    return "frontend_model_name";
  }
  if (/^ui\.(?:business_config|menu_config|form_field_policy|form_custom_field)|^sc\.approval_policy/.test(text)) {
    return "intent_or_route_key";
  }
  if (/^smart_core\.nav\./.test(text)) {
    return "runtime_param";
  }
  if (/^current_form_/.test(text)) {
    return "form_action_key";
  }
  if (/business_config_lowcode|form_field_configuration|return_to_business_config/.test(text)) {
    return "route_or_mode_flag";
  }
  if (/ui\.business\.config\.contract\.menu_orchestration|ui\.menu\.config\.policy/.test(text)) {
    return "runtime_source_or_model";
  }
  return "boundary_constant";
}

async function auditLowCodeBoundaryConstants() {
  const leaked = [];
  const pattern = /(?:ui\.(?:business_config|menu_config|form_field_policy|form_custom_field)|sc\.approval_policy)\.[a-zA-Z0-9_.]+|ui\.menu\.config\.policy|ui\.business\.config\.contract\.menu_orchestration|smart_core\.nav\.(?:user_menu_config(?:\.config_only)?\.enabled|user_data_acceptance_only)|current_form_(?:field_settings|add_custom_field|field_order_save|field_configuration)|["'](?:business_config_lowcode|form_field_configuration|return_to_business_config)["']/g;
  const frontendModelPattern = /ui\.(?:business\.config\.contract|form\.field\.policy|form\.custom\.field\.wizard|menu\.config\.policy)|sc\.approval\.policy/g;
  const files = await discoverLowCodeBoundaryFiles();
  const checkedFilesByRoot = Object.fromEntries(LOW_CODE_BOUNDARY_SCAN_ROOTS.map((root) => [root, 0]));
  for (const relativePath of files) {
    const root = LOW_CODE_BOUNDARY_SCAN_ROOTS.find((candidate) => relativePath.startsWith(`${candidate}/`));
    if (root) checkedFilesByRoot[root] = (checkedFilesByRoot[root] || 0) + 1;
    if (LOW_CODE_BOUNDARY_ALLOW_FILES.has(relativePath)) continue;
    const absolutePath = path.join(ROOT_DIR, relativePath);
    const text = await fs.readFile(absolutePath, "utf8");
    const lines = text.split(/\r?\n/);
    lines.forEach((line, index) => {
      const categorizedMatches = [];
      (line.match(pattern) || []).forEach((match) => {
        categorizedMatches.push({ value: match, kind: classifyLowCodeBoundaryLeak(match, relativePath) });
      });
      if (relativePath.startsWith("frontend/apps/web/src/")) {
        (line.match(frontendModelPattern) || []).forEach((match) => {
          categorizedMatches.push({ value: match, kind: "frontend_model_name" });
        });
      }
      const seen = new Set();
      categorizedMatches.forEach((match) => {
        const key = `${match.kind}:${match.value}`;
        if (seen.has(key)) return;
        seen.add(key);
        leaked.push({ path: relativePath, line: index + 1, kind: match.kind, value: match.value });
      });
    });
  }
  return {
    checkedFiles: files.length,
    minCheckedFiles: LOW_CODE_BOUNDARY_MIN_CHECKED_FILES,
    checkedFilesByRoot,
    minFilesByRoot: LOW_CODE_BOUNDARY_MIN_FILES_BY_ROOT,
    scanRoots: LOW_CODE_BOUNDARY_SCAN_ROOTS,
    allowedFiles: Array.from(LOW_CODE_BOUNDARY_ALLOW_FILES),
    leaked,
  };
}

async function auditLowCodeLegacyWritePaths() {
  const leaked = [];
  for (const relativePath of LOW_CODE_LEGACY_WRITE_GUARD_FILES) {
    const absolutePath = path.join(ROOT_DIR, relativePath);
    const text = await fs.readFile(absolutePath, "utf8");
    text.split(/\r?\n/).forEach((line, index) => {
      if (/^\s*legacy_lowcode_draft\s*:/.test(line)) {
        leaked.push({ path: relativePath, line: index + 1 });
      }
    });
  }
  return {
    checkedFiles: LOW_CODE_LEGACY_WRITE_GUARD_FILES.length,
    leaked,
  };
}

function uniqueSorted(values) {
  return Array.from(new Set(values.map((value) => String(value || "").trim()).filter(Boolean))).sort();
}

function extractJavaScriptConstantValues(source) {
  return Object.fromEntries(Array.from(source.matchAll(/export\s+const\s+([A-Z0-9_]+)\s*=\s*['"]([^'"]+)['"]\s*;/g)).map((item) => [item[1], item[2]]));
}

function extractObjectStringValues(source, objectName) {
  const match = source.match(new RegExp(`(?:export\\s+)?const\\s+${objectName}\\s*=\\s*\\{([\\s\\S]*?)\\}\\s*(?:as\\s+const)?\\s*;`));
  if (!match) return [];
  const constants = extractJavaScriptConstantValues(source);
  return uniqueSorted(match[1].split(/\r?\n/).flatMap((line) => {
    const literal = line.match(/:\s*['"]([^'"]+)['"]/);
    if (literal) return [literal[1]];
    const identifier = line.match(/:\s*([A-Z0-9_]+)\s*,?/);
    if (identifier && constants[identifier[1]]) return [constants[identifier[1]]];
    return [];
  }));
}

function extractPythonSetValues(source, objectName) {
  const match = source.match(new RegExp(`${objectName}\\s*=\\s*\\{([\\s\\S]*?)\\}\\s*(?:\\n[A-Z_]+\\s*=|\\ndef\\s+|\\n\\n)`, "m"));
  if (!match) return [];
  return uniqueSorted(Array.from(match[1].matchAll(/["']([^"']+)["']/g)).map((item) => item[1]));
}

function extractPythonDictValues(source, objectName) {
  const match = source.match(new RegExp(`${objectName}\\s*=\\s*\\{([\\s\\S]*?)\\}\\s*(?:\\n[A-Z_]+\\s*=|\\ndef\\s+|\\n\\n)`, "m"));
  if (!match) return [];
  return uniqueSorted(match[1].split(/\r?\n/).flatMap((line) => {
    const literal = line.match(/:\s*["']([^"']+)["']/);
    return literal ? [literal[1]] : [];
  }));
}

function extractPythonConstantValues(source, names) {
  return uniqueSorted(names.flatMap((name) => {
    const match = source.match(new RegExp(`${name}\\s*=\\s*["']([^"']+)["']`));
    return match ? [match[1]] : [];
  }));
}

function compareValueSets(name, frontendValues, backendValues) {
  const frontend = uniqueSorted(frontendValues);
  const backend = uniqueSorted(backendValues);
  const frontendSet = new Set(frontend);
  const backendSet = new Set(backend);
  return {
    name,
    frontendCount: frontend.length,
    backendCount: backend.length,
    missingFrontend: backend.filter((value) => !frontendSet.has(value)),
    missingBackend: frontend.filter((value) => !backendSet.has(value)),
  };
}

async function auditLowCodeBoundaryParity() {
  const frontend = await fs.readFile(path.join(ROOT_DIR, FRONTEND_BOUNDARY_FILE), "utf8");
  const backend = await fs.readFile(path.join(ROOT_DIR, BACKEND_BOUNDARY_FILE), "utf8");
  const comparisons = [
    compareValueSets(
      "business_config_runtime_models",
      extractObjectStringValues(frontend, "BUSINESS_CONFIG_MODELS"),
      extractPythonSetValues(backend, "BUSINESS_CONFIG_RUNTIME_MODELS"),
    ),
    compareValueSets(
      "business_config_modes",
      extractObjectStringValues(frontend, "BUSINESS_CONFIG_MODES"),
      extractPythonDictValues(backend, "BUSINESS_CONFIG_MODES"),
    ),
    compareValueSets(
      "business_config_action_keys",
      extractObjectStringValues(frontend, "BUSINESS_CONFIG_ACTION_KEYS"),
      extractPythonDictValues(backend, "BUSINESS_CONFIG_ACTION_KEYS"),
    ),
    compareValueSets(
      "business_config_intents",
      extractObjectStringValues(frontend, "BUSINESS_CONFIG_INTENTS"),
      extractPythonDictValues(backend, "BUSINESS_CONFIG_INTENTS"),
    ),
    compareValueSets(
      "form_field_config_intents",
      extractObjectStringValues(frontend, "FORM_FIELD_CONFIG_INTENTS"),
      extractPythonDictValues(backend, "FORM_FIELD_CONFIG_INTENTS"),
    ),
    compareValueSets(
      "menu_config_intents",
      extractObjectStringValues(frontend, "MENU_CONFIG_INTENTS"),
      extractPythonDictValues(backend, "MENU_CONFIG_INTENTS"),
    ),
    compareValueSets(
      "menu_config_runtime_sources",
      extractObjectStringValues(frontend, "MENU_CONFIG_RUNTIME_SOURCES"),
      extractPythonConstantValues(backend, ["MENU_CONFIG_RUNTIME_SOURCE_POLICY", "MENU_CONFIG_RUNTIME_SOURCE_CONTRACT"]),
    ),
    compareValueSets(
      "approval_policy_intents",
      extractObjectStringValues(frontend, "APPROVAL_POLICY_INTENTS"),
      extractPythonDictValues(backend, "APPROVAL_POLICY_INTENTS"),
    ),
  ];
  return {
    frontendFile: FRONTEND_BOUNDARY_FILE,
    backendFile: BACKEND_BOUNDARY_FILE,
    comparisons,
    mismatches: comparisons.filter((item) => item.missingFrontend.length || item.missingBackend.length),
  };
}

async function visibleForbiddenTerms(page, selector = "body") {
  const text = await page.locator(selector).innerText();
  return DEFAULT_UI_FORBIDDEN_TERMS.filter((term) => text.includes(term));
}

async function visibleAdvancedForbiddenTerms(page, selector = "body") {
  const text = await page.locator(selector).innerText();
  return ADVANCED_UI_FORBIDDEN_TERMS.filter((term) => text.includes(term));
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

async function readToken(page) {
  return page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith("sc_auth_token")) || "";
    return key ? sessionStorage.getItem(key) : "";
  });
}

async function browserIntent(page, intentName, params = {}) {
  const token = await readToken(page);
  return page.evaluate(async ({ dbName, token, intentName, params }) => {
    const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Odoo-DB": dbName,
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true } }),
    });
    const body = await res.json();
    if (!res.ok || body.ok === false) {
      throw new Error(JSON.stringify(body.error || body).slice(0, 700));
    }
    return body.data || body;
  }, { dbName: DB_NAME, token, intentName, params });
}

async function browserIntentEnvelope(page, intentName, params = {}) {
  const token = await readToken(page);
  return page.evaluate(async ({ dbName, token, intentName, params }) => {
    const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Odoo-DB": dbName,
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true } }),
    });
    const body = await res.json();
    if (!res.ok || body.ok === false) {
      throw new Error(JSON.stringify(body.error || body).slice(0, 700));
    }
    return body;
  }, { dbName: DB_NAME, token, intentName, params });
}

function collectContractFieldRows(nodes, out = [], seen = new Set()) {
  for (const node of nodes || []) {
    if (!node || typeof node !== "object") continue;
    const type = String(node.type || node.containerType || "").trim().toLowerCase();
    const name = String(node.name || "").trim();
    if (type === "field" && name && !seen.has(name)) {
      seen.add(name);
      out.push({
        name,
        label: String(node.string || node.label || name).trim() || name,
      });
    }
    for (const key of ["children", "pages", "tabs", "nodes", "items"]) {
      if (Array.isArray(node[key])) collectContractFieldRows(node[key], out, seen);
    }
  }
  return out;
}

function groupedViewOrchestration(fieldRows) {
  const firstGroup = fieldRows.slice(0, 3);
  const secondGroup = fieldRows.slice(3);
  const groupTitle = (index) => (index < 3 ? "验收分组A" : "验收分组B");
  return {
    views: {
      form: {
        fields: fieldRows.map((field, index) => ({
          name: field.name,
          label: field.label,
          visible: true,
          sequence: (index + 1) * 10,
          group_title: groupTitle(index),
        })),
        sections: [
          { name: "acceptance_group_a", title: "验收分组A", sequence: 10, fields: firstGroup.map((field) => field.name) },
          { name: "acceptance_group_b", title: "验收分组B", sequence: 20, fields: secondGroup.map((field) => field.name) },
        ],
        layout: [
          { type: "group", string: "验收分组A", children: firstGroup.map((field) => ({ type: "field", name: field.name })) },
          { type: "group", string: "验收分组B", children: secondGroup.map((field) => ({ type: "field", name: field.name })) },
        ],
      },
    },
  };
}

async function collectDesignerFieldRows(page) {
  return page.locator(".field--selectable").evaluateAll((nodes) => {
    const seen = new Set();
    return nodes.map((node) => {
      const name = String(node.getAttribute("data-field-name") || node.getAttribute("data-field-key") || "").trim();
      const text = node.textContent?.replace(/\s+/g, " ").trim() || "";
      const label = text.split("⋮⋮")[0].split("↑")[0].trim() || name;
      return { name, label };
    }).filter((field) => {
      if (!field.name || seen.has(field.name)) return false;
      seen.add(field.name);
      return true;
    });
  });
}

async function ensureCrossGroupDesignerBaseline(page) {
  const contractData = await browserIntent(page, "ui.contract.v2", {
    model: CONFIG_MODEL,
    action_id: CONFIG_ACTION_ID,
    view_type: "form",
  });
  const contractRows = collectContractFieldRows(contractData?.layoutContract?.containerTree || []);
  const designerRows = contractRows.length >= 4 ? [] : await collectDesignerFieldRows(page);
  const fieldRows = contractRows.length >= 4 ? contractRows : designerRows;
  if (fieldRows.length < 4) {
    return {
      prepared: false,
      fieldCount: fieldRows.length,
      contractFieldCount: contractRows.length,
      designerFieldCount: designerRows.length,
    };
  }
  await browserIntent(page, "ui.business_config.contract.save", {
    name: `view_orchestration:${CONFIG_MODEL}:form:action:${CONFIG_ACTION_ID}:view:0`,
    model: CONFIG_MODEL,
    view_type: "form",
    action_id: CONFIG_ACTION_ID,
    view_id: 0,
    publish: true,
    contract_json: {
      view_orchestration: groupedViewOrchestration(fieldRows),
    },
  });
  return {
    prepared: true,
    fieldCount: fieldRows.length,
    contractFieldCount: contractRows.length,
    designerFieldCount: designerRows.length,
  };
}

async function formDesignerFieldTexts(page) {
  return page.locator(".field--selectable").evaluateAll((nodes) => (
    nodes.map((node) => {
      const editorValue = node.querySelector(".field-label-editor")?.value?.trim() || "";
      if (editorValue) return editorValue;
      const text = node.textContent?.replace(/\s+/g, " ").trim() || "";
      return text.split("⋮⋮")[0].split("↑")[0].trim();
    }).filter(Boolean)
  ));
}

async function dragDesignerField(page, fromIndex, toIndex) {
  const source = page.locator(".field--selectable").nth(fromIndex);
  const target = page.locator(".field--selectable").nth(toIndex);
  await source.scrollIntoViewIfNeeded();
  await target.scrollIntoViewIfNeeded();
  const targetBox = await target.boundingBox();
  const targetPosition = targetBox
    ? {
      x: Math.max(2, Math.round(targetBox.width / 2)),
      y: fromIndex < toIndex ? Math.max(2, Math.round(targetBox.height - 2)) : 2,
    }
    : undefined;
  await source.dragTo(target, targetPosition ? { targetPosition } : undefined);
}

async function probeDesignerFieldDragAutoScroll(page) {
  const source = page.locator(".field--selectable").first();
  await source.waitFor({ timeout: 10000 });
  await source.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.scrollTo(0, 0));
  const beforeScrollY = await page.evaluate(() => window.scrollY);
  const result = await source.evaluate(async (node) => {
    const fieldKey = node.getAttribute("data-field-key") || node.getAttribute("data-field-name") || "";
    if (!fieldKey) return { fieldKey, before: window.scrollY, after: window.scrollY };
    const dataTransfer = new DataTransfer();
    node.dispatchEvent(new DragEvent("dragstart", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.round(window.innerHeight / 2),
    }));
    window.dispatchEvent(new DragEvent("dragover", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.max(1, window.innerHeight - 2),
    }));
    await new Promise((resolve) => window.setTimeout(resolve, 420));
    const after = window.scrollY;
    window.dispatchEvent(new DragEvent("dragend", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.max(1, window.innerHeight - 2),
    }));
    return { fieldKey, before: 0, after };
  });
  await page.waitForTimeout(100);
  const dirtyAfterProbe = await page.locator(".contract-field-governance-dirty").count();
  return {
    fieldKey: result.fieldKey,
    beforeScrollY,
    afterScrollY: result.after,
    dirtyAfterProbe,
  };
}

async function probeDesignerFieldDropPlacement(page) {
  const fields = page.locator(".field--selectable");
  const fieldCount = await fields.count();
  if (fieldCount < 2) {
    return {
      fieldCount,
      beforeClassVisible: false,
      afterClassVisible: false,
      dirtyAfterProbe: await page.locator(".contract-field-governance-dirty").count(),
    };
  }
  const source = fields.nth(0);
  const target = fields.nth(1);
  await source.scrollIntoViewIfNeeded();
  await target.scrollIntoViewIfNeeded();
  const result = await target.evaluate(async (targetNode) => {
    const sourceNode = document.querySelector(".field--selectable");
    if (!sourceNode || !targetNode) {
      return { beforeClassVisible: false, afterClassVisible: false };
    }
    const sourceRect = sourceNode.getBoundingClientRect();
    const targetRect = targetNode.getBoundingClientRect();
    const dataTransfer = new DataTransfer();
    sourceNode.dispatchEvent(new DragEvent("dragstart", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.round(sourceRect.top + sourceRect.height / 2),
    }));
    targetNode.dispatchEvent(new DragEvent("dragover", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.round(targetRect.top + Math.max(2, targetRect.height * 0.2)),
    }));
    await new Promise((resolve) => requestAnimationFrame(resolve));
    const beforeClassVisible = targetNode.classList.contains("field--order-drop-before")
      && !targetNode.classList.contains("field--order-drop-after");
    targetNode.dispatchEvent(new DragEvent("dragover", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.round(targetRect.bottom - Math.max(2, targetRect.height * 0.2)),
    }));
    await new Promise((resolve) => requestAnimationFrame(resolve));
    const afterClassVisible = targetNode.classList.contains("field--order-drop-after")
      && !targetNode.classList.contains("field--order-drop-before");
    sourceNode.dispatchEvent(new DragEvent("dragend", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientY: Math.round(sourceRect.top + sourceRect.height / 2),
    }));
    return { beforeClassVisible, afterClassVisible };
  });
  await page.waitForTimeout(100);
  return {
    fieldCount,
    beforeClassVisible: result.beforeClassVisible,
    afterClassVisible: result.afterClassVisible,
    dirtyAfterProbe: await page.locator(".contract-field-governance-dirty").count(),
  };
}

async function formDesignerFieldGroups(page) {
  return page.locator(".native-container--group").evaluateAll((nodes) => (
    nodes.map((node, groupIndex) => {
      const stableTitle = node.getAttribute("data-group-title")?.trim() || "";
      const visibleTitle = node.querySelector(":scope > .native-container-head")?.textContent?.replace(/\+/g, " ").replace(/\s+/g, " ").trim() || "";
      const sectionTitle = node.querySelector(".template-form-section-title")?.textContent?.trim() || "";
      const title = stableTitle || visibleTitle || sectionTitle || `默认分组 ${groupIndex + 1}`;
      const fields = Array.from(node.querySelectorAll(".field--selectable"))
        .filter((fieldNode) => fieldNode.closest(".native-container--group") === node)
        .map((fieldNode) => {
          const allFields = Array.from(document.querySelectorAll(".field--selectable"));
          const editorValue = fieldNode.querySelector(".field-label-editor")?.value?.trim() || "";
          const text = fieldNode.textContent?.replace(/\s+/g, " ").trim() || "";
          return {
            index: allFields.indexOf(fieldNode),
            label: editorValue || text.split("⋮⋮")[0].split("↑")[0].trim(),
          };
        })
        .filter((field) => field.index >= 0 && field.label);
      return { groupIndex, title, fields };
    }).filter((group) => group.title && group.fields.length)
  ));
}

async function dragDesignerFieldToGroup(page, fromFieldIndex, targetGroupIndex) {
  const source = page.locator(".field--selectable").nth(fromFieldIndex);
  const targetGroup = page.locator(".native-container--group").nth(targetGroupIndex);
  const targetField = targetGroup.locator(".field--selectable").first();
  const targetHead = targetGroup.locator(":scope > .native-container-head").first();
  const targetStrip = targetGroup.locator(':scope > [data-drop-zone="field-group"]').first();
  const target = await targetField.count()
    ? targetField
    : (await targetHead.count()
      ? targetHead
      : (await targetStrip.count() ? targetStrip : targetGroup));
  await source.scrollIntoViewIfNeeded();
  await target.scrollIntoViewIfNeeded();
  await source.dragTo(target);
}

async function approvalStepNames(page) {
  return page.locator(".approval-step-row input[type='text']").evaluateAll((nodes) => (
    nodes.map((node) => node.value || "")
  ));
}

async function dragApprovalStep(page, fromIndex, toIndex) {
  const source = page.locator(".approval-step-row").nth(fromIndex);
  const target = page.locator(".approval-step-row").nth(toIndex);
  await source.scrollIntoViewIfNeeded();
  await target.scrollIntoViewIfNeeded();
  const targetNameBefore = await target.locator("input[type='text']").inputValue();
  const targetBox = await target.boundingBox();
  const targetPosition = targetBox
    ? {
      x: Math.max(2, Math.round(targetBox.width / 2)),
      y: fromIndex < toIndex ? Math.max(2, Math.round(targetBox.height - 2)) : 2,
    }
    : undefined;
  await source.dragTo(target, targetPosition ? { targetPosition } : undefined);
  await page.waitForTimeout(250);
  const firstNameAfterDragTo = await page.locator(".approval-step-row").nth(fromIndex).locator("input[type='text']").inputValue();
  if (firstNameAfterDragTo === targetNameBefore) return;

  await page.evaluate(({ fromIndex, toIndex }) => {
    const rows = Array.from(document.querySelectorAll(".approval-step-row"));
    const sourceNode = rows[fromIndex];
    const targetNode = rows[toIndex];
    if (!sourceNode || !targetNode) return;
    const sourceRect = sourceNode.getBoundingClientRect();
    const targetRect = targetNode.getBoundingClientRect();
    const dataTransfer = new DataTransfer();
    sourceNode.dispatchEvent(new DragEvent("dragstart", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientX: Math.round(sourceRect.left + sourceRect.width / 2),
      clientY: Math.round(sourceRect.top + sourceRect.height / 2),
    }));
    targetNode.dispatchEvent(new DragEvent("dragenter", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientX: Math.round(targetRect.left + targetRect.width / 2),
      clientY: Math.round(targetRect.bottom - 2),
    }));
    targetNode.dispatchEvent(new DragEvent("dragover", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientX: Math.round(targetRect.left + targetRect.width / 2),
      clientY: Math.round(targetRect.bottom - 2),
    }));
    targetNode.dispatchEvent(new DragEvent("drop", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientX: Math.round(targetRect.left + targetRect.width / 2),
      clientY: Math.round(targetRect.bottom - 2),
    }));
    sourceNode.dispatchEvent(new DragEvent("dragend", {
      bubbles: true,
      cancelable: true,
      dataTransfer,
      clientX: Math.round(sourceRect.left + sourceRect.width / 2),
      clientY: Math.round(sourceRect.top + sourceRect.height / 2),
    }));
  }, { fromIndex, toIndex });
}

async function selectDesignerField(page, index = 0) {
  const fields = page.locator(".field--selectable");
  await fields.nth(index).waitFor({ timeout: 10000 });
  await fields.nth(index).scrollIntoViewIfNeeded();
  await fields.nth(index).evaluate((field) => {
    field.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  });
  await page.waitForFunction((targetIndex) => {
    const selected = document.querySelector(".contract-field-selection-card");
    const selectedCount = document.querySelectorAll(".field--selected").length;
    const selectableCount = document.querySelectorAll(".field--selectable").length;
    return Boolean(selected) && selectedCount > 0 && selectableCount > targetIndex;
  }, index, { timeout: 10000 });
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

async function clickButtonByProductAliases(scope, names) {
  for (const name of names) {
    const button = scope.getByRole("button", { name });
    if (await button.count()) {
      await button.first().click();
      return name;
    }
  }
  throw new Error(`expected one of buttons: ${names.join(", ")}`);
}

async function main() {
  await ensureDirs();
  const boundaryConstants = await auditLowCodeBoundaryConstants();
  const boundaryParity = await auditLowCodeBoundaryParity();
  const legacyWritePaths = await auditLowCodeLegacyWritePaths();
  assert(
    boundaryConstants.checkedFiles >= LOW_CODE_BOUNDARY_MIN_CHECKED_FILES,
    "低代码边界扫描覆盖文件数异常偏低",
    boundaryConstants,
  );
  Object.entries(LOW_CODE_BOUNDARY_MIN_FILES_BY_ROOT).forEach(([root, minFiles]) => {
    assert(
      Number(boundaryConstants.checkedFilesByRoot?.[root] || 0) >= Number(minFiles || 0),
      `低代码边界扫描根目录覆盖文件数异常偏低：${root}`,
      boundaryConstants,
    );
  });
  assert(
    boundaryConstants.leaked.length === 0,
    "低代码边界常量散落在页面、API 或 handler 中",
    boundaryConstants,
  );
  assert(
    boundaryParity.mismatches.length === 0,
    "低代码前后端边界契约常量不一致",
    boundaryParity,
  );
  assert(
    legacyWritePaths.leaked.length === 0,
    "低代码保存路径仍在写 legacy_lowcode_draft",
    legacyWritePaths,
  );
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  let currentStep = "start";
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
    checks: {
      boundaryConstants,
      boundaryParity,
      legacyWritePaths,
    },
    artifacts: {},
    errors,
    warnings,
  };

  try {
    currentStep = "login";
    await login(page);

    currentStep = "open default config page";
    await page.goto(CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const defaultCards = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const configWorkspaceCount = await page.locator(".config-workspace").count();
    const pagePickerPanelCount = await page.locator(".config-workspace .page-picker-panel").count();
    const pageConfigPanelCount = await page.locator(".config-workspace .page-config-panel").count();
    const pagePickerHeadText = await page.locator(".page-picker-head").innerText();
    const selectedOverviewText = await page.locator(".selected-page-overview").innerText();
    const defaultSelectedRowActionLabels = await page.locator(".scan-row--selected .scan-row-actions button").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const defaultSelectedRowCurrentText = await page.locator(".scan-row--selected .scan-row-current").innerText();
    const defaultNonSelectedChooseButtonCount = await page.locator(".scan-row:not(.scan-row--selected) .scan-row-actions button").filter({ hasText: "选择" }).count();
    const selectedName = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const pagePickerNameWhiteSpace = await page.locator(".page-picker-panel .scan-row-main strong").first().evaluate((node) => (
      window.getComputedStyle(node).whiteSpace
    ));
    const pagePickerNameTitle = await page.locator(".page-picker-panel .scan-row-main strong").first().getAttribute("title");
    const pagePickerListStyles = await page.locator(".page-picker-panel .scan-list").first().evaluate((node) => {
      const style = window.getComputedStyle(node);
      return {
        maxHeight: style.maxHeight,
        overflowY: style.overflowY,
      };
    });
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
    const defaultVersionGuideCount = await page.locator(".version-panel .version-guide").count();
    const defaultVersionCurrentBadgeCount = await page.locator(".version-panel .version-current-badge").count();
    const defaultVersionRowCount = await page.locator(".version-panel .version-row").count();
    const defaultHistoricalVersionRowCount = await page.locator(".version-panel .version-row button:not([disabled])").count();
    const leakedDefaultVersionTerms = await visibleForbiddenTerms(page, ".version-panel");
    await page.locator(".version-panel").getByRole("button", { name: "关闭" }).click();
    await page.waitForSelector(".version-panel", { state: "detached", timeout: 10000 });
    currentStep = "open approval panel";
    const approvalCard = page.locator(".config-card").filter({ hasText: "审批规则" });
    await clickButtonByProductAliases(approvalCard, ["配置审批"]);
    await page.waitForSelector(".approval-panel", { timeout: 10000 });
    const approvalConfigEnvelope = await browserIntentEnvelope(page, "sc.approval_policy.config.get", {
      model: CONFIG_MODEL,
    });
    const approvalSourceAuthority = approvalConfigEnvelope?.meta?.source_authority || {};
    const approvalSourceAuthorities = Array.isArray(approvalSourceAuthority.authorities)
      ? approvalSourceAuthority.authorities.map((item) => String(item || ""))
      : [];
    let approvalPanel = page.locator(".approval-panel");
    const approvalPanelTitle = await approvalPanel.locator("h2").innerText();
    const approvalPanelText = await approvalPanel.innerText();
    const approvalEditorPanelCount = await approvalPanel.evaluate((node) => node.classList.contains("config-editor-panel") ? 1 : 0);
    const approvalRulePanelCount = await approvalPanel.locator(".approval-rule-panel").count();
    const approvalStepCanvasCount = await approvalPanel.locator(".approval-steps").count();
    const approvalGuideText = await approvalPanel.locator(".approval-guide").innerText();
    const approvalImpactSummaryText = await approvalPanel.locator(".approval-impact-summary").innerText();
    const approvalFieldLabels = await approvalPanel.locator(".approval-config-grid label span").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const approvalModeOptionLabels = await approvalPanel.locator("select").first().locator("option").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const approvalScopeOptionCount = await approvalPanel.locator("select").nth(1).locator("option").count();
    const approvalSaveDisabledInitially = await approvalPanel.getByRole("button", { name: "保存审批设置" }).isDisabled();
    const approvalAdvancedButtonCount = await approvalPanel.getByRole("button", { name: "更多规则" }).count();
    const approvalRequiredToggle = approvalPanel.locator(".approval-toggle input[type='checkbox']");
    const approvalWasEnabledInitially = await approvalRequiredToggle.isChecked();
    const approvalStepText = await approvalPanel.locator(".approval-steps").innerText();
    const approvalStepDragHandleCount = await approvalPanel.locator(".approval-step-drag").count();
    let approvalStepDirectDragRowCount = await approvalPanel.locator(".approval-step-row[draggable='true']").count();
    const approvalStepHeaderText = await approvalPanel.locator(".approval-step-table-head").innerText().catch(() => "");
    const approvalAddStepButtonCount = await approvalPanel.getByRole("button", { name: "添加步骤" }).count();
    const approvalStepRowCount = await approvalPanel.locator(".approval-step-row").count();
    const approvalDragProbeSuffix = String(Date.now());
    let approvalDragOrderBefore = [];
    let approvalDragOrderAfter = [];
    let approvalDragResetOrder = [];
    let approvalDragSaveEnabled = false;
    let approvalDragResetSaveDisabled = false;
    let approvalPersistOriginalName = "";
    let approvalPersistSavedName = "";
    let approvalPersistSaveEnabled = false;
    let approvalPersistReloadName = "";
    let approvalPersistRestoreSaveDisabled = false;
    if (approvalStepRowCount >= 2) {
      if (!approvalWasEnabledInitially) {
        currentStep = "enable approval for drag probe";
        await approvalRequiredToggle.check();
        await page.waitForFunction(() => {
          const firstInput = document.querySelector(".approval-step-row input[type='text']");
          return firstInput && !firstInput.disabled;
        }, null, { timeout: 10000 });
      }
      approvalStepDirectDragRowCount = await approvalPanel.locator(".approval-step-row[draggable='true']").count();
      const firstProbeName = `验收步骤A-${approvalDragProbeSuffix}`;
      const secondProbeName = `验收步骤B-${approvalDragProbeSuffix}`;
      currentStep = "prepare approval drag probe";
      await approvalPanel.locator(".approval-step-row").nth(0).locator("input[type='text']").fill(firstProbeName);
      await approvalPanel.locator(".approval-step-row").nth(1).locator("input[type='text']").fill(secondProbeName);
      approvalDragOrderBefore = await approvalStepNames(page);
      currentStep = "run approval drag probe";
      await dragApprovalStep(page, 0, 1);
      await page.waitForFunction((expectedFirst) => {
        const firstInput = document.querySelector(".approval-step-row input[type='text']");
        return firstInput?.value === expectedFirst;
      }, secondProbeName, { timeout: 10000 });
      approvalDragOrderAfter = await approvalStepNames(page);
      approvalDragSaveEnabled = await approvalPanel.getByRole("button", { name: "保存审批设置" }).isEnabled();
      report.artifacts.approvalPanelDragged = await captureStep(page, "approval-panel-dragged");
      currentStep = "reset approval drag probe";
      await approvalPanel.getByRole("button", { name: "还原" }).click();
      await page.waitForFunction((probeSuffix) => {
        const names = Array.from(document.querySelectorAll(".approval-step-row input[type='text']"))
          .map((node) => node.value || "");
        return names.every((name) => !name.includes(probeSuffix));
      }, approvalDragProbeSuffix, { timeout: 10000 });
      approvalDragResetOrder = await approvalStepNames(page);
      approvalDragResetSaveDisabled = await approvalPanel.getByRole("button", { name: "保存审批设置" }).isDisabled();
      currentStep = "save approval step persistence probe";
      const firstStepInput = approvalPanel.locator(".approval-step-row").nth(0).locator("input[type='text']");
      if (await firstStepInput.isDisabled()) {
        await approvalRequiredToggle.check();
        await page.waitForFunction(() => {
          const input = document.querySelector(".approval-step-row input[type='text']");
          return input && !input.disabled;
        }, null, { timeout: 10000 });
      }
      approvalPersistOriginalName = await firstStepInput.inputValue();
      approvalPersistSavedName = `审批保存验收-${approvalDragProbeSuffix}`;
      await firstStepInput.fill(approvalPersistSavedName);
      approvalPersistSaveEnabled = await approvalPanel.getByRole("button", { name: "保存审批设置" }).isEnabled();
      await approvalPanel.getByRole("button", { name: "保存审批设置" }).click();
      await page.waitForFunction(() => {
        const button = Array.from(document.querySelectorAll("button"))
          .find((node) => node.textContent?.includes("保存审批设置"));
        return Boolean(button?.disabled);
      }, null, { timeout: 20000 });
      await approvalPanel.getByRole("button", { name: "关闭" }).click();
      await page.waitForSelector(".approval-panel", { state: "detached", timeout: 10000 });
      await clickButtonByProductAliases(
        page.locator(".config-card").filter({ hasText: "审批规则" }),
        ["配置审批"],
      );
      await page.waitForSelector(".approval-panel", { timeout: 10000 });
      approvalPanel = page.locator(".approval-panel");
      approvalPersistReloadName = await approvalPanel.locator(".approval-step-row").nth(0).locator("input[type='text']").inputValue();
      currentStep = "restore approval step persistence probe";
      await approvalPanel.locator(".approval-step-row").nth(0).locator("input[type='text']").fill(approvalPersistOriginalName);
      await approvalPanel.getByRole("button", { name: "保存审批设置" }).click();
      await page.waitForFunction(() => {
        const button = Array.from(document.querySelectorAll("button"))
          .find((node) => node.textContent?.includes("保存审批设置"));
        return Boolean(button?.disabled);
      }, null, { timeout: 20000 });
      approvalPersistRestoreSaveDisabled = await approvalPanel.getByRole("button", { name: "保存审批设置" }).isDisabled();
    }
    const leakedApprovalTerms = await visibleForbiddenTerms(page, ".approval-panel");
    report.artifacts.approvalPanel = await captureStep(page, "approval-panel");
    await approvalPanel.getByRole("button", { name: "关闭" }).click();
    await page.waitForSelector(".approval-panel", { state: "detached", timeout: 10000 });
    currentStep = "open menu config panel";
    const menuCard = page.locator(".config-card").filter({ hasText: "菜单入口" });
    await clickButtonByProductAliases(menuCard, ["配置菜单"]);
    await page.waitForURL((url) => String(url).includes("/admin/menu-config"), { timeout: 20000 });
    await page.waitForSelector(".menu-config-editor", { timeout: 20000 });
    await page.waitForFunction(() => !document.querySelector(".menu-config-editor .loading-state"), null, { timeout: 20000 });
    const menuConfigTitle = await page.locator(".menu-config-header h1").innerText();
    const menuConfigEditorCount = await page.locator(".menu-config-editor").count();
    const menuSelectedPanelCount = await page.locator(".menu-selected-panel").count();
    const menuSidePanelCount = await page.locator(".menu-side-panel").count();
    const menuSidePanelHeadCount = await page.locator(".menu-side-panel-head").count();
    const menuSideActionGroupLabels = await page.locator(".menu-side-action-group .menu-side-section-title").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const menuUtilitySectionCount = await page.locator(".menu-utility-section").count();
    const menuHeaderText = await page.locator(".menu-config-header").innerText();
    const menuHeaderHasUtilityActions = /生效检查|版本记录|回滚/.test(menuHeaderText);
    const menuBulkPanelCount = await page.locator(".menu-bulk-panel").count();
    const menuBulkCollapsedCount = await page.locator(".bulk-collapsed-state").count();
    const menuBulkToolbarText = await page.locator(".menu-bulk-panel .table-toolbar").innerText();
    const menuTreeCount = await page.locator(".menu-config-tree").count();
    const menuTreeHeadCount = await page.locator(".menu-config-tree .tree-panel-head").count();
    const menuTreeHeadText = await page.locator(".menu-config-tree .tree-panel-head").innerText();
    const menuTreeOrderToolCount = await page.locator(".tree-node-order-tools").count();
    const menuTreeNodeLabels = await page.locator(".menu-config-tree .tree-scroll .tree-node").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.replace(/\s+/g, " ").trim()).filter(Boolean).slice(0, 20)
    ));
    const menuTreeInternalLabels = menuTreeNodeLabels.filter((label) => /user_confirmed_|technical_|system_/i.test(label));
    const menuFirstTreeNode = page.locator(".menu-config-tree .tree-scroll .tree-node").first();
    const menuFirstTreeNodeCount = await menuFirstTreeNode.count();
    if (menuFirstTreeNodeCount) {
      await menuFirstTreeNode.click();
    }
    const menuSelectedTitle = await page.locator(".menu-selected-panel h2").innerText();
    const menuSelectedInputCount = await page.locator(".menu-selected-panel .cell-input").count();
    const menuRolePanelCount = await page.locator(".menu-selected-panel .menu-role-panel").count();
    const menuDetailSectionLabels = await page.locator(".menu-selected-panel .menu-detail-section-head strong, .menu-selected-panel .menu-role-head strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const menuConfigPageText = await page.locator(".menu-config-page").innerText();
    const menuConfigHasInternalNote = /user_confirmed_|technical_|system_/.test(menuConfigPageText);
    const leakedMenuConfigTerms = await visibleForbiddenTerms(page, ".menu-config-page");
    report.artifacts.menuConfigPanel = await captureStep(page, "menu-config-panel");
    await page.getByRole("button", { name: "返回配置工作台" }).click();
    await page.waitForURL((url) => String(url).includes("/admin/business-config"), { timeout: 20000 });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    currentStep = "page search and switch";
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
    const advancedForbiddenTerms = await visibleAdvancedForbiddenTerms(page);
    const advancedPanelVisible = await page.locator(".scan-panel--admin").count();
    const advancedConfigCheckPanelCount = await page.locator(".scan-panel--admin").filter({ hasText: "配置检查明细" }).count();
    const snapshotDownloadButtonCount = await page.getByRole("button", { name: "下载当前快照" }).count();
    const snapshotCompareButtonCount = await page.getByRole("button", { name: "对比快照" }).count();
    const snapshotRemediationButtonCount = await page.getByRole("button", { name: "下载整改清单" }).count();
    const currentSnapshot = await browserIntent(page, "ui.business_config.snapshot.export");
    await page.locator(".snapshot-input").fill(JSON.stringify(currentSnapshot));
    await page.getByRole("button", { name: "对比快照" }).click();
    await page.waitForFunction(() => {
      const button = Array.from(document.querySelectorAll("button"))
        .find((node) => node.textContent?.includes("下载整改清单"));
      return button && !button.disabled;
    }, null, { timeout: 20000 });
    const remediationDownload = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "下载整改清单" }).click(),
    ]).then(([download]) => download);
    const remediationDownloadPath = await remediationDownload.path();
    const remediationDownloadName = remediationDownload.suggestedFilename();
    assert(remediationDownloadPath, "整改清单下载文件不可用", { remediationDownloadName });
    const remediationPlan = JSON.parse(await fs.readFile(remediationDownloadPath, "utf8"));
    const remediationSummaryText = await page.locator(".snapshot-remediation-summary").innerText();
    await page.getByRole("button", { name: "高级设置" }).click();
    await page.waitForSelector(".scope-panel", { state: "detached", timeout: 10000 });
    await page.locator(".selected-page-overview").getByRole("button", { name: "预览页面" }).click();
    await page.waitForURL((url) => String(url).includes("/a/562"), { timeout: 20000 });
    const previewUrl = page.url();
    await page.goBack({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    report.checks.defaultConfigPage = {
      defaultCards,
      configWorkspaceCount,
      pagePickerPanelCount,
      pageConfigPanelCount,
      pagePickerHeadText,
      selectedOverviewText,
      defaultSelectedRowActionLabels,
      defaultSelectedRowCurrentText,
      defaultNonSelectedChooseButtonCount,
      selectedName,
      pagePickerNameWhiteSpace,
      pagePickerNameTitle,
      pagePickerListStyles,
      pageTypeLabels,
      leakedDefaultTerms,
      defaultHasUnwiredCopy: defaultPageText.includes("编辑入口待接入"),
      defaultVersionButtonCount,
      defaultVersionTitle,
      defaultVersionDescription,
      defaultVersionPanelText,
      defaultVersionGuideCount,
      defaultVersionCurrentBadgeCount,
      defaultVersionRowCount,
      defaultHistoricalVersionRowCount,
      leakedDefaultVersionTerms,
      approvalPanelTitle,
      approvalPanelText,
      approvalEditorPanelCount,
      approvalRulePanelCount,
      approvalStepCanvasCount,
      approvalFieldLabels,
      approvalModeOptionLabels,
      approvalScopeOptionCount,
      approvalSaveDisabledInitially,
      approvalWasEnabledInitially,
      approvalAdvancedButtonCount,
      approvalStepRowCount,
      approvalStepDragHandleCount,
      approvalStepDirectDragRowCount,
      approvalDragOrderBefore,
      approvalDragOrderAfter,
      approvalDragResetOrder,
      approvalDragSaveEnabled,
      approvalDragResetSaveDisabled,
      approvalPersistOriginalName,
      approvalPersistSavedName,
      approvalPersistSaveEnabled,
      approvalPersistReloadName,
      approvalPersistRestoreSaveDisabled,
      approvalBoundary: {
        sourceAuthorityKind: String(approvalSourceAuthority.kind || ""),
        sourceAuthorities: approvalSourceAuthorities,
        projectionOnly: Boolean(approvalSourceAuthority.projection_only),
        noBusinessFactAuthority: Boolean(approvalSourceAuthority.no_business_fact_authority),
        boundary: String(approvalSourceAuthority.boundary || ""),
        lowcodeBoundary: String(approvalSourceAuthority.lowcode_boundary || ""),
        policySource: String(approvalSourceAuthority.policy_source || ""),
        lowcodeSource: String(approvalSourceAuthority.lowcode_source || ""),
      },
      leakedApprovalTerms,
      menuConfigTitle,
      menuConfigEditorCount,
      menuSelectedPanelCount,
      menuSidePanelCount,
      menuSidePanelHeadCount,
      menuSideActionGroupLabels,
      menuUtilitySectionCount,
      menuHeaderHasUtilityActions,
      menuBulkPanelCount,
      menuBulkCollapsedCount,
      menuBulkToolbarText,
      menuTreeCount,
      menuTreeHeadCount,
      menuTreeHeadText,
      menuTreeOrderToolCount,
      menuTreeNodeLabels,
      menuTreeInternalLabels,
      menuFirstTreeNodeCount,
      menuSelectedTitle,
      menuSelectedInputCount,
      menuRolePanelCount,
      menuDetailSectionLabels,
      menuConfigHasInternalNote,
      leakedMenuConfigTerms,
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
      advancedConfigCheckPanelCount,
      advancedHasUnwiredCopy: advancedText.includes("编辑入口待接入"),
      advancedHasConfigCheckText: advancedText.includes("配置检查明细") && advancedText.includes("配置状态"),
      advancedForbiddenTerms,
      snapshotDownloadButtonCount,
      snapshotCompareButtonCount,
      snapshotRemediationButtonCount,
      snapshotRemediationSummaryText: remediationSummaryText,
      snapshotRemediationDownloadName: remediationDownloadName,
      snapshotRemediationPlanSchema: remediationPlan.schema_version,
      snapshotRemediationActionCount: remediationPlan.summary?.action_count,
      previewUrl,
    };
    report.artifacts.defaultConfigPage = await captureStep(page, "default-config-page");
    assert(
      defaultCards.join("|") === "表单字段与布局|列表与搜索|菜单入口|审批规则",
      "默认配置卡片不符合用户配置边界",
      { defaultCards },
    );
    assert(
      menuTreeNodeLabels.length > 0 && menuTreeInternalLabels.length === 0,
      "菜单配置树显示了空节点或内部技术标识",
      { menuTreeNodeLabels, menuTreeInternalLabels },
    );
    assert(
      configWorkspaceCount === 1
        && pagePickerPanelCount === 1
        && pageConfigPanelCount === 1
        && pagePickerHeadText.includes("业务页面目录")
        && pagePickerHeadText.includes("个匹配页面")
        && selectedOverviewText.includes("正在配置")
        && selectedOverviewText.includes("项目合同汇总")
        && defaultSelectedRowActionLabels.length === 0
        && defaultSelectedRowCurrentText === "当前配置"
        && defaultNonSelectedChooseButtonCount >= 1
        && pagePickerNameWhiteSpace === "normal"
        && pagePickerNameTitle === selectedName
        && pagePickerListStyles.overflowY === "auto"
        && pagePickerListStyles.maxHeight !== "none",
      "配置页面没有形成左侧页面列表和右侧配置面板结构",
      {
        configWorkspaceCount,
        pagePickerPanelCount,
        pageConfigPanelCount,
        pagePickerHeadText,
        selectedOverviewText,
        defaultSelectedRowActionLabels,
        defaultSelectedRowCurrentText,
        defaultNonSelectedChooseButtonCount,
        pagePickerNameWhiteSpace,
        pagePickerNameTitle,
        pagePickerListStyles,
      },
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
        && advancedConfigCheckPanelCount === 1
        && advancedText.includes("配置检查明细")
        && advancedText.includes("配置状态")
        && snapshotDownloadButtonCount === 1
        && snapshotCompareButtonCount === 1
        && snapshotRemediationButtonCount === 1
        && remediationSummaryText.includes("无需生成整改动作")
        && remediationDownloadName.startsWith("business-config-remediation-")
        && remediationPlan.schema_version === "business_config_snapshot_remediation_plan.v1"
        && remediationPlan.summary?.action_count === 0
        && advancedForbiddenTerms.length === 0,
      "高级设置不可用或露出了治理/技术话术",
      { advancedScopeLabels, advancedPanelVisible, advancedConfigCheckPanelCount, snapshotDownloadButtonCount, snapshotCompareButtonCount, snapshotRemediationButtonCount, remediationSummaryText, remediationDownloadName, remediationPlan, advancedForbiddenTerms },
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
        && defaultVersionGuideCount === 1
        && (defaultVersionRowCount > 0
          ? defaultVersionPanelText.includes("当前生效") && defaultVersionCurrentBadgeCount > 0
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
        defaultVersionGuideCount,
        defaultVersionCurrentBadgeCount,
        defaultVersionRowCount,
        defaultHistoricalVersionRowCount,
        leakedDefaultVersionTerms,
      },
    );
    assert(
      approvalPanelTitle === "审批规则"
        && approvalEditorPanelCount === 1
        && approvalRulePanelCount === 1
        && approvalStepCanvasCount === 1
        && approvalGuideText.includes("审批配置怎么生效")
        && approvalGuideText.includes("保存后立即影响")
        && approvalImpactSummaryText.includes("当前规则")
        && approvalFieldLabels.join("|") === "启用审批|审批方式|默认审批岗位"
        && approvalModeOptionLabels.includes("无需审核")
        && approvalModeOptionLabels.includes("单级审核")
        && approvalModeOptionLabels.includes("多级顺序审核")
        && approvalScopeOptionCount >= 1
        && approvalSourceAuthority.lowcode_boundary === "approval_policy"
        && approvalSourceAuthority.policy_source === "sc.approval.policy"
        && approvalSourceAuthority.boundary === "industry_policy_runtime"
        && approvalSourceAuthority.no_business_fact_authority === true
        && approvalSourceAuthority.projection_only === true
        && approvalSourceAuthorities.includes("sc.approval.policy")
        && approvalSaveDisabledInitially
        && approvalAdvancedButtonCount === 1
        && approvalStepText.includes("审批步骤")
        && approvalStepHeaderText.includes("步骤名称")
        && approvalStepHeaderText.includes("审批岗位")
        && approvalAddStepButtonCount === 1
        && approvalStepDragHandleCount === 0
        && approvalStepRowCount >= 2
        && approvalStepDirectDragRowCount >= 2
        && approvalDragOrderBefore.length >= 2
        && approvalDragOrderAfter[0] === approvalDragOrderBefore[1]
        && approvalDragOrderAfter[1] === approvalDragOrderBefore[0]
        && approvalDragSaveEnabled
        && approvalDragResetSaveDisabled
        && approvalDragResetOrder.every((name) => !name.includes(approvalDragProbeSuffix))
        && approvalPersistOriginalName.length > 0
        && approvalPersistSaveEnabled
        && approvalPersistReloadName === approvalPersistSavedName
        && approvalPersistRestoreSaveDisabled
        && leakedApprovalTerms.length === 0,
      "审批设置面板不可用或露出了治理话术",
      {
        approvalPanelTitle,
        approvalPanelText,
        approvalEditorPanelCount,
        approvalRulePanelCount,
        approvalStepCanvasCount,
        approvalGuideText,
        approvalImpactSummaryText,
        approvalFieldLabels,
        approvalModeOptionLabels,
        approvalScopeOptionCount,
        approvalSourceAuthority,
        approvalSourceAuthorities,
        approvalSaveDisabledInitially,
        approvalAdvancedButtonCount,
        approvalStepText,
        approvalStepHeaderText,
        approvalStepDragHandleCount,
        approvalStepDirectDragRowCount,
        approvalAddStepButtonCount,
        approvalStepRowCount,
        approvalDragOrderBefore,
        approvalDragOrderAfter,
        approvalDragResetOrder,
        approvalDragSaveEnabled,
        approvalDragResetSaveDisabled,
        approvalPersistOriginalName,
        approvalPersistSavedName,
        approvalPersistSaveEnabled,
        approvalPersistReloadName,
        approvalPersistRestoreSaveDisabled,
        leakedApprovalTerms,
      },
    );
    assert(
      menuConfigTitle === "菜单配置"
        && menuConfigEditorCount === 1
        && menuSelectedPanelCount === 1
        && menuSidePanelCount === 1
        && menuSidePanelHeadCount === 1
        && menuSideActionGroupLabels.join("|") === "新增入口|批量维护|检查发布"
        && menuUtilitySectionCount === 1
        && !menuHeaderHasUtilityActions
        && menuBulkPanelCount === 1
        && menuBulkCollapsedCount === 1
        && menuBulkToolbarText.includes("批量维护")
        && menuBulkToolbarText.includes("未保存")
        && menuTreeCount === 1
        && menuTreeHeadCount === 1
        && menuTreeHeadText.includes("菜单目录")
        && menuTreeHeadText.includes("直接拖拽排序")
        && menuTreeOrderToolCount === 0
        && menuFirstTreeNodeCount >= 1
        && menuSelectedTitle !== "全部菜单"
        && menuSelectedInputCount >= 4
        && menuRolePanelCount === 1
        && menuDetailSectionLabels.join("|") === "基础信息|位置与显示|可见业务角色"
        && !menuConfigHasInternalNote
        && leakedMenuConfigTerms.length === 0,
      "菜单配置页面没有形成专业配置面板结构",
      {
        menuConfigTitle,
        menuConfigEditorCount,
        menuSelectedPanelCount,
        menuSidePanelCount,
        menuSidePanelHeadCount,
        menuSideActionGroupLabels,
        menuUtilitySectionCount,
        menuHeaderHasUtilityActions,
        menuBulkPanelCount,
        menuBulkCollapsedCount,
        menuBulkToolbarText,
        menuTreeCount,
        menuTreeHeadCount,
        menuTreeHeadText,
        menuTreeOrderToolCount,
        menuFirstTreeNodeCount,
        menuSelectedTitle,
        menuSelectedInputCount,
        menuRolePanelCount,
        menuDetailSectionLabels,
        menuConfigHasInternalNote,
        leakedMenuConfigTerms,
      },
    );

    await page.goto(ANALYSIS_CONFIG_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".scan-row--selected", { timeout: 20000 });
    const analysisSelectedName = await page.locator(".scan-row--selected .scan-row-main strong").first().innerText();
    const analysisCards = await page.locator(".config-card h2").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    await clickButtonByProductAliases(page, ["配置分析"]);
    await page.waitForSelector(".edit-panel", { timeout: 20000 });
    const analysisPanel = page.locator(".edit-panel").filter({ hasText: "分析视图设置" });
    const analysisTitle = await analysisPanel.locator("h2").innerText();
    const analysisEditorPanelCount = await analysisPanel.evaluate((node) => node.classList.contains("config-editor-panel") ? 1 : 0);
    const analysisEditorNavCount = await analysisPanel.locator(".list-search-tabs").count();
    const analysisEditorCanvasCount = await analysisPanel.locator(".field-chip-editor").count();
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
      analysisEditorPanelCount,
      analysisEditorNavCount,
      analysisEditorCanvasCount,
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
      analysisEditorPanelCount === 1 && analysisEditorNavCount === 1 && analysisEditorCanvasCount === 1,
      "分析视图面板没有形成配置导航和配置画布结构",
      { analysisEditorPanelCount, analysisEditorNavCount, analysisEditorCanvasCount },
    );
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
    const listSearchAuditEnvelope = await browserIntentEnvelope(page, "ui.business_config.list_search.audit", {
      model: CONFIG_MODEL,
      action_id: CONFIG_ACTION_ID,
    });
    const listSearchAuditBoundary = listSearchAuditEnvelope?.data || {};
    const listSearchAuditSourceAuthority = listSearchAuditEnvelope?.meta?.source_authority || {};
    const listSearchAuditAuthorities = Array.isArray(listSearchAuditSourceAuthority.authorities)
      ? listSearchAuditSourceAuthority.authorities.map((item) => String(item || ""))
      : [];
    const listSearchPanel = page.locator(".edit-panel").filter({ hasText: "列表与搜索设置" });
    const listSearchTitle = await listSearchPanel.locator("h2").innerText();
    const listSearchEditorPanelCount = await listSearchPanel.evaluate((node) => node.classList.contains("config-editor-panel") ? 1 : 0);
    const listSearchEditorNavCount = await listSearchPanel.locator(".list-search-tabs").count();
    const listSearchEditorCanvasCount = await listSearchPanel.locator(".field-chip-editor").count();
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
    const searchedListDuplicateLabelCount = searchedListOptionLabels.length - new Set(searchedListOptionLabels).size;
    await page.locator(".field-option-search").fill("");
    report.checks.listSearchPanel = {
      listSearchTitle,
      listSearchEditorPanelCount,
      listSearchEditorNavCount,
      listSearchEditorCanvasCount,
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
      searchedListDuplicateLabelCount,
      auditBoundary: {
        userPreferenceBoundary: String(listSearchAuditBoundary?.user_preference_boundary || ""),
        userPreferenceCount: Number(listSearchAuditBoundary?.user_preference_count || 0),
        hasBusinessListConfig: Boolean(listSearchAuditBoundary?.has_business_list_config),
        hasBusinessSearchConfig: Boolean(listSearchAuditBoundary?.has_business_search_config),
        sourceAuthorityKind: String(listSearchAuditSourceAuthority.kind || ""),
        sourceAuthorities: listSearchAuditAuthorities,
        projectionOnly: Boolean(listSearchAuditSourceAuthority.projection_only),
        noBusinessFactAuthority: Boolean(listSearchAuditSourceAuthority.no_business_fact_authority),
      },
    };
    report.artifacts.listSearchPanel = await captureStep(page, "list-search-panel");
    assert(listSearchTitle === "列表与搜索设置", "列表与搜索面板标题不正确", { listSearchTitle });
    assert(
      listSearchEditorPanelCount === 1 && listSearchEditorNavCount === 1 && listSearchEditorCanvasCount === 1,
      "列表与搜索面板没有形成配置导航和配置画布结构",
      { listSearchEditorPanelCount, listSearchEditorNavCount, listSearchEditorCanvasCount },
    );
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
      searchedListOptionCount > 0
        && searchedListOptionLabels.every((label) => label.includes("合同"))
        && searchedListDuplicateLabelCount === 0,
      "列表与搜索字段池搜索不可用",
      { searchedListOptionCount, searchedListOptionLabels, searchedListDuplicateLabelCount },
    );
    assert(
      listSearchAuditBoundary?.user_preference_boundary === "ui_only"
        && listSearchAuditAuthorities.includes("ui.business.config.contract")
        && listSearchAuditAuthorities.includes("sc.user.view.preference")
        && listSearchAuditSourceAuthority.projection_only === true
        && listSearchAuditSourceAuthority.no_business_fact_authority === true,
      "列表与搜索业务默认配置和个人偏好边界没有分离",
      {
        listSearchAuditBoundary,
        listSearchAuditSourceAuthority,
        listSearchAuditAuthorities,
      },
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
    await page.getByRole("button", { name: "配置表单字段" }).first().click();
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    const designTitle = await page.locator(".contract-form-settings h4").innerText();
    const leakedFormDesignerTerms = await visibleForbiddenTerms(page, ".contract-form-settings");
    const designFieldCountText = await page.locator(".contract-form-settings-field-count").innerText();
    const designFieldCount = Number((designFieldCountText.match(/\d+/) || ["0"])[0]);
    const dragHandleCount = await page.locator(".field-order-handle").count();
    const orderButtonCount = await page.locator(".field-order-btn, .contract-field-selection-order-btn").count();
    const draggableFieldCount = await page.locator(".field--order-editable[draggable='true']").count();
    const selectableFieldCount = await page.locator(".field--selectable").count();
    const dragAutoScrollProbe = await probeDesignerFieldDragAutoScroll(page);
    const dropPlacementProbe = await probeDesignerFieldDropPlacement(page);
    const returnButtonCount = await page.getByRole("button", { name: "返回配置" }).count();
    const legacyPanelCount = await page.locator(".contract-lowcode-objects").count();
    const designerControlGridCount = await page.locator(".contract-form-designer-control-grid").count();
    const designerInspectorCount = await page.locator(".contract-form-inspector").count();
    const designerCanvasCount = await page.locator(".contract-form-designer-canvas").count();
    const designerWorkspaceCount = await page.locator(".form-grid--designer-workspace").count();
    const designerSidebarCount = await page.locator(".contract-form-designer-sidebar").count();
    const designerSidebarHeadText = await page.locator(".contract-form-designer-sidebar-head").innerText();
    const designerFieldNavigatorCount = await page.locator(".contract-form-field-navigator").count();
    const designerFieldNavigatorHeaderText = await page.locator(".contract-form-field-navigator header").innerText();
    const designerFieldNavigatorItemCount = await page.locator(".contract-form-field-nav-item").count();
    const designerCanvasHeadText = await page.locator(".contract-form-canvas-head").innerText();
    let designerInspectorSectionLabels = [];
    const designerLayoutToolText = await page.locator(".contract-form-layout-tools").innerText();
    const initialFormDirtyCount = await page.locator(".contract-field-governance-dirty").count();
    const initialHiddenFieldDesignCount = await page.locator(".field--config-hidden").count();
    const initialHiddenGroupDesignCount = await page.locator(".native-container--config-hidden").count();
    const initialSaveFormEnabled = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await selectDesignerField(page, 0);
    const selectedFieldCount = await page.locator(".field--selected").count();
    const selectedPanelText = await page.locator(".contract-field-selection-card").innerText();
    designerInspectorSectionLabels = await page.locator(".contract-field-inspector-section header strong").evaluateAll((nodes) => (
      nodes.map((node) => node.textContent?.trim()).filter(Boolean)
    ));
    const inlineAddButtonCount = await page.locator(".field-order-btn", { hasText: "新增" }).count();
    const inlineVisibilityActionCount = await page.locator(".field-inline-actions .field-inline-action").count();
    await page.locator(".contract-field-governance-actions").getByText("隐藏", { exact: true }).click();
    const operationLogTextAfterHide = await page.locator(".contract-form-operation-log").innerText();
    const operationLogEntryCountAfterHide = await page.locator(".contract-form-operation-log-list li").count();
    const formDirtyAfterHide = await page.locator(".contract-field-governance-dirty").count();
    const hiddenFieldDesignCountAfterHide = await page.locator(".field--config-hidden").count();
    const saveFormEnabledAfterHide = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    const resetFormEnabledAfterHide = await page.getByRole("button", { name: "重置" }).isEnabled();
    await page.getByRole("button", { name: "重置" }).click();
    const operationLogTextAfterReset = await page.locator(".contract-form-operation-log").innerText();
    const formDirtyAfterReset = await page.locator(".contract-field-governance-dirty").count();
    const hiddenFieldDesignCountAfterReset = await page.locator(".field--config-hidden").count();
    const saveFormEnabledAfterReset = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    await selectDesignerField(page, 1);
    const selectedPanelBeforeMove = await page.locator(".contract-field-selection-card").innerText();
    const pageColumnsControlCount = await page.locator(".contract-form-layout-tools select").count();
    let pageColumnsDirtyAfterEdit = 0;
    let pageColumnsDirtyAfterRestore = 0;
    if (pageColumnsControlCount > 0) {
      const pageColumnsSelect = page.locator(".contract-form-layout-tools select").first();
      const originalColumns = await pageColumnsSelect.inputValue();
      const alternateColumns = originalColumns === "3" ? "2" : "3";
      await pageColumnsSelect.selectOption(alternateColumns);
      await page.waitForTimeout(300);
      pageColumnsDirtyAfterEdit = await page.locator(".contract-field-governance-dirty").count();
      await pageColumnsSelect.selectOption(originalColumns);
      await page.waitForTimeout(300);
      pageColumnsDirtyAfterRestore = await page.locator(".contract-field-governance-dirty").count();
    }
    await selectDesignerField(page, 1);
    const groupVisibilityControlCount = await page.locator(".contract-field-group-visibility input").count();
    const groupColumnsControlCount = await page.locator(".contract-field-group-columns select").count();
    const fieldSizeControlCount = await page.locator(".contract-field-size-control select").count();
    let groupVisibilityDirtyAfterHide = 0;
    let groupVisibilityDirtyAfterRestore = 0;
    let hiddenGroupDesignCountAfterHide = 0;
    let hiddenGroupDesignCountAfterRestore = 0;
    if (groupVisibilityControlCount >= 2) {
      await page.locator(".contract-field-group-visibility input[value='hide']").first().click();
      await page.waitForTimeout(300);
      groupVisibilityDirtyAfterHide = await page.locator(".contract-field-governance-dirty").count();
      hiddenGroupDesignCountAfterHide = await page.locator(".native-container--config-hidden").count();
      await page.locator(".contract-field-group-visibility input[value='show']").first().click();
      await page.waitForTimeout(300);
      groupVisibilityDirtyAfterRestore = await page.locator(".contract-field-governance-dirty").count();
      hiddenGroupDesignCountAfterRestore = await page.locator(".native-container--config-hidden").count();
    }
    await selectDesignerField(page, 1);
    let groupColumnsDirtyAfterEdit = 0;
    let groupColumnsDirtyAfterRestore = 0;
    if (groupColumnsControlCount > 0) {
      const groupColumnsSelect = page.locator(".contract-field-group-columns select").first();
      const originalColumns = await groupColumnsSelect.inputValue();
      const alternateColumns = originalColumns === "3" ? "2" : "3";
      await groupColumnsSelect.selectOption(alternateColumns);
      await page.waitForTimeout(300);
      groupColumnsDirtyAfterEdit = await page.locator(".contract-field-governance-dirty").count();
      await groupColumnsSelect.selectOption(originalColumns);
      await page.waitForTimeout(300);
      groupColumnsDirtyAfterRestore = await page.locator(".contract-field-governance-dirty").count();
    }
    let fieldSizeDirtyAfterEdit = 0;
    let fieldSizeDirtyAfterRestore = 0;
    if (fieldSizeControlCount > 0) {
      const fieldSizeSelect = page.locator(".contract-field-size-control select").first();
      const originalSize = await fieldSizeSelect.inputValue();
      const alternateSize = originalSize === "full" ? "normal" : "full";
      await fieldSizeSelect.selectOption(alternateSize);
      await page.waitForTimeout(300);
      fieldSizeDirtyAfterEdit = await page.locator(".contract-field-governance-dirty").count();
      await fieldSizeSelect.selectOption(originalSize);
      await page.waitForTimeout(300);
      fieldSizeDirtyAfterRestore = await page.locator(".contract-field-governance-dirty").count();
    }
    await selectDesignerField(page, 1);
    const groupRenameControlCount = await page.locator(".contract-field-group-rename input").count();
    let groupRenameOriginalTitle = "";
    let groupRenameTempTitle = "";
    let groupRenamePanelAfterRename = "";
    let groupRenamePanelAfterRestore = "";
    if (groupRenameControlCount > 0) {
      const groupRenameInput = page.locator(".contract-field-group-rename input").first();
      groupRenameOriginalTitle = (await groupRenameInput.inputValue()).trim();
      groupRenameTempTitle = `${groupRenameOriginalTitle}验收`;
      if (groupRenameOriginalTitle && groupRenameTempTitle !== groupRenameOriginalTitle) {
        await groupRenameInput.fill(groupRenameTempTitle);
        await groupRenameInput.press("Enter");
        await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
        await page.waitForTimeout(1000);
        await selectDesignerField(page, 1);
        groupRenamePanelAfterRename = await page.locator(".contract-field-selection-card").innerText();
        const restoreInput = page.locator(".contract-field-group-rename input").first();
        await restoreInput.fill(groupRenameOriginalTitle);
        await restoreInput.press("Enter");
        await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
        await page.waitForTimeout(1000);
        await selectDesignerField(page, 1);
        groupRenamePanelAfterRestore = await page.locator(".contract-field-selection-card").innerText();
      }
    }
    const positionMoveControlCount = await page.locator(".contract-field-position-move").count();
    const formOrderBeforePanelMove = await formDesignerFieldTexts(page);
    const panelMoveSourceLabel = formOrderBeforePanelMove[1] || "";
    const panelMoveTargetLabel = formOrderBeforePanelMove[2] || formOrderBeforePanelMove[0] || "";
    let formOrderAfterPanelMove = formOrderBeforePanelMove;
    let panelMoveResetSaveDisabled = true;
    if (panelMoveSourceLabel && panelMoveTargetLabel) {
      await page.locator(".contract-field-position-move select").first().selectOption({ label: panelMoveTargetLabel });
      await page.locator(".contract-field-position-move select").nth(1).selectOption("after");
      await page.locator(".contract-field-position-move").getByRole("button", { name: "移动" }).click();
      await page.waitForTimeout(500);
      formOrderAfterPanelMove = await formDesignerFieldTexts(page);
      await page.getByRole("button", { name: "重置" }).click();
      await page.waitForTimeout(500);
      panelMoveResetSaveDisabled = !(await page.getByRole("button", { name: "保存表单设置" }).isEnabled());
    }
    const formOrderBeforeDragPersist = await formDesignerFieldTexts(page);
    const sameGroupOrderProbe = (await formDesignerFieldGroups(page)).find((group) => group.fields.length >= 2);
    const orderSourceField = sameGroupOrderProbe?.fields?.[0] || { index: 0, label: formOrderBeforeDragPersist[0] || "" };
    const orderTargetField = sameGroupOrderProbe?.fields?.[1] || { index: 1, label: formOrderBeforeDragPersist[1] || "" };
    const draggedFieldLabel = orderSourceField.label;
    const nextFieldLabel = orderTargetField.label;
    await dragDesignerField(page, orderSourceField.index, orderTargetField.index);
    await page.waitForTimeout(1000);
    const formOrderAfterDrag = await formDesignerFieldTexts(page);
    const operationLogTextAfterDrag = await page.locator(".contract-form-operation-log").innerText();
    const operationLogHasTechnicalFieldAfterDrag = /\b[a-z][a-z0-9]*_[a-z0-9_]+\b/.test(operationLogTextAfterDrag);
    const operationLogGroupColumnEntryCountAfterDrag = (operationLogTextAfterDrag.match(/调整分组列数/g) || []).length;
    const saveFormEnabledAfterDrag = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
    let formOrderAfterPersistReload = formOrderAfterDrag;
    let saveFormEnabledAfterRestoreDrag = false;
    let formOrderAfterRestoreReload = formOrderAfterDrag;
    if (saveFormEnabledAfterDrag) {
      await page.getByRole("button", { name: "保存表单设置" }).click();
      await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
      await page.reload({ waitUntil: "domcontentloaded" });
      await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
      formOrderAfterPersistReload = await formDesignerFieldTexts(page);
      const persistedDraggedIndex = formOrderAfterPersistReload.indexOf(draggedFieldLabel);
      const persistedNextIndex = formOrderAfterPersistReload.indexOf(nextFieldLabel);
      await dragDesignerField(page, persistedDraggedIndex >= 0 ? persistedDraggedIndex : 1, persistedNextIndex >= 0 ? persistedNextIndex : 0);
      await page.waitForTimeout(1000);
      saveFormEnabledAfterRestoreDrag = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
      if (saveFormEnabledAfterRestoreDrag) {
        await page.getByRole("button", { name: "保存表单设置" }).click();
        await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
        await page.reload({ waitUntil: "domcontentloaded" });
        await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
        formOrderAfterRestoreReload = await formDesignerFieldTexts(page);
      }
    }
    const crossGroupBaseline = await ensureCrossGroupDesignerBaseline(page);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
    let formGroupsBeforeCrossDrop = await formDesignerFieldGroups(page);
    const crossDropSourceGroup = formGroupsBeforeCrossDrop.find((group) => group.fields.length);
    const crossDropTargetGroup = formGroupsBeforeCrossDrop.find((group) => (
      crossDropSourceGroup
        && group.groupIndex !== crossDropSourceGroup.groupIndex
        && group.title !== crossDropSourceGroup.title
    ));
    const crossDropSourceField = crossDropSourceGroup?.fields?.[0];
    let crossGroupDrop = { skipped: true };
    if (crossDropSourceGroup && crossDropTargetGroup && crossDropSourceField) {
      await dragDesignerFieldToGroup(page, crossDropSourceField.index, crossDropTargetGroup.groupIndex);
      await page.waitForTimeout(1000);
      const crossGroupSaveEnabled = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
      const crossDropPanelAfterDrop = await page.locator(".contract-field-selection-card").innerText().catch(() => "");
      const groupsAfterCrossDrop = await formDesignerFieldGroups(page);
      const targetGroupAfterDrop = groupsAfterCrossDrop.find((group) => group.title === crossDropTargetGroup.title);
      const sourceGroupAfterDrop = groupsAfterCrossDrop.find((group) => group.title === crossDropSourceGroup.title);
      const movedToTargetBeforeSave = Boolean(targetGroupAfterDrop?.fields.some((field) => field.label === crossDropSourceField.label));
      const removedFromSourceBeforeSave = !Boolean(sourceGroupAfterDrop?.fields.some((field) => field.label === crossDropSourceField.label));
      if (crossGroupSaveEnabled) {
        await page.getByRole("button", { name: "保存表单设置" }).click();
        await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
        await page.reload({ waitUntil: "domcontentloaded" });
        await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
      }
      const groupsAfterCrossDropPersist = await formDesignerFieldGroups(page);
      const persistedTargetGroup = groupsAfterCrossDropPersist.find((group) => group.title === crossDropTargetGroup.title);
      const persistedSourceGroup = groupsAfterCrossDropPersist.find((group) => group.title === crossDropSourceGroup.title);
      const persistedInTarget = Boolean(persistedTargetGroup?.fields.some((field) => field.label === crossDropSourceField.label));
      const persistedInSource = Boolean(persistedSourceGroup?.fields.some((field) => field.label === crossDropSourceField.label));
      const targetFieldAfterPersist = persistedTargetGroup?.fields.find((field) => field.label === crossDropSourceField.label);
      if (targetFieldAfterPersist) {
        await selectDesignerField(page, targetFieldAfterPersist.index);
      }
      const crossDropPanelAfterReload = await page.locator(".contract-field-selection-card").innerText().catch(() => "");
      crossGroupDrop = {
        skipped: false,
        baseline: crossGroupBaseline,
        sourceGroup: crossDropSourceGroup.title,
        targetGroup: crossDropTargetGroup.title,
        sourceField: crossDropSourceField.label,
        saveEnabled: crossGroupSaveEnabled,
        movedToTargetBeforeSave,
        removedFromSourceBeforeSave,
        panelAfterDrop: crossDropPanelAfterDrop,
        persistedInTarget,
        persistedInSource,
        panelAfterReload: crossDropPanelAfterReload,
      };
      if (targetFieldAfterPersist) {
        await dragDesignerFieldToGroup(page, targetFieldAfterPersist.index, crossDropSourceGroup.groupIndex);
        await page.waitForTimeout(1000);
        const crossGroupRestoreSaveEnabled = await page.getByRole("button", { name: "保存表单设置" }).isEnabled();
        crossGroupDrop.restoreSaveEnabled = crossGroupRestoreSaveEnabled;
        if (crossGroupRestoreSaveEnabled) {
          await page.getByRole("button", { name: "保存表单设置" }).click();
          await page.waitForFunction(() => !document.body.innerText.includes("表单设置已调整，保存后生效"), { timeout: 20000 });
          await page.reload({ waitUntil: "domcontentloaded" });
          await page.waitForSelector(".contract-form-settings", { timeout: 30000 });
        }
      }
    }
    await selectDesignerField(page, 0);
    await page.locator(".contract-field-central-create").click();
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
      orderButtonCount,
      draggableFieldCount,
      dragAutoScrollProbe,
      dropPlacementProbe,
      selectedFieldCount,
      selectedPanelText,
      operationLogTextAfterHide,
      operationLogTextAfterReset,
      operationLogTextAfterDrag,
      operationLogEntryCountAfterHide,
      initialFormDirtyCount,
      initialHiddenFieldDesignCount,
      initialHiddenGroupDesignCount,
      initialSaveFormEnabled,
      formDirtyAfterHide,
      hiddenFieldDesignCountAfterHide,
      saveFormEnabledAfterHide,
      resetFormEnabledAfterHide,
      formDirtyAfterReset,
      hiddenFieldDesignCountAfterReset,
      saveFormEnabledAfterReset,
      pageColumnsControlCount,
      pageColumnsDirtyAfterEdit,
      pageColumnsDirtyAfterRestore,
      groupVisibilityControlCount,
      groupVisibilityDirtyAfterHide,
      groupVisibilityDirtyAfterRestore,
      hiddenGroupDesignCountAfterHide,
      hiddenGroupDesignCountAfterRestore,
      groupColumnsControlCount,
      groupColumnsDirtyAfterEdit,
      groupColumnsDirtyAfterRestore,
      fieldSizeControlCount,
      fieldSizeDirtyAfterEdit,
      fieldSizeDirtyAfterRestore,
      groupRenameControlCount,
      groupRenameOriginalTitle,
      groupRenameTempTitle,
      groupRenamePanelAfterRename,
      groupRenamePanelAfterRestore,
      positionMoveControlCount,
      formOrderBeforePanelMove,
      formOrderAfterPanelMove,
      panelMoveResetSaveDisabled,
      selectedPanelBeforeMove,
      formOrderBeforeDragPersist,
      formOrderAfterDrag,
      operationLogHasTechnicalFieldAfterDrag,
      operationLogGroupColumnEntryCountAfterDrag,
      saveFormEnabledAfterDrag,
      formOrderAfterPersistReload,
      saveFormEnabledAfterRestoreDrag,
      formOrderAfterRestoreReload,
      crossGroupDrop,
      createFieldDialogText,
      createFieldLabelInputCount,
      createFieldTypeOptionCount,
      createFieldDialogClosed,
      returnButtonCount,
      legacyPanelCount,
      designerControlGridCount,
      designerInspectorCount,
      designerCanvasCount,
      designerWorkspaceCount,
      designerSidebarCount,
      designerSidebarHeadText,
      designerFieldNavigatorCount,
      designerFieldNavigatorHeaderText,
      designerFieldNavigatorItemCount,
      designerCanvasHeadText,
      designerInspectorSectionLabels,
      designerLayoutToolText,
    };
    report.artifacts.formDesigner = await captureStep(page, "form-designer");
    assert(designTitle === "当前页面字段配置", "表单设计器标题不正确", { designTitle });
    assert(
      leakedFormDesignerTerms.length === 0,
      "表单设计器默认面板露出了治理或技术话术",
      { leakedFormDesignerTerms },
    );
    assert(designFieldCount > 0, "表单设计器没有显示可配置字段数量", { designFieldCountText });
    assert(
      designerControlGridCount === 1
        && designerInspectorCount === 1
        && designerCanvasCount === 1
        && designerWorkspaceCount === 1
        && designerSidebarCount === 1
        && designerSidebarHeadText.includes("字段目录")
        && designerSidebarHeadText.includes("个字段")
        && designerSidebarHeadText.includes("个分组")
        && designerFieldNavigatorCount === 1
        && designerFieldNavigatorHeaderText.includes("分组导航")
        && designerFieldNavigatorItemCount > 0
        && designerCanvasHeadText.includes("表单画布")
        && designerInspectorSectionLabels.includes("基础属性")
        && designerInspectorSectionLabels.includes("布局与分组")
        && designerInspectorSectionLabels.includes("位置调整")
        && designerLayoutToolText.includes("页面布局"),
      "表单设计器没有形成专业配置面板结构",
      {
        designerControlGridCount,
        designerInspectorCount,
        designerCanvasCount,
        designerWorkspaceCount,
        designerSidebarCount,
        designerSidebarHeadText,
        designerFieldNavigatorCount,
        designerFieldNavigatorHeaderText,
        designerFieldNavigatorItemCount,
        designerCanvasHeadText,
        designerInspectorSectionLabels,
        designerLayoutToolText,
      },
    );
    assert(selectableFieldCount > 0, "表单设计器没有可点选字段", { selectableFieldCount });
    assert(dragHandleCount === 0, "表单设计器不应再显示六点拖拽把手", { dragHandleCount });
    assert(orderButtonCount === 0, "表单设计器不应再显示上下箭头排序按钮", { orderButtonCount });
    assert(draggableFieldCount > 0, "表单设计器字段块不可直接拖拽", { draggableFieldCount });
    assert(
      dragAutoScrollProbe.afterScrollY > dragAutoScrollProbe.beforeScrollY
        && dragAutoScrollProbe.dirtyAfterProbe === 0,
      "表单设计器长距离拖拽时未触发页面自动滚动",
      { dragAutoScrollProbe },
    );
    assert(
      dropPlacementProbe.fieldCount < 2
        || (
          dropPlacementProbe.beforeClassVisible
          && dropPlacementProbe.afterClassVisible
          && dropPlacementProbe.dirtyAfterProbe === 0
        ),
      "表单设计器拖拽时没有区分放到目标字段前后",
      { dropPlacementProbe },
    );
    assert(selectedFieldCount > 0 && selectedPanelText.includes("已选字段"), "表单字段点选后没有进入配置状态", {
      selectedFieldCount,
      selectedPanelText,
    });
    assert(
      operationLogEntryCountAfterHide > 0
        && operationLogTextAfterHide.includes("本次操作记录")
        && operationLogTextAfterHide.includes("隐藏字段")
        && operationLogTextAfterHide.includes("待保存")
        && operationLogTextAfterReset.includes("已撤销"),
      "表单配置没有记录当前用户操作",
      { operationLogTextAfterHide, operationLogTextAfterReset, operationLogEntryCountAfterHide },
    );
    assert(
      formDirtyAfterHide > 0
        && hiddenFieldDesignCountAfterHide > initialHiddenFieldDesignCount
        && saveFormEnabledAfterHide
        && resetFormEnabledAfterHide
        && formDirtyAfterReset === initialFormDirtyCount
        && hiddenFieldDesignCountAfterReset === initialHiddenFieldDesignCount
        && saveFormEnabledAfterReset === initialSaveFormEnabled,
      "表单字段显示隐藏草稿或重置不可用",
      {
        initialFormDirtyCount,
        initialHiddenFieldDesignCount,
        initialSaveFormEnabled,
        formDirtyAfterHide,
        hiddenFieldDesignCountAfterHide,
        saveFormEnabledAfterHide,
        resetFormEnabledAfterHide,
        formDirtyAfterReset,
        hiddenFieldDesignCountAfterReset,
        saveFormEnabledAfterReset,
      },
    );
    assert(selectedPanelBeforeMove.includes("已选字段"), "表单字段点选状态不可用", { selectedPanelBeforeMove });
    assert(
      pageColumnsControlCount > 0
        && pageColumnsDirtyAfterEdit > 0
        && groupVisibilityControlCount >= 2
        && groupVisibilityDirtyAfterHide > 0
        && groupColumnsControlCount > 0
        && fieldSizeControlCount > 0
        && fieldSizeDirtyAfterEdit > 0,
      "表单布局低代码配置能力不可用",
      {
        pageColumnsControlCount,
        initialHiddenGroupDesignCount,
        pageColumnsDirtyAfterEdit,
        pageColumnsDirtyAfterRestore,
        groupVisibilityControlCount,
        groupVisibilityDirtyAfterHide,
        groupVisibilityDirtyAfterRestore,
        hiddenGroupDesignCountAfterHide,
        hiddenGroupDesignCountAfterRestore,
        groupColumnsControlCount,
        groupColumnsDirtyAfterEdit,
        groupColumnsDirtyAfterRestore,
        fieldSizeControlCount,
        fieldSizeDirtyAfterEdit,
        fieldSizeDirtyAfterRestore,
      },
    );
    assert(
      groupRenameControlCount > 0
        && (
          !groupRenameOriginalTitle
          || (
            groupRenamePanelAfterRename.includes(groupRenameTempTitle)
            && groupRenamePanelAfterRestore.includes(groupRenameOriginalTitle)
          )
        ),
      "表单分组名称不能在字段配置面板自主编辑",
      {
        groupRenameControlCount,
        groupRenameOriginalTitle,
        groupRenameTempTitle,
        groupRenamePanelAfterRename,
        groupRenamePanelAfterRestore,
      },
    );
    assert(
      positionMoveControlCount > 0
        && (
          !panelMoveSourceLabel
          || !panelMoveTargetLabel
          || (
            formOrderAfterPanelMove.indexOf(panelMoveSourceLabel) > formOrderAfterPanelMove.indexOf(panelMoveTargetLabel)
            && panelMoveResetSaveDisabled
          )
        ),
      "表单字段面板定位移动不可用",
      {
        positionMoveControlCount,
        panelMoveSourceLabel,
        panelMoveTargetLabel,
        formOrderBeforePanelMove,
        formOrderAfterPanelMove,
        panelMoveResetSaveDisabled,
      },
    );
    assert(
      formOrderAfterDrag.indexOf(nextFieldLabel) >= 0
        && formOrderAfterDrag.indexOf(draggedFieldLabel) > formOrderAfterDrag.indexOf(nextFieldLabel)
        && operationLogTextAfterDrag.includes(nextFieldLabel)
        && !operationLogHasTechnicalFieldAfterDrag
        && operationLogGroupColumnEntryCountAfterDrag <= 1
        && (
          !saveFormEnabledAfterDrag
          || (
            formOrderAfterPersistReload.indexOf(nextFieldLabel) >= 0
            && formOrderAfterPersistReload.indexOf(draggedFieldLabel) > formOrderAfterPersistReload.indexOf(nextFieldLabel)
            && (
              !saveFormEnabledAfterRestoreDrag
              || (
                formOrderAfterRestoreReload.indexOf(draggedFieldLabel) >= 0
                && formOrderAfterRestoreReload.indexOf(nextFieldLabel) > formOrderAfterRestoreReload.indexOf(draggedFieldLabel)
              )
            )
          )
        ),
      "表单字段拖拽排序不可用",
      {
        sameGroupOrderProbe,
        orderSourceField,
        orderTargetField,
        formOrderBeforeDragPersist,
        formOrderAfterDrag,
        operationLogTextAfterDrag,
        operationLogHasTechnicalFieldAfterDrag,
        operationLogGroupColumnEntryCountAfterDrag,
        saveFormEnabledAfterDrag,
        formOrderAfterPersistReload,
        saveFormEnabledAfterRestoreDrag,
        formOrderAfterRestoreReload,
      },
    );
    assert(
      crossGroupDrop.skipped === false
        && crossGroupDrop.saveEnabled
        && crossGroupDrop.movedToTargetBeforeSave
        && crossGroupDrop.removedFromSourceBeforeSave
        && crossGroupDrop.panelAfterDrop.includes(crossGroupDrop.sourceField)
        && crossGroupDrop.persistedInTarget
        && !crossGroupDrop.persistedInSource,
      "表单字段跨分组拖拽保存刷新后没有保持",
      { crossGroupDrop },
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
    assert(inlineAddButtonCount === 0, "字段行不应显示分散新增字段按钮", { inlineAddButtonCount });
    assert(inlineVisibilityActionCount > 0, "字段行缺少显示隐藏操作", { inlineVisibilityActionCount });

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
      details: { currentStep, ...(err?.details || {}) },
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
