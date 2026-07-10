import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "system-user-experience-shell");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");

function findCachedChromiumExecutable() {
  const explicit = process.env.CHROMIUM_EXECUTABLE_PATH || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "";
  if (explicit && fsSync.existsSync(explicit)) return explicit;
  const cacheRoot = path.join(process.env.HOME || "", ".cache", "ms-playwright");
  if (!cacheRoot || !fsSync.existsSync(cacheRoot)) return "";
  return fsSync.readdirSync(cacheRoot)
    .filter((name) => name.startsWith("chromium_headless_shell-") || name.startsWith("chromium-"))
    .sort()
    .reverse()
    .flatMap((name) => [
      path.join(cacheRoot, name, "chrome-headless-shell-linux64", "chrome-headless-shell"),
      path.join(cacheRoot, name, "chrome-linux64", "chrome"),
    ])
    .find((item) => fsSync.existsSync(item)) || "";
}

function slug(value) {
  return String(value || "")
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80) || "case";
}

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator("input").count() >= 3) {
    const db = page.locator("input").nth(2);
    if (await db.isEnabled().catch(() => false)) await db.fill(DB_NAME);
  }
  await page.locator('button[type="submit"]').click();
  await page.waitForFunction(() => !window.location.pathname.includes("/login"), null, { timeout: 60000 });
}

async function readToken(page) {
  return page.evaluate(() => {
    const key = Object.keys(sessionStorage).find((item) => item.startsWith("sc_auth_token")) || "";
    return key ? sessionStorage.getItem(key) : "";
  });
}

