import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");
const ARTIFACT_ROOT = path.join(ROOT_DIR, "artifacts", "playwright", "business-form-user-perspective");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");
const MIN_CASE_COUNT = 20;

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

async function main() {
  const report = await readJson(REPORT_PATH);
  const results = Array.isArray(report.results) ? report.results : [];
  const failures = results.filter((row) => row?.ok !== true);
  const screenshotMissing = [];
  for (const row of results) {
    if (!await isFile(row?.screenshotPath)) screenshotMissing.push(row);
  }
  const leaked = results.filter((row) => Array.isArray(row?.leaked) && row.leaked.length > 0);
  const missing = results.filter((row) => Array.isArray(row?.missing) && row.missing.length > 0);
  const consoleErrors = Array.isArray(report.consoleErrors) ? report.consoleErrors : [];

  if (report.ok !== true) fail("business form user perspective report is not ok", { ok: report.ok });
  if (results.length < MIN_CASE_COUNT) fail("business form user perspective case count is too low", { actual: results.length, expected: MIN_CASE_COUNT });
  if (failures.length) fail("business form user perspective has failed cases", { failures });
  if (missing.length) fail("business form user perspective has missing user-facing sections", { missing });
  if (leaked.length) fail("business form user perspective leaked forbidden technical/source text", { leaked });
  if (screenshotMissing.length) fail("business form user perspective screenshot evidence missing", { screenshotMissing });
  if (consoleErrors.length) fail("business form user perspective has console errors", { consoleErrors });

  console.log(JSON.stringify({
    ok: true,
    reportPath: REPORT_PATH,
    caseCount: results.length,
    failures: failures.length,
    missing: missing.length,
    leaked: leaked.length,
    consoleErrors: consoleErrors.length,
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
