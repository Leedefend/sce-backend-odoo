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

async function main() {
  await ensureDirs();
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 }, locale: "zh-CN" });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text().slice(0, 500));
    }
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));

  await login(page);
  await page.goto(`${BASE_URL}${SCENE_PATH}?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
  await page.locator(".handling-surface").waitFor({ state: "visible", timeout: 60000 });
  await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });

  const groupTitles = await page.locator(".handling-group__header h4").allTextContents();
  const itemLabels = await page.locator(".handling-item span").allTextContents();
  const bodyText = await page.locator("body").innerText({ timeout: 10000 });
  const rawCodeVisible = /finance\.|invoice\.|tax\.certificate/.test(bodyText);
  const expectedGroups = ["收付款办理", "开票与税务办理", "费用与报销办理", "资金往来办理"];
  const missingGroups = expectedGroups.filter((title) => !groupTitles.includes(title));

  const report = {
    ok: missingGroups.length === 0 && groupTitles.length === 4 && itemLabels.length === 35 && !rawCodeVisible && consoleErrors.length === 0,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    scenePath: SCENE_PATH,
    groupTitles,
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
