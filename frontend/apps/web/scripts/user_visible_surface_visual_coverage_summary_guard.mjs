import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const REPORT_PATH = process.env.REPORT_PATH
  || path.join(ROOT_DIR, "artifacts", "playwright", "user-visible-surface-visual-coverage", "report.json");
const MIN_ACTIONS = Number(process.env.MIN_ACTIONS || 80);

function fail(message, details = {}) {
  const error = new Error(message);
  error.details = details;
  throw error;
}

async function readJson(filePath) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (err) {
    fail(`cannot read visual coverage report: ${filePath}`, { error: err instanceof Error ? err.message : String(err) });
  }
}

function countArray(value) {
  return Array.isArray(value) ? value.length : 0;
}

function missingScreenshots(rows) {
  return rows
    .filter((row) => row?.ok === true)
    .filter((row) => !row.screenshotPath || !fsSync.existsSync(row.screenshotPath))
    .slice(0, 20)
    .map((row) => ({ path: row.path, route: row.route, screenshotPath: row.screenshotPath || "" }));
}

function placeholderHeaderRows(rows) {
  return rows
    .map((row) => ({
      path: row?.path || "",
      route: row?.route || "",
      headers: Array.isArray(row?.headers)
        ? row.headers.filter((header) => /历史验收可见字段|测试字段|占位字段/.test(String(header || "")))
        : [],
      screenshotPath: row?.screenshotPath || "",
    }))
    .filter((row) => row.headers.length)
    .slice(0, 20);
}

function auditHeaderRows(rows) {
  const auditHeaderPattern = /^(Created by|Created on|Last Updated by|Last Updated on)$/i;
  return rows
    .map((row) => ({
      path: row?.path || "",
      route: row?.route || "",
      headers: Array.isArray(row?.headers)
        ? row.headers.filter((header) => auditHeaderPattern.test(String(header || "").trim()))
        : [],
      screenshotPath: row?.screenshotPath || "",
    }))
    .filter((row) => row.headers.length)
    .slice(0, 20);
}

function missingRequiredBusinessHeaders(rows) {
  const requiredByAction = new Map([
    [581, ["采购单号", "项目", "供应商", "合计金额", "订单状态"]],
    [786, ["客户类型", "单位名称", "业务身份", "业务依据"]],
    [787, ["单位名称", "供应商类型", "业务身份", "业务依据"]],
    [753, ["结算单号", "合同名称", "合同总额", "往来单位", "未付款金额"]],
    [754, ["单据状态", "单据编号", "项目名称", "结算单位", "结算金额"]],
    [1009, ["业务模型", "视图类型", "业务入口", "发布状态", "版本"]],
  ]);
  return rows
    .map((row) => {
      const actionId = Number(row?.actionId || 0);
      const required = requiredByAction.get(actionId) || [];
      const headers = Array.isArray(row?.headers) ? row.headers.map((header) => String(header || "").trim()).filter(Boolean) : [];
      const missing = required.filter((label) => !headers.includes(label));
      return {
        actionId,
        path: row?.path || "",
        route: row?.route || "",
        missing,
        headers,
        screenshotPath: row?.screenshotPath || "",
      };
    })
    .filter((row) => row.missing.length)
    .slice(0, 20);
}

async function main() {
  const report = await readJson(REPORT_PATH);
  const summary = report.summary && typeof report.summary === "object" ? report.summary : {};
  const actionResults = Array.isArray(report.actionResults) ? report.actionResults : [];
  const actionFailures = actionResults.filter((row) => row?.ok !== true);
  const overflowFailures = actionResults.filter((row) => row?.hasHorizontalOverflow === true);
  const screenshotMissing = missingScreenshots(actionResults);
  const placeholderHeaders = placeholderHeaderRows(actionResults);
  const auditHeaders = auditHeaderRows(actionResults);
  const missingBusinessHeaders = missingRequiredBusinessHeaders(actionResults);
  const errors = [];

  if (Number(summary.totalScanned || 0) < MIN_ACTIONS) {
    errors.push(`visible action coverage too small: ${summary.totalScanned || 0} < ${MIN_ACTIONS}`);
  }
  if (actionFailures.length) errors.push(`action visual failures: ${actionFailures.length}`);
  if (overflowFailures.length) errors.push(`horizontal overflow failures: ${overflowFailures.length}`);
  if (Number(summary.consoleErrorCount || 0) !== 0 || countArray(report.consoleErrors) !== 0) {
    errors.push(`console errors: ${summary.consoleErrorCount || countArray(report.consoleErrors)}`);
  }
  if (screenshotMissing.length) errors.push(`missing screenshots: ${screenshotMissing.length}`);
  if (placeholderHeaders.length) errors.push(`placeholder headers visible: ${placeholderHeaders.length}`);
  if (auditHeaders.length) errors.push(`audit headers visible: ${auditHeaders.length}`);
  if (missingBusinessHeaders.length) errors.push(`required business headers missing: ${missingBusinessHeaders.length}`);

  const payload = {
    ok: errors.length === 0,
    reportPath: REPORT_PATH,
    minActions: MIN_ACTIONS,
    summary,
    failures: {
      errors,
      actionFailures: actionFailures.slice(0, 20),
      overflowFailures: overflowFailures.slice(0, 20),
      screenshotMissing,
      placeholderHeaders,
      auditHeaders,
      missingBusinessHeaders,
      consoleErrors: Array.isArray(report.consoleErrors) ? report.consoleErrors.slice(0, 20) : [],
    },
  };

  if (!payload.ok) fail("user visible surface visual coverage is not ok", payload);
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((err) => {
  console.error(JSON.stringify({
    ok: false,
    message: err instanceof Error ? err.message : String(err),
    details: err?.details || {},
  }, null, 2));
  process.exit(1);
});
