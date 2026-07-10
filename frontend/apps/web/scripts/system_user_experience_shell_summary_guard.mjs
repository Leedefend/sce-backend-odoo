import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "system-user-experience-shell");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");

const EXPECTED_CASE_KEYS = [
  "home",
  "my_work",
  "project_ledger_list",
  "release_operator_access_boundary",
  "mobile_home",
];

function fail(message, details = {}) {
  const error = new Error(message);
  error.details = details;
  throw error;
}

async function readJson(filePath) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (err) {
    fail(`cannot read JSON artifact: ${filePath}`, { error: err instanceof Error ? err.message : String(err) });
  }
}

async function isFile(filePath) {
  if (!filePath) return false;
  return fs.stat(filePath).then((stat) => stat.isFile()).catch(() => false);
}

function assertExactList(actual = [], expected = [], message) {
  const missing = expected.filter((item) => !actual.includes(item));
  const extra = actual.filter((item) => !expected.includes(item));
  const orderMismatch = expected
    .map((item, index) => ({ index, actual: actual[index], expected: item }))
    .filter((item) => item.actual !== item.expected);
  if (missing.length || extra.length || orderMismatch.length || actual.length !== expected.length) {
    fail(message, { missing, extra, orderMismatch, actual, expected });
  }
}

async function main() {
  const report = await readJson(REPORT_PATH);
  const results = Array.isArray(report.results) ? report.results : [];
  const caseKeys = results.map((row) => String(row?.key || ""));
  const failures = results.filter((row) => row?.ok !== true);
  const screenshotMissing = [];
  for (const row of results) {
    if (!await isFile(row?.screenshotPath)) screenshotMissing.push(row);
  }
  const layoutFailures = results.filter((row) => row?.layout?.hasHorizontalOverflow === true);
  const technicalLeaks = results.filter((row) => Array.isArray(row?.technicalTerms) && row.technicalTerms.length > 0);
  const consoleErrors = Array.isArray(report.consoleErrors) ? report.consoleErrors : [];
  const requestFailed = Array.isArray(report.requestFailed) ? report.requestFailed : [];

  if (report.ok !== true) fail("system user experience shell report is not ok", { ok: report.ok });
  assertExactList(caseKeys, EXPECTED_CASE_KEYS, "system user experience shell case keys drifted");
  if (failures.length) fail("system user experience shell has failed cases", { failures });
  if (screenshotMissing.length) fail("system user experience shell screenshot evidence missing", { screenshotMissing });
  if (layoutFailures.length) fail("system user experience shell has horizontal overflow", { layoutFailures });
  if (technicalLeaks.length) fail("system user experience shell leaked technical terms", { technicalLeaks });
  if (consoleErrors.length) fail("system user experience shell has console errors", { consoleErrors });
  if (requestFailed.length) fail("system user experience shell has failed requests", { requestFailed });

  console.log(JSON.stringify({
    ok: true,
    reportPath: REPORT_PATH,
    caseCount: results.length,
    failures: failures.length,
    consoleErrors: consoleErrors.length,
    requestFailed: requestFailed.length,
  }, null, 2));
}

main().catch((err) => {
  console.error(JSON.stringify({
    ok: false,
    message: err instanceof Error ? err.message : String(err),
    details: err?.details || {},
  }, null, 2));
  process.exit(1);
});
