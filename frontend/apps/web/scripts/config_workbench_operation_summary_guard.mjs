import fs from "node:fs/promises";
import path from "node:path";

const ARTIFACT_ROOT = path.resolve(process.cwd(), "artifacts/playwright/config-workbench-operation");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");
const SUMMARY_PATH = path.join(ARTIFACT_ROOT, "summary.json");

const EXPECTED_FILES = [
  "01-selected-from-scan.png",
  "02-switched-page.png",
  "03-direct-selected.png",
  "04-list-search-entry.png",
  "05-approval-entry.png",
  "06-form-designer-entry.png",
  "07-menu-config.png",
  "08-mobile-selected.png",
  "09-mobile-viewport.png",
  "report.json",
  "summary.json",
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

function ratio(passed, total) {
  return `${passed || 0}/${total || 0}`;
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) fail(message, { actual, expected });
}

async function main() {
  const [report, summary, files] = await Promise.all([
    readJson(REPORT_PATH),
    readJson(SUMMARY_PATH),
    fs.readdir(ARTIFACT_ROOT).catch((err) => fail("cannot read config workbench artifact directory", { error: err instanceof Error ? err.message : String(err) })),
  ]);

  const artifactFiles = files.filter((item) => item.endsWith(".png") || item.endsWith(".json")).sort();
  assertEqual(artifactFiles.join("|"), EXPECTED_FILES.join("|"), "config workbench artifacts must be exact and current");

  assertEqual(summary.ok, report.ok === true, "summary.ok must match report.ok");
  assertEqual(summary.reportPath, REPORT_PATH, "summary.reportPath must point to report.json");
  assertEqual(summary.summaryPath, SUMMARY_PATH, "summary.summaryPath must point to summary.json");
  assertEqual(summary.assertion, ratio(report.metrics?.assertion_passed_count, report.metrics?.assertion_count), "summary assertion ratio drifted");
  assertEqual(summary.journeys, ratio(report.metrics?.journey_passed_count, report.metrics?.journey_count), "summary journey ratio drifted");
  assertEqual(summary.actions, ratio(report.metrics?.action_passed_count, report.metrics?.action_count), "summary action ratio drifted");
  assertEqual(summary.screenshots, ratio(report.metrics?.screenshot_captured_count, report.metrics?.screenshot_required_count), "summary screenshot ratio drifted");
  assertEqual(summary.delivery, report.product_usability?.delivery_status || "unknown", "summary delivery status drifted");
  assertEqual(summary.professional, report.professional_readiness?.status || "unknown", "summary professional status drifted");
  assertEqual(summary.consoleErrors, report.metrics?.browser_console_error_count ?? 0, "summary console error count drifted");
  assertEqual(summary.requestFailed, report.metrics?.browser_request_failed_count ?? 0, "summary failed request count drifted");
  assertEqual(summary.currentPage, report.checks?.pageStructureDesktop?.currentConfig?.overviewLabel || "", "summary current page drifted");
  assertEqual(summary.formDesignerCurrentPageLabel, report.checks?.formDesignerCurrentPageLabel || "", "summary form designer page label drifted");
  assertEqual(summary.menuTreeHead, report.checks?.menuTreeHead || "", "summary menu tree head drifted");

  if (summary.ok !== true) fail("config workbench summary is not ok", { summary });
  if (summary.assertion !== "55/55") fail("config workbench assertion gate is not complete", { summary });
  if (summary.journeys !== "10/10" || summary.actions !== "18/18") fail("config workbench journey/action gate is not complete", { summary });
  if (summary.screenshots !== "9/9") fail("config workbench screenshot gate is not complete", { summary });
  if (summary.delivery !== "delivery_ready" || summary.professional !== "professional_ready") fail("config workbench readiness status is not complete", { summary });
  if (summary.consoleErrors !== 0 || summary.requestFailed !== 0) fail("config workbench browser health is not clean", { summary });
  if (summary.currentPage !== "项目合同汇总" || summary.formDesignerCurrentPageLabel !== "项目合同汇总") fail("config workbench page context summary is not aligned", { summary });

  console.log(JSON.stringify({
    ok: true,
    summaryPath: SUMMARY_PATH,
    assertion: summary.assertion,
    delivery: summary.delivery,
    professional: summary.professional,
    artifacts: artifactFiles.length,
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
