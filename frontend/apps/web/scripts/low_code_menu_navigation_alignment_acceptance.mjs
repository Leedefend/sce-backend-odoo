import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const ROOT_MENU_XMLID = process.env.LOW_CODE_MENU_ROOT_XMLID || "smart_construction_core.menu_sc_root";
const MENU_CONFIG_ROUTE = process.env.LOW_CODE_MENU_CONFIG_ROUTE
  || `/admin/menu-config?menu_id=646&action_id=841&root_menu_xmlid=${encodeURIComponent(ROOT_MENU_XMLID)}&return_to_business_config=1`;
const REQUIRED_CONFIG_TREE_ROWS = [
  { menuId: 465, label: "施工管理" },
  { menuId: 295, label: "物资与分包" },
  { menuId: 297, label: "配置中心" },
  { menuId: 646, label: "菜单配置" },
];

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

function normalize(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function menuIdOf(node) {
  const meta = node?.meta && typeof node.meta === "object" ? node.meta : {};
  for (const candidate of [node?.menu_id, meta.menu_id, node?.id]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function configMenuIdOf(node) {
  const meta = node?.meta && typeof node.meta === "object" ? node.meta : {};
  const configRef = (node?.config_ref && typeof node.config_ref === "object")
    ? node.config_ref
    : (meta.config_ref && typeof meta.config_ref === "object" ? meta.config_ref : {});
  const configRefModel = normalize(configRef.model || "ir.ui.menu");
  for (const candidate of [
    node?.config_menu_id,
    meta.config_menu_id,
    configRefModel === "ir.ui.menu" ? configRef.id : 0,
  ]) {
    const parsed = Number(candidate || 0);
    if (Number.isInteger(parsed) && parsed > 0) return parsed;
  }
  return 0;
}

function labelOf(node) {
  return normalize(node?.name || node?.label || node?.title);
}

function flattenTree(nodes, parent = null, out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== "object") continue;
    const menuId = menuIdOf(node);
    const label = labelOf(node);
    out.push({
      menuId,
      parentMenuId: parent?.menuId || 0,
      label,
      path: [...(parent?.path || []), label].filter(Boolean).join(" / "),
      node,
    });
    flattenTree(node.children, { menuId, path: [...(parent?.path || []), label].filter(Boolean) }, out);
  }
  return out;
}

function flattenNavigationContract(nodes, parent = null, out = []) {
  for (const node of Array.isArray(nodes) ? nodes : []) {
    if (!node || typeof node !== "object") continue;
    const menuId = menuIdOf(node);
    const configMenuId = configMenuIdOf(node);
    const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
    const label = labelOf(node);
    out.push({
      menuId,
      configMenuId,
      configurable: node.configurable ?? meta.configurable ?? null,
      configRef: node.config_ref || meta.config_ref || null,
      synthetic: meta.synthetic ?? null,
      nodeKind: normalize(meta.node_kind),
      label,
      path: [...(parent?.path || []), label].filter(Boolean).join(" / "),
      node,
    });
    flattenNavigationContract(node.children, { path: [...(parent?.path || []), label].filter(Boolean) }, out);
  }
  return out;
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

async function intentRequest(page, intent, params = {}) {
  const token = await authToken(page);
  const response = await page.evaluate(async ({ dbName, tokenValue, intentName, payload }) => {
    const resp = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: tokenValue ? `Bearer ${tokenValue}` : "",
        "X-Trace-Id": `low-code-menu-alignment-${Date.now()}`,
      },
      body: JSON.stringify({ intent: intentName, params: { db: dbName, ...payload } }),
    });
    const body = await resp.json().catch(() => ({}));
    return { status: resp.status, body };
  }, { dbName: DB_NAME, tokenValue: token, intentName: intent, payload: params });
  assert(response.status >= 200 && response.status < 300 && response.body?.ok === true, `${intent} 请求失败`, response);
  return response.body.data || {};
}

