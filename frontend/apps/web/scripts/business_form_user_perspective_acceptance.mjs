import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:5174";
const DB_NAME = process.env.DB_NAME || "sc_demo";
const LOGIN = process.env.E2E_LOGIN || "wutao";
const PASSWORD = process.env.E2E_PASSWORD || "123456";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "business-form-user-perspective");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");

const CASES = [
  {
    code: "finance.loan.project_borrow_company",
    entryLabel: "借款办理",
    label: "项目借公司款登记",
    expected: ["办理类型", "项目与借款方", "项目借公司款", "办理说明"],
    forbidden: ["来源与系统追溯", "历史账户线索"],
  },
  {
    code: "settlement.income",
    entryLabel: "结算办理",
    label: "收入合同结算",
    expected: ["办理类型", "项目与发包人", "结算依据", "结算金额", "办理说明"],
    forbidden: ["来源与系统追溯", "历史来源表"],
  },
  {
    code: "finance.receipt.income.progress",
    entryLabel: "收款登记",
    label: "工程进度款收入登记",
    expected: ["办理类型", "项目与收款申请", "工程进度款收入", "收款账户"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.receipt.income.project",
    entryLabel: "收款登记",
    label: "到款确认",
    expected: ["办理类型", "项目与收款申请", "到款确认", "收款账户"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.receipt.income.residual",
    entryLabel: "收款登记",
    label: "其他/残余收款",
    expected: ["办理主信息", "项目与合同", "收款事项", "收款账户"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.self_funding.income",
    entryLabel: "自筹垫付办理",
    label: "自筹垫付办理",
    expected: ["办理类型", "项目与承包人", "自筹垫付金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.fund.transfer",
    entryLabel: "账户间资金往来",
    label: "账户间资金往来",
    expected: ["办理类型", "项目与账户", "金额", "办理说明"],
    forbidden: ["来源与系统追溯", "历史账户线索"],
  },
  {
    code: "finance.payment.apply.pay",
    entryLabel: "收付款申请办理",
    label: "付款申请",
    expected: ["办理类型", "项目与收款单位", "付款申请金额", "收款账户", "付款单位", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.payment.apply.receive",
    entryLabel: "收款申请",
    label: "收款申请",
    expected: ["收款申请", "项目", "申请金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.expense.reimbursement",
    entryLabel: "费用/扣款/保证金办理",
    label: "报销申请",
    expected: ["办理类型", "项目与往来单位", "报销金额", "收付款信息", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.deposit.bid.pay",
    entryLabel: "投标保证金支付",
    label: "投标保证金缴纳",
    expected: ["投标保证金支付", "项目", "保证金", "金额"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.deduction.bill",
    entryLabel: "费用/扣款/保证金办理",
    label: "扣款单",
    expected: ["扣款登记", "项目与往来单位", "扣款登记信息", "扣款单明细"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "finance.repayment.registration",
    entryLabel: "还款登记",
    label: "还款登记",
    expected: ["还款登记", "项目", "金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "material.inbound",
    label: "入库单",
    expected: ["办理类型", "项目与业务对象", "入库明细", "办理说明"],
    forbidden: ["来源与系统追溯"],
  },
  {
    code: "site.construction.diary",
    label: "施工日志",
    expected: ["项目与日志", "现场情况", "质量安全"],
    forbidden: ["来源与系统追溯"],
  },
  {
    code: "tax.deduction.registration",
    label: "抵扣登记",
    expected: ["办理类型", "项目与开票单位", "发票信息", "抵扣信息"],
    forbidden: ["来源与系统追溯"],
  },
  {
    code: "invoice.output.application",
    entryLabel: "票税办理",
    label: "销项开票申请",
    expected: ["办理类型", "项目与受票方", "开票申请信息", "本次开票金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "invoice.output.registration",
    entryLabel: "票税办理",
    label: "销项开票登记",
    expected: ["办理类型", "项目与受票方", "发票登记信息", "发票金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "invoice.input.report",
    entryLabel: "票税办理",
    label: "进项税额上报",
    expected: ["办理类型", "项目与供应商", "进项发票信息", "发票金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
  {
    code: "invoice.prepaid_tax",
    entryLabel: "票税办理",
    label: "预缴税款",
    expected: ["办理类型", "项目与税款归属", "预缴税款信息", "税款金额", "办理说明"],
    forbidden: ["来源与系统追溯", "迁移来源"],
  },
];

function findCachedChromiumExecutable() {
  const explicit = process.env.CHROMIUM_EXECUTABLE_PATH || process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || "";
  if (explicit && fsSync.existsSync(explicit)) {
    return explicit;
  }
  const cacheRoot = path.join(process.env.HOME || "", ".cache", "ms-playwright");
  if (!cacheRoot || !fsSync.existsSync(cacheRoot)) {
    return "";
  }
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

async function login(page) {
  await page.goto(`${BASE_URL}/login?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
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

function walk(nodes, fn) {
  for (const node of nodes || []) {
    if (!node || typeof node !== "object") {
      continue;
    }
    const found = fn(node);
    if (found) {
      return found;
    }
    const childFound = walk(Array.isArray(node.children) ? node.children : [], fn);
    if (childFound) {
      return childFound;
    }
  }
  return null;
}

function findCategoryNode(nav, code) {
  return walk(nav, (node) => {
    const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
    const allowedCodes = Array.isArray(meta.allowed_business_category_codes)
      ? meta.allowed_business_category_codes.map((item) => String(item || "").trim()).filter(Boolean)
      : [];
    if (String(meta.default_business_category_code || "").trim() === code || allowedCodes.includes(code)) {
      return {
        menuId: Number(node.menu_id || node.id || meta.menu_id || 0),
        actionId: Number(meta.action_id || 0),
        label: String(node.label || node.title || "").trim(),
      };
    }
    return null;
  });
}

function findLabelNode(nav, label) {
  const expected = String(label || "").trim();
  return walk(nav, (node) => {
    const nodeLabel = String(node.label || node.title || "").trim();
    if (nodeLabel !== expected) {
      return null;
    }
    const meta = node.meta && typeof node.meta === "object" ? node.meta : {};
    return {
      menuId: Number(node.menu_id || node.id || meta.menu_id || 0),
      actionId: Number(meta.action_id || 0),
      label: nodeLabel,
    };
  });
}

async function openCreateFromMenu(page, menuId, code, optionLabel = "") {
  await page.goto(`${BASE_URL}/m/${menuId}?db=${encodeURIComponent(DB_NAME)}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForURL((url) => url.pathname.startsWith("/a/") || url.pathname.startsWith("/m/"), { timeout: 60000 });
  await page.locator(".action-toolbar").waitFor({ state: "visible", timeout: 60000 });
  const createButton = page.locator(".action-toolbar button", { hasText: /新建|创建|新增|Create/i }).first();
  if (await createButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    await createButton.click();
  } else {
    await page.locator(".action-toolbar .toolbar-actions button").first().click();
  }
  await page.waitForTimeout(800);
  if (!page.url().includes("/new")) {
    const pickerText = optionLabel || code;
    const optionButton = page.locator("button", { hasText: pickerText }).last();
    if (await optionButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await optionButton.click();
    } else {
      const codeOption = page.locator("button", { hasText: code }).last();
      if (await codeOption.isVisible({ timeout: 5000 }).catch(() => false)) {
        await codeOption.click();
      }
    }
  }
  await page.waitForURL((url) => url.pathname.includes("/new"), { timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForFunction(
    () => !((document.body?.innerText || "").includes("加载表单中")),
    null,
    { timeout: 60000 },
  ).catch(() => {});
  await page.waitForTimeout(1000);
}

async function main() {
  await fs.rm(ARTIFACT_ROOT, { recursive: true, force: true });
  await fs.mkdir(ARTIFACT_ROOT, { recursive: true });
  const executablePath = findCachedChromiumExecutable();
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, locale: "zh-CN" });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text().slice(0, 500));
    }
  });
  page.on("pageerror", (err) => consoleErrors.push(err.message.slice(0, 500)));

  await login(page);
  const token = await readToken(page);
  if (!token) {
    throw new Error("login token missing");
  }
  const init = await intent(page, token, "system.init", {
    with_preload: false,
    with: ["workspace_home"],
    root_xmlid: "smart_construction_core.menu_sc_root",
  });
  const nav = init?.delivery_engine_v1?.nav || init?.nav || [];
  const results = [];
  const errors = [];

  for (const testCase of CASES) {
    const node = findCategoryNode(nav, testCase.code) || findLabelNode(nav, testCase.entryLabel || "");
    if (!node?.menuId) {
      errors.push(`${testCase.code}: menu node missing`);
      results.push({ ...testCase, ok: false, reason: "menu node missing" });
      continue;
    }
    await openCreateFromMenu(page, node.menuId, testCase.code, testCase.label);
    await page.waitForFunction(
      (expected) => {
        const text = document.body?.innerText || "";
        return expected.some((item) => text.includes(item))
          || text.includes("加载失败")
          || text.includes("初始化失败")
          || text.includes("暂无导航数据");
      },
      testCase.expected,
      { timeout: 60000 },
    ).catch(() => {});
    await page.waitForTimeout(300);
    const bodyText = await page.locator("body").innerText({ timeout: 30000 });
    const missing = testCase.expected.filter((text) => !bodyText.includes(text));
    const leaked = testCase.forbidden.filter((text) => bodyText.includes(text));
    const screenshotPath = path.join(ARTIFACT_ROOT, `${testCase.code.replaceAll(".", "_")}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    const ok = missing.length === 0 && leaked.length === 0;
    if (!ok) {
      errors.push(`${testCase.code}: missing=${missing.join(",")} leaked=${leaked.join(",")}`);
    }
    results.push({
      code: testCase.code,
      menuId: node.menuId,
      actionId: node.actionId,
      label: node.label,
      url: page.url(),
      missing,
      leaked,
      screenshotPath,
      ok,
    });
  }

  const report = {
    ok: errors.length === 0 && consoleErrors.length === 0,
    baseUrl: BASE_URL,
    dbName: DB_NAME,
    login: LOGIN,
    results,
    errors,
    consoleErrors,
  };
  await fs.writeFile(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  await browser.close();

  if (!report.ok) {
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(report, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
