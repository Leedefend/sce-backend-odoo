import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const FORM_MODEL = process.env.LOW_CODE_STABILITY_FORM_MODEL || "sc.general.contract";
const FORM_ACTION_ID = Number(process.env.LOW_CODE_STABILITY_FORM_ACTION_ID || 669);
const ANALYSIS_MODEL = process.env.LOW_CODE_STABILITY_ANALYSIS_MODEL || "sc.account.income.expense.summary";
const ANALYSIS_ACTION_ID = Number(process.env.LOW_CODE_STABILITY_ANALYSIS_ACTION_ID || 681);

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

async function readToken(page) {
  return page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith("sc_auth_token")) || "";
    return key ? sessionStorage.getItem(key) : "";
  });
}

async function intent(page, intentName, params = {}) {
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
      throw new Error(JSON.stringify(body.error || body).slice(0, 1000));
    }
    return body.data || body;
  }, { dbName: DB_NAME, token, intentName, params });
}

function names(rows, key = "name") {
  return (Array.isArray(rows) ? rows : [])
    .map((row) => {
      if (typeof row === "string") return row.trim();
      if (row && typeof row === "object") return String(row[key] || row.field || row.name || "").trim();
      return "";
    })
    .filter(Boolean);
}

function sameOrderedPrefix(actual, expected) {
  return expected.every((item, index) => actual[index] === item);
}

function pickAvailableFields(audit, preferred, count) {
  const available = new Set(names(audit.available_model_fields || []));
  const out = [];
  for (const item of preferred) {
    if (available.has(item) && !out.includes(item)) out.push(item);
    if (out.length >= count) return out;
  }
  for (const item of available) {
    if (!out.includes(item)) out.push(item);
    if (out.length >= count) return out;
  }
  return out;
}

function resolveUnifiedPageContractV2ListProfile(contract) {
  const formal = contract?.layoutContract?.listProfile || contract?.layoutContract?.["list_profile"];
  if (formal && typeof formal === "object" && !Array.isArray(formal)) return formal;
  const rootFallback = contract?.["list_profile"];
  return rootFallback && typeof rootFallback === "object" && !Array.isArray(rootFallback) ? rootFallback : {};
}

function treeRuntimeColumns(contract) {
  const profile = resolveUnifiedPageContractV2ListProfile(contract);
  if (profile?.columns) return names(profile.columns);
  const widgets = contract?.layoutContract?.containerTree?.[0]?.widgetList;
  return names(widgets || [], "fieldCode");
}

function searchRuntimeFields(contract, key) {
  const search = contract?.searchContract || contract?.dataContract?.search || {};
  return names(search[key] || []);
}

async function contractSnapshot(page, { model, actionId, viewType }) {
  try {
    return await intent(page, "ui.business_config.contract.get", {
      model,
      action_id: actionId,
      view_type: viewType,
    });
  } catch (error) {
    const text = String(error?.message || error || "");
    if (text.includes("NOT_FOUND") || text.includes("未找到业务配置")) return null;
    throw error;
  }
}

function sanitizedContractJson(contractJson) {
  const copy = JSON.parse(JSON.stringify(contractJson || {}));
  delete copy.legacy_lowcode_draft;
  return copy;
}

async function restoreContract(page, snapshot) {
  if (!snapshot) return;
  await intent(page, "ui.business_config.contract.save", {
    name: snapshot.name,
    model: snapshot.model,
    view_type: snapshot.view_type,
    action_id: snapshot.action_id,
    view_id: snapshot.view_id,
    role_key: snapshot.role_key,
    contract_json: sanitizedContractJson(snapshot.contract_json),
    publish: snapshot.status === "published",
  });
}

