import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:5174";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const ARTIFACT_ROOT = path.resolve(process.cwd(), "artifacts/playwright/business-form-all-category-direct");
const CATALOG_PATH = process.env.BUSINESS_CATEGORY_CATALOG_PATH || path.join(ARTIFACT_ROOT, "category_catalog.json");
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
    .replace(/[^a-zA-Z0-9\u4e00-\u9fa5._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 120) || "case";
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

function createUrl(category) {
  const params = new URLSearchParams({
    db: DB_NAME,
    menu_id: String(category.menu_id || category.action_id || 0),
    action_id: String(category.action_id || 0),
    product_domain: String(category.domain || ""),
    entry_intent: "handling",
    disposition_policy: "category_direct_acceptance",
    integration_target: `${category.model} ${category.name}`,
    entry_target_policy: "category_direct_acceptance",
    business_entry_contract_version: "business_entry_disposition.v1",
    current_business_category_code: category.code,
    default_business_category_code: category.code,
    ctx_source: "business_category_direct_acceptance",
  });
  return `${BASE_URL}/f/${encodeURIComponent(category.model)}/new?${params.toString()}`;
}

async function validateCategory(page, category) {
  await page.goto(createUrl(category), { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForURL((url) => url.pathname.includes("/new"), { timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForFunction(
    () => !((document.body?.innerText || "").includes("加载表单中")),
    null,
    { timeout: 60000 },
  ).catch(() => {});
  await page.waitForTimeout(500);
  const bodyText = await page.locator("body").innerText({ timeout: 30000 });
  const url = new URL(page.url());
  const screenshotPath = path.join(ARTIFACT_ROOT, `${slug(category.code)}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });

  const leaked = ["来源与系统追溯", "迁移来源", "历史账户线索", "legacy_"].filter((token) => bodyText.includes(token));
  const failures = [];
  if (url.searchParams.get("default_business_category_code") !== category.code) failures.push("default category code mismatch");
  if (url.searchParams.get("current_business_category_code") !== category.code) failures.push("current category code mismatch");
  if (bodyText.includes("加载表单中")) failures.push("form still loading");
  if (bodyText.includes("发生错误") || bodyText.includes("加载失败") || bodyText.includes("初始化失败")) failures.push("visible error state");
  if (!bodyText.includes("保存")) failures.push("form save action missing");
  if (!bodyText.includes("办理类型") && !bodyText.includes("项目") && !bodyText.includes("责任口径")) {
    failures.push("business form content missing");
  }
  if (leaked.length) failures.push(`create form leaked readonly/source text: ${leaked.join(",")}`);

  return {
    code: category.code,
    name: category.name,
    model: category.model,
    actionId: category.action_id,
    menuId: category.menu_id,
    url: page.url(),
    screenshotPath,
    leaked,
    failures,
    ok: failures.length === 0,
  };
}

async function main() {
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
  const catalog = JSON.parse(await fs.readFile(CATALOG_PATH, "utf8"));
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: "zh-CN" });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 500));
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));
  await login(page);

  const results = [];
  for (const category of catalog) {
    results.push(await validateCategory(page, category));
  }
  const failures = results.filter((row) => !row.ok);
  const report = {
    ok: failures.length === 0 && consoleErrors.length === 0,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    categoryCount: catalog.length,
    failures,
    consoleErrors,
    results,
  };
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  await browser.close();
  if (!report.ok) {
    console.error(JSON.stringify({ ...report, results: results.slice(0, 20) }, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({ ok: true, categoryCount: catalog.length, reportPath: REPORT_PATH }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
