import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:5174";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "demo_full";
const PASSWORD = process.env.E2E_PASSWORD || "demo";

const ROOT_DIR = path.resolve(process.cwd(), "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright");
const SCREENSHOT_DIR = path.join(ARTIFACT_ROOT, "screenshots");
const LOG_DIR = path.join(ARTIFACT_ROOT, "logs");
const REPORT_PATH = path.join(LOG_DIR, "list_selection_contract_smoke.json");

const TARGETS = [
  { label: "finance", path: "/a/473?menu_id=273" },
  { label: "material", path: "/a/471?menu_id=305" },
];

function extractSelectionRows(data) {
  const rows = [];
  const addRows = (source, items) => {
    if (!Array.isArray(items)) return;
    for (const row of items) {
      const selection = String(row?.selection || "").trim().toLowerCase();
      if (selection !== "single" && selection !== "multi") continue;
      rows.push({
        source,
        key: String(row?.key || "").trim(),
        label: String(row?.label || "").trim(),
        selection,
        level: String(row?.level || "").trim(),
        visible_profiles: Array.isArray(row?.visible_profiles) ? row.visible_profiles : [],
      });
    }
  };
  addRows("buttons", data?.buttons);
  addRows("actions", data?.actions);
  addRows("toolbar.header", data?.toolbar?.header);
  addRows("toolbar.action", data?.toolbar?.action);
  return rows;
}

async function ensureDirs() {
  await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  await fs.mkdir(LOG_DIR, { recursive: true });
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.locator('input[autocomplete="username"]').fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('input[autocomplete="off"]').fill(DB_NAME);
  await page.getByRole("button", { name: "登录" }).click();
  await page.waitForTimeout(3000);
}

async function inspectTarget(page, target, captures) {
  captures.length = 0;
  await page.goto(`${BASE_URL}${target.path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  const rowCheckbox = page.locator('tbody input[type="checkbox"]').first();
  const rowCount = await page.locator("tbody tr").count().catch(() => 0);
  if (await rowCheckbox.count()) {
    await rowCheckbox.check({ force: true });
    await page.waitForTimeout(1000);
  }

  const domButtons = await page.locator(".batch-bar button").allTextContents().catch(() => []);
  const actionButtons = domButtons
    .map((item) => String(item || "").trim())
    .filter((item) => item && item !== "清空");
  const selectionRows = captures.flatMap((capture) => capture.selectionRows || []);
  const contractLabels = selectionRows.map((row) => row.label).filter(Boolean);
  const matchedLabels = actionButtons.filter((label) => contractLabels.includes(label));
  const screenshotPath = path.join(SCREENSHOT_DIR, `list_selection_${target.label}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });

  return {
    target,
    url: page.url(),
    title: await page.locator("h1").first().textContent().catch(() => ""),
    rowCount,
    domButtons,
    actionButtons,
    contractLabels,
    matchedLabels,
    captures: [...captures],
    screenshotPath,
    ok: selectionRows.length > 0 && actionButtons.length > 0 && matchedLabels.length > 0,
  };
}

async function main() {
  await ensureDirs();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 } });
  const captures = [];

  await page.addInitScript(() => {
    const noop = () => {};
    console.debug = noop;
  });

  page.on("response", async (response) => {
    try {
      if (!response.url().includes("/api/v1/intent")) return;
      const request = response.request();
      const postData = request.postDataJSON?.();
      if (!postData || postData.intent !== "ui.contract") return;
      const body = await response.json();
      const data = body?.data || {};
      captures.push({
        params: postData.params || {},
        head: data.head || {},
        selectionRows: extractSelectionRows(data),
      });
    } catch {}
  });

  await login(page);

  const results = [];
  for (const target of TARGETS) {
    results.push(await inspectTarget(page, target, captures));
  }

  await browser.close();

  const report = {
    ok: results.every((item) => item.ok),
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    results,
  };
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");

  if (!report.ok) {
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }

  console.log(JSON.stringify(report, null, 2));
}

await main();