async function verifyListSearch(page, report) {
  const treeSnapshot = await contractSnapshot(page, {
    model: FORM_MODEL,
    actionId: FORM_ACTION_ID,
    viewType: "tree",
  });
  const searchSnapshot = await contractSnapshot(page, {
    model: FORM_MODEL,
    actionId: FORM_ACTION_ID,
    viewType: "search",
  });
  const before = await intent(page, "ui.business_config.list_search.audit", {
    model: FORM_MODEL,
    action_id: FORM_ACTION_ID,
  });
  const listColumns = pickAvailableFields(before, ["contract_name", "contract_no", "amount_total", "company_id"], 3);
  const searchFilters = pickAvailableFields(before, ["contract_name", "contract_no", "archived", "company_id"], 2);
  const searchGroupBy = pickAvailableFields(before, ["company_id", "contract_type", "contract_direction", "project_id"], 2);
  assert(listColumns.length >= 3 && searchFilters.length >= 2 && searchGroupBy.length >= 2, "列表/搜索可配置字段不足", {
    listColumns,
    searchFilters,
    searchGroupBy,
    available: before.available_model_fields,
  });

  try {
    const changed = await intent(page, "ui.business_config.list_search.set", {
      model: FORM_MODEL,
      action_id: FORM_ACTION_ID,
      list_columns: listColumns,
      search_filters: searchFilters,
      search_group_by: searchGroupBy,
      publish: true,
    });
    const after = await intent(page, "ui.business_config.list_search.audit", {
      model: FORM_MODEL,
      action_id: FORM_ACTION_ID,
    });
    const tree = await intent(page, "ui.contract.v2", {
      model: FORM_MODEL,
      action_id: FORM_ACTION_ID,
      view_type: "tree",
    });
    const runtimeColumns = treeRuntimeColumns(tree);
    const runtimeFilters = searchRuntimeFields(tree, "filters");
    const runtimeGroupBy = searchRuntimeFields(tree, "group_by");

    assert(sameOrderedPrefix(after.business_config_list_columns || [], listColumns), "列表列保存后 audit 未生效", {
      expected: listColumns,
      actual: after.business_config_list_columns,
      changed,
    });
    assert(sameOrderedPrefix(after.business_config_search_filters || [], searchFilters), "搜索条件保存后 audit 未生效", {
      expected: searchFilters,
      actual: after.business_config_search_filters,
    });
    assert(sameOrderedPrefix(after.business_config_search_group_by || [], searchGroupBy), "搜索分组保存后 audit 未生效", {
      expected: searchGroupBy,
      actual: after.business_config_search_group_by,
    });
    assert(listColumns.every((field) => runtimeColumns.includes(field)), "列表列保存后运行契约未生效", {
      expected: listColumns,
      runtimeColumns,
    });
    assert(searchFilters.every((field) => runtimeFilters.includes(field)), "搜索条件保存后运行契约未生效", {
      expected: searchFilters,
      runtimeFilters,
    });
    assert(searchGroupBy.every((field) => runtimeGroupBy.includes(field)), "搜索分组保存后运行契约未生效", {
      expected: searchGroupBy,
      runtimeGroupBy,
    });

    report.listSearch = {
      saved: { listColumns, searchFilters, searchGroupBy },
      audit: {
        listColumns: after.business_config_list_columns,
        searchFilters: after.business_config_search_filters,
        searchGroupBy: after.business_config_search_group_by,
      },
      runtime: { runtimeColumns, runtimeFilters, runtimeGroupBy },
    };
  } finally {
    await restoreContract(page, treeSnapshot);
    await restoreContract(page, searchSnapshot);
  }
}