async function intent(page, token, intentName, params = {}) {
  return page.evaluate(async ({ token, intentName, params, dbName }) => {
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

function walk(nodes, fn) {
  for (const node of nodes || []) {
    if (!node || typeof node !== "object") continue;
    const found = fn(node);
    if (found) return found;
    const childFound = walk(Array.isArray(node.children) ? node.children : [], fn);
    if (childFound) return childFound;
  }
  return null;
}

function findLabelNode(nav, label) {
  const expected = String(label || "").trim();
  return walk(nav, (node) => {
    const nodeLabel = String(node.label || node.title || "").trim();
    if (nodeLabel !== expected) return null;
    const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
    return {
      menuId: Number(node.menu_id || node.id || meta.menu_id || 0),
      actionId: Number(meta.action_id || 0),
      label: nodeLabel,
    };
  });
}

async function visibleTechnicalTerms(page) {
  const text = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  const patterns = [
    /\b(action_id|view_id|root_menu_xmlid|role_key|scene_key)\b/gi,
    /\b(user_confirmed_|technical_|synced_from_|generated_from_|migrated_from_)\w*/gi,
    /对象\s+[a-z0-9_.]+/gi,
  ];
  return patterns
    .flatMap((pattern) => text.match(pattern) || [])
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .filter((item, index, items) => items.indexOf(item) === index);
}

async function pageEvidence(page, testCase) {
  await page.goto(testCase.url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(testCase.settleMs || 800);

  const bodyText = await page.locator("body").innerText({ timeout: 30000 });
  const missing = testCase.expected.filter((text) => !bodyText.includes(text));
  const forbiddenHits = (testCase.forbidden || []).filter((text) => bodyText.includes(text));
  const technicalTerms = testCase.allowTechnicalTerms ? [] : await visibleTechnicalTerms(page);
  const screenshotPath = path.join(ARTIFACT_ROOT, `${slug(testCase.key)}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const layout = await page.evaluate(() => ({
    path: window.location.pathname,
    pageMode: document.querySelector("[data-product-page-mode]")?.getAttribute("data-product-page-mode") || "",
    hasProductPage: Boolean(document.querySelector(".sc-page")),
    hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1 || document.body.scrollWidth > window.innerWidth + 1,
    title: document.title,
  }));
  const failures = [];
  if (missing.length) failures.push(`missing: ${missing.join(",")}`);
  if (forbiddenHits.length) failures.push(`forbidden visible text: ${forbiddenHits.join(",")}`);
  if (technicalTerms.length) failures.push(`technical terms visible: ${technicalTerms.join(",")}`);
  if (layout.hasHorizontalOverflow) failures.push("horizontal overflow");
  if (testCase.requireProductPage && !layout.hasProductPage) failures.push("missing sc-page shell");
  if (testCase.expectedMode && layout.pageMode !== testCase.expectedMode) {
    failures.push(`page mode mismatch expected=${testCase.expectedMode} actual=${layout.pageMode || "-"}`);
  }
  return {
    ...testCase,
    screenshotPath,
    layout,
    missing,
    forbiddenHits,
    technicalTerms,
    failures,
    ok: failures.length === 0,
  };
}

async function main() {
  await fs.rm(ARTIFACT_ROOT, { recursive: true, force: true });
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: "zh-CN" });
  const consoleErrors = [];
  const requestFailed = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 500));
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));
  page.on("requestfailed", (request) => {
    const failureText = request.failure()?.errorText || "";
    if (failureText.includes("net::ERR_ABORTED")) return;
    requestFailed.push(`${request.method()} ${request.url()} ${failureText}`.slice(0, 700));
  });

  await login(page);
  const token = await readToken(page);
  if (!token) throw new Error("login token missing");
  const init = await intent(page, token, "system.init", {
    with_preload: false,
    with: ["workspace_home"],
    root_xmlid: "smart_construction_core.menu_sc_root",
  });
  const nav = init?.delivery_engine_v1?.nav || init?.nav || [];
  const projectLedger = findLabelNode(nav, "项目台账");
  if (!projectLedger?.menuId) throw new Error("项目台账 menu node missing");

  const cases = [
    {
      key: "home",
      name: "首页首跳",
      url: `${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`,
      expected: ["当前角色", "今天先做什么", "今日优先动作", "角色能力摘要"],
      forbidden: ["HUD:", "role_key=", "scene_key="],
      requireProductPage: false,
    },
    {
      key: "my_work",
      name: "我的工作",
      url: `${BASE_URL}/my-work?db=${encodeURIComponent(DB_NAME)}`,
      expected: ["我的工作", "待办", "处理"],
      forbidden: ["role_key=", "scene_key="],
      requireProductPage: false,
    },
    {
      key: "project_ledger_list",
      name: "项目台账列表",
      url: `${BASE_URL}/m/${projectLedger.menuId}?db=${encodeURIComponent(DB_NAME)}`,
      expected: ["项目台账", "搜索"],
      forbidden: ["action_id", "view_id", "root_menu_xmlid"],
      expectedMode: "list",
      requireProductPage: true,
    },
    {
      key: "release_operator_access_boundary",
      name: "发布支持控制台权限边界",
      url: `${BASE_URL}/admin/release-operator?db=${encodeURIComponent(DB_NAME)}`,
      expected: ["项目列表"],
      forbidden: ["Traceback", "undefined", "发布控制台"],
      allowTechnicalTerms: true,
      settleMs: 1500,
    },
  ];

  const results = [];
  for (const testCase of cases) {
    results.push(await pageEvidence(page, testCase));
  }

  const mobilePage = await browser.newPage({ viewport: { width: 390, height: 900 }, locale: "zh-CN" });
  await login(mobilePage);
  results.push(await pageEvidence(mobilePage, {
    key: "mobile_home",
    name: "移动端首页",
    url: `${BASE_URL}/?db=${encodeURIComponent(DB_NAME)}`,
    expected: ["今天先做什么", "今日优先动作"],
    forbidden: ["HUD:", "role_key="],
    requireProductPage: false,
  }));
  await mobilePage.close();

  const failures = results.filter((row) => !row.ok);
  const report = {
    ok: failures.length === 0 && consoleErrors.length === 0 && requestFailed.length === 0,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    caseCount: results.length,
    failures,
    consoleErrors,
    requestFailed,
    results,
  };
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  await browser.close();
  if (!report.ok) {
    console.error(JSON.stringify({ ...report, results: results.map((row) => ({ key: row.key, name: row.name, ok: row.ok, failures: row.failures, layout: row.layout })) }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({ ok: true, caseCount: results.length, reportPath: REPORT_PATH }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
