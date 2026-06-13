import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:5174";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const SCENE_PATH = process.env.SCENE_PATH || "/s/finance.workspace";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright");
const SCREENSHOT_DIR = path.join(ARTIFACT_ROOT, "screenshots");
const LOG_DIR = path.join(ARTIFACT_ROOT, "logs");
const REPORT_PATH = path.join(LOG_DIR, "handling_entry_catalog_smoke.json");
const SCREENSHOT_PATH = path.join(SCREENSHOT_DIR, "handling_entry_catalog_finance_workspace.png");

function findCachedChromiumExecutable() {
  const explicit = process.env.CHROMIUM_EXECUTABLE_PATH || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "";
  if (explicit && fsSync.existsSync(explicit)) {
    return explicit;
  }
  const cacheRoot = path.join(process.env.HOME || "", ".cache", "ms-playwright");
  if (!cacheRoot || !fsSync.existsSync(cacheRoot)) {
    return "";
  }
  const candidates = fsSync.readdirSync(cacheRoot)
    .filter((name) => name.startsWith("chromium_headless_shell-") || name.startsWith("chromium-"))
    .sort()
    .reverse()
    .flatMap((name) => [
      path.join(cacheRoot, name, "chrome-headless-shell-linux64", "chrome-headless-shell"),
      path.join(cacheRoot, name, "chrome-linux64", "chrome"),
    ]);
  return candidates.find((item) => fsSync.existsSync(item)) || "";
}

async function ensureDirs() {
  await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  await fs.mkdir(LOG_DIR, { recursive: true });
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator("input").count() >= 3) {
    const db = page.locator("input").nth(2);
    if (await db.isEnabled().catch(() => false)) {
      await db.fill(DB_NAME);
    }
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForLoadState("networkidle", { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1000);
}

async function readAuthToken(page) {
  return await page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith("sc_auth_token")) || "";
    return key ? sessionStorage.getItem(key) : "";
  });
}

async function intent(page, token, intentName, params = {}) {
  return await page.evaluate(async ({ token, intentName, params, dbName }) => {
    const res = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Odoo-DB": dbName,
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ intent: intentName, params, meta: { startup_chain_bypass: true } }),
    });
    const body = await res.json();
    if (!res.ok || body.ok === false) {
      throw new Error(JSON.stringify(body.error || body).slice(0, 700));
    }
    return body.data || body;
  }, { token, intentName, params, dbName: DB_NAME });
}

async function revealSidebarLabel(page, targetLabel) {
  const target = page.locator('[data-component="SidebarNav"] button.label', { hasText: targetLabel }).first();
  if (await target.isVisible({ timeout: 500 }).catch(() => false)) {
    return;
  }
  for (const label of ["项目中心", "物资与分包", "财务中心", "人事行政"]) {
    const button = page.locator('[data-component="SidebarNav"] button.label', { hasText: label }).first();
    if (await button.count()) {
      await button.click().catch(() => {});
      await page.waitForTimeout(150);
    }
    if (await target.isVisible({ timeout: 500 }).catch(() => false)) {
      return;
    }
  }
  const intentButtons = await page.locator('[data-component="SidebarNav"] button.label', { hasText: "办理入口" }).count();
  for (let index = 0; index < intentButtons; index += 1) {
    await page.locator('[data-component="SidebarNav"] button.label', { hasText: "办理入口" }).nth(index).click().catch(() => {});
    await page.waitForTimeout(150);
    if (await target.isVisible({ timeout: 500 }).catch(() => false)) {
      return;
    }
  }
}