async function verifyAnalysis(page, report) {
  const before = await intent(page, "ui.business_config.analysis.audit", {
    model: ANALYSIS_MODEL,
    action_id: ANALYSIS_ACTION_ID,
  });
  const pivotMeasures = pickAvailableFields(before, ["income_amount", "expense_amount", "current_account_balance"], 2);
  const pivotDimensions = pickAvailableFields(before, ["account_type", "project_id", "row_level"], 2);
  const graphMeasures = pickAvailableFields(before, ["expense_amount", "income_amount", "current_bank_balance"], 2);
  const graphDimensions = pickAvailableFields(before, ["project_id", "account_type", "row_level"], 1);
  assert(
    pivotMeasures.length >= 2 && pivotDimensions.length >= 2 && graphMeasures.length >= 2 && graphDimensions.length >= 1,
    "分析视图可配置字段不足",
    { pivotMeasures, pivotDimensions, graphMeasures, graphDimensions, available: before.available_model_fields },
  );

  try {
    const changed = await intent(page, "ui.business_config.analysis.set", {
      model: ANALYSIS_MODEL,
      action_id: ANALYSIS_ACTION_ID,
      pivot_measures: pivotMeasures,
      pivot_dimensions: pivotDimensions,
      graph_measures: graphMeasures,
      graph_dimensions: graphDimensions,
      graph_type: "line",
      publish: true,
    });
    const after = await intent(page, "ui.business_config.analysis.audit", {
      model: ANALYSIS_MODEL,
      action_id: ANALYSIS_ACTION_ID,
    });

    assert(sameOrderedPrefix(after.pivot_measures || [], pivotMeasures), "透视指标保存后 audit 未生效", {
      expected: pivotMeasures,
      actual: after.pivot_measures,
      changed,
    });
    assert(sameOrderedPrefix(after.pivot_dimensions || [], pivotDimensions), "透视维度保存后 audit 未生效", {
      expected: pivotDimensions,
      actual: after.pivot_dimensions,
    });
    assert(sameOrderedPrefix(after.graph_measures || [], graphMeasures), "图表指标保存后 audit 未生效", {
      expected: graphMeasures,
      actual: after.graph_measures,
    });
    assert(sameOrderedPrefix(after.graph_dimensions || [], graphDimensions), "图表维度保存后 audit 未生效", {
      expected: graphDimensions,
      actual: after.graph_dimensions,
    });
    assert(after.graph_type === "line", "图表类型保存后 audit 未生效", {
      expected: "line",
      actual: after.graph_type,
    });

    const pivotContract = await intent(page, "ui.contract.v2", {
      model: ANALYSIS_MODEL,
      action_id: ANALYSIS_ACTION_ID,
      view_type: "pivot",
    });
    const graphContract = await intent(page, "ui.contract.v2", {
      model: ANALYSIS_MODEL,
      action_id: ANALYSIS_ACTION_ID,
      view_type: "graph",
    });
    assert(pivotContract.pageInfo?.viewType === "pivot", "透视运行契约不可用", { pageInfo: pivotContract.pageInfo });
    assert(graphContract.pageInfo?.viewType === "graph", "图表运行契约不可用", { pageInfo: graphContract.pageInfo });

    report.analysis = {
      saved: { pivotMeasures, pivotDimensions, graphMeasures, graphDimensions, graphType: "line" },
      audit: {
        pivotMeasures: after.pivot_measures,
        pivotDimensions: after.pivot_dimensions,
        graphMeasures: after.graph_measures,
        graphDimensions: after.graph_dimensions,
        graphType: after.graph_type,
      },
      runtime: {
        pivotViewType: pivotContract.pageInfo?.viewType,
        graphViewType: graphContract.pageInfo?.viewType,
      },
    };
  } finally {
    if (
      (before.pivot_measures || []).length
      || (before.pivot_dimensions || []).length
      || (before.graph_measures || []).length
      || (before.graph_dimensions || []).length
    ) {
      await intent(page, "ui.business_config.analysis.set", {
        model: ANALYSIS_MODEL,
        action_id: ANALYSIS_ACTION_ID,
        pivot_measures: before.pivot_measures || [],
        pivot_dimensions: before.pivot_dimensions || [],
        graph_measures: before.graph_measures || [],
        graph_dimensions: before.graph_dimensions || [],
        graph_type: before.graph_type || "bar",
        publish: true,
      });
    }
  }
}

async function verifyApproval(page, report) {
  const before = await intent(page, "sc.approval_policy.config.get", { model: FORM_MODEL });
  const scopeOptions = before.approval_scope_options || before.scope_options || [];
  const steps = before.steps || before.policy?.steps || [];
  assert(before.model === FORM_MODEL, "审批配置读取模型不一致", { before, expected: FORM_MODEL });
  assert(Array.isArray(scopeOptions) && scopeOptions.length > 0, "审批岗位选项不可用", {
    before,
  });
  assert(Array.isArray(steps), "审批步骤读取不可用", { before });
  report.approval = {
    model: before.model,
    approvalRequired: before.approval_required ?? before.policy?.approval_required,
    mode: before.mode || before.policy?.mode,
    scopeOptionCount: scopeOptions.length,
    stepCount: steps.length,
    runtimeApprovalRequired: before.runtime_approval_required,
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const report = {
    ok: false,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    formModel: FORM_MODEL,
    formActionId: FORM_ACTION_ID,
    analysisModel: ANALYSIS_MODEL,
    analysisActionId: ANALYSIS_ACTION_ID,
  };
  try {
    await login(page);
    await verifyListSearch(page, report);
    await verifyAnalysis(page, report);
    await verifyApproval(page, report);
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
