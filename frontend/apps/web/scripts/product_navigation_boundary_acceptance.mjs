import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:18081";
const LOGIN = process.env.LOGIN || "admin";
const PASSWORD = process.env.PASSWORD || "admin";
const MENU_CONFIG_PATH = process.env.MENU_CONFIG_PATH || "/admin/menu-config?menu_id=646&action_id=841";

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  const inputs = page.locator("input.sc-input");
  await inputs.nth(0).fill(LOGIN);
  await inputs.nth(1).fill(PASSWORD);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL((url) => !String(url).includes("/login"), { timeout: 30000 });
  await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
}

function normalizeLabel(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, " ")
    .replace(/[0-9]+$/g, "");
}

async function mainNavigationLabels(page) {
  return page.evaluate(() => Array.from(document.querySelectorAll(".nav-shell .label"))
    .filter((el) => Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length))
    .map((el) => String(el.textContent || "").trim().replace(/\s+/g, " ")));
}

async function menuConfigTopLabels(page) {
  await page.goto(`${BASE_URL}${MENU_CONFIG_PATH}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".tree-scroll .tree-node[data-menu-id]", { timeout: 30000 });
  await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
  return page.evaluate(() => {
    const directNodes = Array.from(document.querySelectorAll(".tree-scroll > ul.config-tree-list > li > button.tree-node[data-menu-id]"));
    return directNodes
      .filter((el) => Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length))
      .map((button) => {
        const labelSpan = button.querySelector("span:not(.branch-marker):not(.menu-origin-badge)");
        return String(labelSpan?.textContent || button.textContent || "").trim().replace(/\s+/g, " ");
      });
  });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  try {
    await login(page);
    const labels = await mainNavigationLabels(page);
    const menuConfigLabels = await menuConfigTopLabels(page);
    const normalizedMainLabels = labels.map(normalizeLabel);
    const normalizedMenuConfigLabels = menuConfigLabels.map(normalizeLabel);
    const expectedPrefix = normalizedMainLabels.slice(0, normalizedMenuConfigLabels.length);
    const menuConfigAligned = normalizedMenuConfigLabels.length > 0
      && normalizedMenuConfigLabels.every((label, index) => label === expectedPrefix[index]);
    const result = {
      url: page.url(),
      labels,
      menu_config_top_labels: menuConfigLabels,
      has_lowcode_fact_spread: ["客户", "供应商", "一般合同", "材料合同"].every((label) => normalizedMainLabels.includes(label)),
      menu_config_has_lowcode_fact_spread: ["客户", "供应商", "一般合同", "材料合同"].every((label) => normalizedMenuConfigLabels.includes(label)),
      has_legacy_base_settings_group: normalizedMainLabels.some((label) => label.includes("基础设置") || label.includes("系统设置")),
      menu_config_has_legacy_base_settings_group: normalizedMenuConfigLabels.some((label) => label.includes("基础设置") || label.includes("系统设置")),
      has_config_center_group: normalizedMainLabels.some((label) => label.includes("配置中心")),
      menu_config_aligned_with_main_navigation: menuConfigAligned,
    };
    result.ok = !result.has_lowcode_fact_spread
      && !result.menu_config_has_lowcode_fact_spread
      && !result.has_legacy_base_settings_group
      && !result.menu_config_has_legacy_base_settings_group
      && result.has_config_center_group
      && result.menu_config_aligned_with_main_navigation;
    console.log(JSON.stringify(result, null, 2));
    assert(result.ok, "产品发布主导航与菜单配置默认树边界漂移", result);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("[product_navigation_boundary_acceptance] FAIL", error.message);
  if (error.details) console.error(JSON.stringify(error.details, null, 2));
  process.exit(1);
});