async function navigationRequest(page) {
  const token = await authToken(page);
  const response = await page.evaluate(async ({ dbName, tokenValue }) => {
    const resp = await fetch(`/api/menu/navigation?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: tokenValue ? `Bearer ${tokenValue}` : "",
        "X-Trace-Id": `low-code-menu-navigation-${Date.now()}`,
      },
      body: JSON.stringify({}),
    });
    const body = await resp.json().catch(() => ({}));
    return { status: resp.status, body };
  }, { dbName: DB_NAME, tokenValue: token });
  assert(response.status >= 200 && response.status < 300 && response.body?.ok === true, "业务办理导航请求失败", response);
  return response.body;
}

async function verifyMenuConfigTreeUi(page) {
  await page.goto(`${BASE_URL}${MENU_CONFIG_ROUTE}`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(
    () => !document.body.innerText.includes("正在加载菜单配置...") && /\d+ 个可配置菜单/.test(document.body.innerText),
    null,
    { timeout: 90000 },
  );
  const rows = await page.evaluate(() => Array.from(document.querySelectorAll(".tree-node")).map((element) => ({
    menuId: Number(element.getAttribute("data-menu-id") || 0),
    text: String(element.textContent || "").replace(/\s+/g, " ").trim(),
  })));
  const violations = [];
  const sample = [];
  for (const expected of REQUIRED_CONFIG_TREE_ROWS) {
    const row = rows.find((item) => item.menuId === expected.menuId || item.text.includes(expected.label));
    if (row) sample.push(row);
    if (!row) {
      violations.push({ ...expected, reason: "missing_tree_row" });
      continue;
    }
    if (row.menuId !== expected.menuId) {
      violations.push({ ...expected, actual_menu_id: row.menuId, text: row.text, reason: "tree_row_not_real_odoo_menu_id" });
    }
    if (row.text.includes("候选")) {
      violations.push({ ...expected, actual_menu_id: row.menuId, text: row.text, reason: "visible_group_rendered_as_candidate" });
    }
    if (!row.text.includes("启用")) {
      violations.push({ ...expected, actual_menu_id: row.menuId, text: row.text, reason: "visible_group_not_enabled_in_tree" });
    }
  }
  return {
    ok: violations.length === 0,
    checked: REQUIRED_CONFIG_TREE_ROWS.length,
    violations,
    sample,
  };
}

function expectedVisiblePolicies(audit, panel) {
  const runtimeStates = panel.runtime?.states || audit.runtime?.states || {};
  const runtimeExpected = Object.values(runtimeStates)
    .filter((state) => state && typeof state === "object" && state.runtime_visible === true)
    .map((state) => {
      const menuId = Number(state.menu_id || 0);
      const menu = (panel.menus || []).find((row) => Number(row.id || row.menu_id || 0) === menuId) || {};
      return {
        menuId,
        expectedLabel: normalize(menu.name || menu.display_name),
        labelExplicit: false,
        expectedParentId: 0,
        targetParentId: 0,
        configuredParentId: Number(menu.parent_id || 0),
        policyId: 0,
        menuCompleteName: normalize(menu.complete_name),
        runtimeState: normalize(state.runtime_state),
        runtimeReason: normalize(state.runtime_visibility_reason),
        runtimePath: normalize(state.runtime_path),
      };
    })
    .filter((row) => row.menuId > 0);
  if (runtimeExpected.length) return runtimeExpected;

  const menuById = new Map((panel.menus || []).map((menu) => [Number(menu.id || menu.menu_id || 0), menu]));
  const policyByMenuId = new Map((audit.applicable_policies || [])
    .map((policy) => [Number(policy.menu_id || 0), policy])
    .filter(([menuId]) => menuId > 0));
  const isPolicyVisible = (menuId) => policyByMenuId.get(menuId)?.visible === true;
  const effectiveVisibleParentId = (parentId) => {
    let currentId = Number(parentId || 0);
    const seen = new Set();
    while (currentId && !seen.has(currentId)) {
      seen.add(currentId);
      if (isPolicyVisible(currentId)) return currentId;
      const parentPolicy = policyByMenuId.get(currentId) || {};
      const parentMenu = menuById.get(currentId) || {};
      currentId = Number(parentPolicy.target_parent_menu_id || parentMenu.parent_id || 0);
    }
    return 0;
  };
  const rows = [];
  for (const policy of audit.applicable_policies || []) {
    const menuId = Number(policy.menu_id || 0);
    if (!menuId || policy.visible !== true) continue;
    const menu = menuById.get(menuId) || {};
    const configuredParentId = Number(policy.target_parent_menu_id || menu.parent_id || 0);
    const expectedParentId = effectiveVisibleParentId(configuredParentId);
    rows.push({
      menuId,
      expectedLabel: normalize(policy.custom_label || policy.menu_label || menu.name),
      labelExplicit: Boolean(normalize(policy.custom_label)),
      expectedParentId,
      targetParentId: Number(policy.target_parent_menu_id || 0),
      configuredParentId,
      policyId: Number(policy.id || 0),
      menuCompleteName: normalize(policy.menu_complete_name || menu.complete_name),
    });
  }
  return rows;
}

function analyzeAlignment({ audit, panel, navigation }) {
  const expected = expectedVisiblePolicies(audit, panel);
  const expectedById = new Map(expected.map((row) => [row.menuId, row]));
  const expectedIds = new Set(expectedById.keys());
  const runtimeStates = panel.runtime?.states || audit.runtime?.states || {};
  const navTree = navigation.nav_fact?.tree || navigation.nav_explained?.tree || [];
  const actual = flattenTree(navTree).filter((row) => row.menuId);
  const contractRows = flattenNavigationContract(navTree);
  const groupContractMismatches = REQUIRED_CONFIG_TREE_ROWS.flatMap((expected) => {
    const row = contractRows.find((item) => item.configMenuId === expected.menuId || item.menuId === expected.menuId || item.label === expected.label);
    if (!row) return [{ ...expected, reason: "missing_navigation_contract_row" }];
    const problems = [];
    if (row.configMenuId !== expected.menuId) {
      problems.push({ ...expected, actual_menu_id: row.menuId, actual_config_menu_id: row.configMenuId, path: row.path, reason: "navigation_group_not_mapped_to_real_odoo_menu" });
    }
    if (row.configurable !== true) {
      problems.push({ ...expected, actual_configurable: row.configurable, path: row.path, reason: "navigation_group_not_configurable" });
    }
    if (!row.configRef || Number(row.configRef.id || 0) !== expected.menuId || normalize(row.configRef.model || "ir.ui.menu") !== "ir.ui.menu") {
      problems.push({ ...expected, actual_config_ref: row.configRef, path: row.path, reason: "navigation_group_missing_config_ref" });
    }
    return problems;
  });
  const actualById = new Map();
  const duplicates = [];
  for (const row of actual) {
    if (actualById.has(row.menuId)) duplicates.push({ menu_id: row.menuId, first_path: actualById.get(row.menuId).path, duplicate_path: row.path });
    else actualById.set(row.menuId, row);
  }

  const missing = expected
    .filter((row) => !actualById.has(row.menuId))
    .map((row) => ({ menu_id: row.menuId, label: row.expectedLabel, policy_id: row.policyId, configured_path: row.menuCompleteName }));
  const isProtectedRuntimeConfigEntry = (row) => (
    normalize(row.label) === "菜单配置"
      && normalize(row.path).endsWith("配置中心 / 菜单配置")
  );
  const unexpected = actual
    .filter((row) => !expectedIds.has(row.menuId) && !isProtectedRuntimeConfigEntry(row))
    .map((row) => ({ menu_id: row.menuId, label: row.label, path: row.path }))
    .slice(0, 50);
  const runtimeHiddenButVisible = actual
    .filter((row) => {
      const state = runtimeStates[String(row.menuId)];
      return state && state.runtime_visible === false;
    })
    .map((row) => ({
      menu_id: row.menuId,
      label: row.label,
      path: row.path,
      runtime_state: runtimeStates[String(row.menuId)]?.runtime_state || "",
      runtime_reason: runtimeStates[String(row.menuId)]?.runtime_visibility_reason || "",
    }));
  const labelMismatches = expected
    .filter((row) => {
      const actualRow = actualById.get(row.menuId);
      return actualRow && row.labelExplicit && row.expectedLabel && actualRow.label !== row.expectedLabel;
    })
    .map((row) => ({
      menu_id: row.menuId,
      expected_label: row.expectedLabel,
      actual_label: actualById.get(row.menuId)?.label || "",
      actual_path: actualById.get(row.menuId)?.path || "",
    }));
  const parentMismatches = expected
    .filter((row) => {
      const actualRow = actualById.get(row.menuId);
      if (!actualRow) return false;
      if (!row.targetParentId) return false;
      if (!row.expectedParentId) return false;
      return Number(actualRow.parentMenuId || 0) !== Number(row.expectedParentId);
    })
    .map((row) => ({
      menu_id: row.menuId,
      label: row.expectedLabel,
      expected_parent_id: row.expectedParentId,
      actual_parent_id: actualById.get(row.menuId)?.parentMenuId || 0,
      actual_path: actualById.get(row.menuId)?.path || "",
    }));
  const userMenuConfig = navigation.meta?.user_menu_config || {};
  return {
    ok: expected.length > 0
      && missing.length === 0
      && unexpected.length === 0
      && runtimeHiddenButVisible.length === 0
      && duplicates.length === 0
      && labelMismatches.length === 0
      && parentMismatches.length === 0
      && groupContractMismatches.length === 0,
    summary: {
      base_url: BASE_URL,
      db: DB_NAME,
      login: LOGIN,
      root_menu_xmlid: ROOT_MENU_XMLID,
      runtime_source: audit.summary?.runtime_source || "",
      configured_policy_count: Number(audit.summary?.configured_policy_count || 0),
      applicable_policy_count: Number(audit.summary?.applicable_policy_count || 0),
      expected_visible_count: expected.length,
      actual_navigation_count: actual.length,
      menu_config_tree_count: 0,
      missing_count: missing.length,
      unexpected_count: unexpected.length,
      runtime_hidden_but_visible_count: runtimeHiddenButVisible.length,
      duplicate_count: duplicates.length,
      label_mismatch_count: labelMismatches.length,
      parent_mismatch_count: parentMismatches.length,
      group_contract_mismatch_count: groupContractMismatches.length,
      order_mismatch_count: 0,
      navigation_config_only: Boolean(userMenuConfig.nav_fact?.config_only ?? userMenuConfig.config_only),
    },
    missing,
    unexpected,
    runtimeHiddenButVisible,
    duplicates,
    labelMismatches,
    parentMismatches,
    groupContractMismatches,
    orderMismatches: [],
    actualSample: actual.slice(0, 20).map((row) => ({ menu_id: row.menuId, label: row.label, path: row.path })),
    menuConfigSample: [],
    expectedSample: expected.slice(0, 20),
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await login(page);
    const params = { root_menu_xmlid: ROOT_MENU_XMLID };
    const [panel, audit, navigation] = await Promise.all([
      intentRequest(page, "ui.menu_config.panel.get", params),
      intentRequest(page, "ui.menu_config.audit", params),
      navigationRequest(page),
    ]);
    const result = analyzeAlignment({ audit, panel, navigation });
    const menuConfigTreeUi = await verifyMenuConfigTreeUi(page);
    result.summary.menu_config_tree_ui_violation_count = menuConfigTreeUi.violations.length;
    result.menuConfigTreeUi = menuConfigTreeUi;
    result.menuConfigSample = menuConfigTreeUi.sample;
    result.ok = result.ok && menuConfigTreeUi.ok;
    console.log(JSON.stringify(result, null, 2));
    assert(result.ok, "菜单配置与最终业务办理导航未严格对齐", result);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("[low_code_menu_navigation_alignment_acceptance] FAIL", error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