async function openFinanceWorkspace(page, targetLabel = "") {
  await page.goto(`${BASE_URL}${SCENE_PATH}?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
  await page.locator(".handling-surface").waitFor({ state: "visible", timeout: 60000 });
  if (targetLabel) {
    await revealSidebarLabel(page, targetLabel);
  } else {
    for (const label of ["项目中心", "物资与分包", "财务中心", "人事行政"]) {
      const button = page.locator('[data-component="SidebarNav"] button.label', { hasText: label }).first();
      if (await button.count()) {
        await button.click().catch(() => {});
      }
    }
  }
  await page.waitForTimeout(500);
}

function findNodeByLabel(nodes, label) {
  for (const node of nodes || []) {
    if (!node || typeof node !== "object") {
      continue;
    }
    if (String(node.label || node.title || "").trim() === label) {
      return node;
    }
    const found = findNodeByLabel(Array.isArray(node.children) ? node.children : [], label);
    if (found) {
      return found;
    }
  }
  return null;
}

function findBusinessCategoryNode(nodes, preferredLabels = []) {
  const preferred = new Set(preferredLabels.map((item) => String(item || "").trim()).filter(Boolean));
  let fallback = null;
  function walk(source) {
    for (const node of source || []) {
      if (!node || typeof node !== "object") {
        continue;
      }
      const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
      const categoryCode = String(meta.default_business_category_code || "").trim();
      const menuId = Number(node.menu_id || node.id || meta.menu_id || 0);
      const actionId = Number(meta.action_id || 0);
      const label = String(node.label || node.title || "").trim();
      if (categoryCode && menuId > 0 && actionId > 0) {
        const row = { node, meta, categoryCode, menuId, actionId, label };
        if (preferred.has(label)) {
          return row;
        }
        fallback = fallback || row;
      }
      const found = walk(Array.isArray(node.children) ? node.children : []);
      if (found) {
        return found;
      }
    }
    return null;
  }
  return walk(nodes) || fallback;
}

async function main() {
  await ensureDirs();
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 }, locale: "zh-CN" });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const location = msg.location();
      const url = String(location?.url || "");
      if (!url.endsWith("/favicon.ico")) {
        consoleErrors.push(msg.text().slice(0, 500));
      }
    }
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));

  await login(page);
  const token = await readAuthToken(page);
  if (!token) {
    throw new Error("login token missing");
  }
  const init = await intent(page, token, "system.init", {
    with_preload: false,
    with: ["workspace_home"],
    root_xmlid: "smart_construction_core.menu_sc_root",
  });
  const deliveryNav = init?.delivery_engine_v1?.nav || init?.nav || [];
  const financeNode = findNodeByLabel(deliveryNav, "财务中心");
  const financeChildren = Array.isArray(financeNode?.children) ? financeNode.children : [];
  const financeChildLabels = financeChildren.map((node) => String(node?.label || node?.title || "").trim()).filter(Boolean);
  const blockedIntentGroupLabels = ["办理入口", "台账查询", "分析报表", "来源明细", "基础配置"];
  const leakedFinanceIntentGroups = financeChildLabels.filter((label) => blockedIntentGroupLabels.includes(label));
  const financeHandlingLabels = financeChildLabels;
  const expectedFinanceHandlingLabels = [
    "收款登记",
    "付款执行",
    "付款申请",
    "票税办理",
    "费用/扣款/保证金办理",
    "借款办理",
    "还款办理",
    "账户间资金往来",
    "自筹垫付办理",
    "自筹退回办理",
  ];
  const missingFinanceHandlingLabels = expectedFinanceHandlingLabels.filter((label) => !financeHandlingLabels.includes(label));
  const duplicateFinanceHandlingLabels = financeHandlingLabels.filter((label, index) => financeHandlingLabels.indexOf(label) !== index);
  const leakedFinanceHandlingLabels = [
    "自筹保证金",
    "自筹垫付收入",
    "自筹垫付退回",
    "保证金退回办理",
    "保证金退还办理",
    "支付申请",
    "报销申请",
    "扣款单",
    "进项发票",
    "销项开票申请",
    "销项开票登记",
    "预缴税款",
  ].filter((label) => financeHandlingLabels.includes(label));
  const financeEntry = financeChildren[0] || {};
  const financeEntryMeta = financeEntry.meta || {};
  const financeEntryTarget = financeEntryMeta.entry_target || {};
  const categoryNode = findBusinessCategoryNode(deliveryNav, ["支付申请", "报销申请", "采购计划", "收入合同"]);
  if (!categoryNode) {
    throw new Error("productized business category menu node missing");
  }
  await openFinanceWorkspace(page);
  await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });

  const groupTitles = await page.locator(".handling-group__header h4").allTextContents();
  const itemLabels = await page.locator(".handling-item span").allTextContents();
  const sidebarLabels = await page.locator('[data-component="SidebarNav"] button.label .label-text').evaluateAll((nodes) =>
    nodes.map((node) => (node.textContent || "").trim()).filter(Boolean)
  );
  const sidebarIntentLabels = sidebarLabels.filter((label) => blockedIntentGroupLabels.includes(label));
  const expectedMergeFamilyLabels = ["费用/扣款/保证金办理", "票税办理"];
  const missingMergeFamilyLabels = expectedMergeFamilyLabels.filter((label) => !sidebarLabels.includes(label));
  const hiddenLegacyHandlingLabels = ["报销申请", "扣款单", "进项发票", "销项开票申请", "销项开票登记", "预缴税款"];
  const leakedLegacyHandlingLabels = hiddenLegacyHandlingLabels.filter((label) => sidebarLabels.includes(label));
  const leakedLegacyHandlingCards = hiddenLegacyHandlingLabels.filter((label) => itemLabels.includes(label));
  const bodyText = await page.locator("body").innerText({ timeout: 10000 });
  const rawCodeVisible = /finance\.|invoice\.|tax\.certificate/.test(bodyText);
  const expectedGroups = ["收付款办理", "开票与税务办理", "费用与报销办理", "资金往来办理"];
  const expectedCatalogItems = ["收款登记", "付款执行", "票税办理", "费用/扣款/保证金办理", "借款办理", "还款办理"];
  const missingGroups = expectedGroups.filter((title) => !groupTitles.includes(title));
  const missingCatalogItems = expectedCatalogItems.filter((label) => !itemLabels.includes(label));
  const catalogEntryNavigation = [];
  for (const label of ["票税办理", "费用/扣款/保证金办理"]) {
    await openFinanceWorkspace(page);
    const entryButton = page.locator(".handling-item", { hasText: label }).first();
    if (!(await entryButton.isVisible({ timeout: 30000 }).catch(() => false))) {
      throw new Error(`catalog entry button missing: ${label}`);
    }
    const previousUrl = page.url();
    await entryButton.click();
    await page.waitForURL((url) => {
      const actionId = Number(url.searchParams.get("action_id") || 0);
      return url.href !== previousUrl
        && url.pathname.startsWith("/a/")
        && actionId > 0
        && !url.searchParams.get("default_business_category_code")
        && !url.searchParams.get("current_business_category_code");
    }, { timeout: 60000 });
    await page.locator(".action-toolbar").waitFor({ state: "visible", timeout: 60000 });
    catalogEntryNavigation.push({ label, resolvedUrl: page.url() });
  }
  const mergeFamilyNavigation = [];
  for (const label of expectedMergeFamilyLabels) {
    await openFinanceWorkspace(page, label);
    const familyButton = page.locator('[data-component="SidebarNav"] button.label', { hasText: label }).first();
    if (!(await familyButton.isVisible({ timeout: 30000 }).catch(() => false))) {
      throw new Error(`merge family button missing: ${label}`);
    }
    const previousUrl = page.url();
    await familyButton.click();
    await page.waitForURL((url) => {
      const actionId = Number(url.searchParams.get("action_id") || 0);
      return url.href !== previousUrl
        && url.pathname.startsWith("/a/")
        && actionId > 0
        && !url.searchParams.get("default_business_category_code")
        && !url.searchParams.get("current_business_category_code");
    }, { timeout: 60000 });
    await page.locator(".action-toolbar").waitFor({ state: "visible", timeout: 60000 });
    mergeFamilyNavigation.push({ label, resolvedUrl: page.url() });
  }

  await page.goto(`${BASE_URL}/m/${categoryNode.menuId}?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForURL((url) => (
    url.searchParams.get("default_business_category_code") === categoryNode.categoryCode
    && url.searchParams.get("current_business_category_code") === categoryNode.categoryCode
  ), { timeout: 60000 });
  await page.locator(".action-toolbar").waitFor({ state: "visible", timeout: 60000 });
  const menuResolvedUrl = page.url();
  const createButton = page.locator(".action-toolbar .toolbar-actions button").first();
  if (!(await createButton.isVisible({ timeout: 30000 }).catch(() => false))) {
    throw new Error(`create button missing for productized entry ${categoryNode.label}`);
  }
  await createButton.click();
  await page.waitForURL((url) => (
    url.pathname.includes("/new")
    && url.searchParams.get("default_business_category_code") === categoryNode.categoryCode
  ), { timeout: 60000 });
  const createResolvedUrl = page.url();

  const report = {
    ok: missingGroups.length === 0 && groupTitles.length === 4 && itemLabels.length === 13 && !rawCodeVisible && consoleErrors.length === 0
      && sidebarIntentLabels.length === 0
      && missingCatalogItems.length === 0
      && missingMergeFamilyLabels.length === 0
      && leakedFinanceIntentGroups.length === 0
      && missingFinanceHandlingLabels.length === 0
      && duplicateFinanceHandlingLabels.length === 0
      && leakedFinanceHandlingLabels.length === 0
      && leakedLegacyHandlingLabels.length === 0
      && leakedLegacyHandlingCards.length === 0
      && catalogEntryNavigation.length === 2
      && catalogEntryNavigation.every((item) => item.resolvedUrl.includes("action_id=") && !item.resolvedUrl.includes("default_business_category_code="))
      && mergeFamilyNavigation.length === expectedMergeFamilyLabels.length
      && mergeFamilyNavigation.every((item) => item.resolvedUrl.includes("/a/") && !item.resolvedUrl.includes("default_business_category_code="))
      && menuResolvedUrl.includes(`default_business_category_code=${encodeURIComponent(categoryNode.categoryCode)}`)
      && createResolvedUrl.includes(`default_business_category_code=${encodeURIComponent(categoryNode.categoryCode)}`),
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    scenePath: SCENE_PATH,
    financeChildLabels,
    financeHandlingLabels,
    leakedFinanceIntentGroups,
    missingFinanceHandlingLabels,
    duplicateFinanceHandlingLabels,
    leakedFinanceHandlingLabels,
    financeEntryTarget,
    categoryNavigation: {
      label: categoryNode.label,
      menuId: categoryNode.menuId,
      actionId: categoryNode.actionId,
      categoryCode: categoryNode.categoryCode,
      menuResolvedUrl,
      createResolvedUrl,
    },
    mergeFamilyNavigation,
    groupTitles,
    sidebarIntentLabels,
    missingCatalogItems,
    missingMergeFamilyLabels,
    leakedLegacyHandlingLabels,
    leakedLegacyHandlingCards,
    catalogEntryNavigation,
    itemCount: itemLabels.length,
    missingGroups,
    rawCodeVisible,
    consoleErrors,
    screenshotPath: SCREENSHOT_PATH,
    executablePath,
  };
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  await browser.close();

  if (!report.ok) {
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(report, null, 2));
}

await main();
