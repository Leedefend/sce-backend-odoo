import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:5174";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";
const ARTIFACT_ROOT = path.resolve(
  process.cwd(),
  "artifacts/playwright/business-form-frontend-full-walk",
);
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
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.locator("input").nth(0).fill(LOGIN);
  await page.locator('input[type="password"]').fill(PASSWORD);
  if (await page.locator("input").count() >= 3) {
    const db = page.locator("input").nth(2);
    if (await db.isEnabled().catch(() => false)) {
      await db.fill(DB_NAME);
    }
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

function collectHandlingEntries(nav) {
  const rows = [];
  function walk(nodes, pathLabels = []) {
    for (const node of nodes || []) {
      if (!node || typeof node !== "object") continue;
      const label = String(node.label || node.title || "").trim();
      const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
      const target = meta.entry_target && typeof meta.entry_target === "object" ? meta.entry_target : {};
      const refs = target.compatibility_refs && typeof target.compatibility_refs === "object" ? target.compatibility_refs : {};
      const menuId = Number(node.menu_id || node.id || meta.menu_id || 0);
      const actionId = Number(meta.action_id || refs.action_id || 0);
      const model = String(refs.model || meta.model || "").trim();
      const categoryCode = String(meta.default_business_category_code || "").trim();
      const deliveryMode = String(refs.delivery_mode || "").trim();
      const currentPath = [...pathLabels, label].filter(Boolean);
      if (menuId > 0 && actionId > 0 && model && (categoryCode || deliveryMode === "merge_by_category_integration")) {
        rows.push({
          label,
          path: currentPath.join(" / "),
          menuId,
          actionId,
          model,
          categoryCode,
          deliveryMode,
        });
      }
      walk(Array.isArray(node.children) ? node.children : [], currentPath);
    }
  }
  walk(nav);
  return rows;
}

async function openEntryList(page, entry) {
  await page.goto(`${BASE_URL}/m/${entry.menuId}?db=${encodeURIComponent(DB_NAME)}`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.locator(".action-toolbar").waitFor({ state: "visible", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(500);
}

async function clickCreate(page) {
  const createButton = page.locator(".action-toolbar button", { hasText: /新建|创建|新增|Create/i }).first();
  if (await createButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    await createButton.click();
  } else {
    await page.locator(".action-toolbar button").filter({ hasText: "新建" }).first().click();
  }
  await page.waitForTimeout(800);
}

async function collectPickerOptions(page) {
  const bodyText = await page.locator("body").innerText({ timeout: 10000 });
  if (!bodyText.includes("选择办理类型")) return [];
  const buttons = await page.locator("button").evaluateAll((nodes) => nodes.map((node) => {
    const text = (node.innerText || node.textContent || "").trim();
    return { text };
  }));
  const seen = new Set();
  return buttons
    .map((row) => {
      const lines = String(row.text || "").split(/\n+/).map((item) => item.trim()).filter(Boolean);
      const code = lines.find((line) => /^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$/.test(line)) || "";
      const label = lines.find((line) => line !== code && !line.includes("选择办理类型")) || "";
      if (!code || seen.has(code)) return null;
      seen.add(code);
      return { code, label: label || code, text: row.text };
    })
    .filter(Boolean);
}

async function waitFormLoaded(page) {
  await page.waitForURL((url) => url.pathname.includes("/new"), { timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForFunction(
    () => !((document.body?.innerText || "").includes("加载表单中")),
    null,
    { timeout: 60000 },
  );
  await page.waitForTimeout(800);
}

async function validateCreatePage(page, row, screenshotName) {
  await waitFormLoaded(page);
  const bodyText = await page.locator("body").innerText({ timeout: 30000 });
  const screenshotPath = path.join(ARTIFACT_ROOT, `${screenshotName}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const url = new URL(page.url());
  const expectedCode = String(row.option?.code || row.categoryCode || "").trim();
  const defaultCode = url.searchParams.get("default_business_category_code") || "";
  const currentCode = url.searchParams.get("current_business_category_code") || "";
  const leaked = ["来源与系统追溯", "迁移来源", "历史账户线索", "legacy_"].filter((token) => bodyText.includes(token));
  const failures = [];
  if (!page.url().includes("/new")) failures.push("not on new form route");
  if (expectedCode && defaultCode !== expectedCode) {
    failures.push(`default_business_category_code mismatch expected=${expectedCode} actual=${defaultCode}`);
  }
  if (expectedCode && currentCode !== expectedCode) {
    failures.push(`current_business_category_code mismatch expected=${expectedCode} actual=${currentCode}`);
  }
  if (bodyText.includes("加载表单中")) failures.push("form still loading");
  if (bodyText.includes("发生错误") || bodyText.includes("加载失败")) failures.push("visible error state");
  if (leaked.length) failures.push(`create form leaked readonly/source text: ${leaked.join(",")}`);
  if (!bodyText.includes("保存")) failures.push("form save action missing");
  if (!bodyText.includes("办理类型") && !bodyText.includes("项目")) failures.push("business form content missing");
  return {
    ...row,
    url: page.url(),
    expectedCode,
    defaultCode,
    currentCode,
    screenshotPath,
    leaked,
    failures,
    ok: failures.length === 0,
  };
}

async function exerciseEntry(page, entry) {
  const results = [];
  await openEntryList(page, entry);
  await clickCreate(page);
  const options = await collectPickerOptions(page);
  if (options.length) {
    for (const option of options) {
      await openEntryList(page, entry);
      await clickCreate(page);
      const optionButton = page.locator("button", { hasText: option.code }).last();
      if (!(await optionButton.isVisible({ timeout: 10000 }).catch(() => false))) {
        results.push({
          ...entry,
          option,
          failures: [`picker option missing: ${option.code}`],
          ok: false,
        });
        continue;
      }
      await optionButton.click();
      results.push(await validateCreatePage(
        page,
        { ...entry, option },
        `${slug(entry.label)}_${slug(option.code)}`,
      ));
    }
    return results;
  }
  results.push(await validateCreatePage(
    page,
    { ...entry, option: entry.categoryCode ? { code: entry.categoryCode, label: entry.label } : null },
    `${slug(entry.label)}_${slug(entry.categoryCode || entry.model)}`,
  ));
  return results;
}

async function main() {
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: "zh-CN" });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 500));
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));

  await login(page);
  const token = await readToken(page);
  if (!token) throw new Error("login token missing");
  const init = await intent(page, token, "system.init", {
    with_preload: false,
    with: ["workspace_home"],
    root_xmlid: "smart_construction_core.menu_sc_root",
  });
  const nav = init?.delivery_engine_v1?.nav || init?.nav || [];
  const entries = collectHandlingEntries(nav);
  const results = [];
  for (const entry of entries) {
    const entryResults = await exerciseEntry(page, entry);
    results.push(...entryResults);
  }
  const failures = results.filter((row) => !row.ok);
  const report = {
    ok: failures.length === 0 && consoleErrors.length === 0,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    entryCount: entries.length,
    createCaseCount: results.length,
    entries,
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
  console.log(JSON.stringify({ ok: true, entryCount: entries.length, createCaseCount: results.length, reportPath: REPORT_PATH }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
