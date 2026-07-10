import fs from "node:fs/promises";
import path from "node:path";
import { CONFIG_WORKBENCH_OPERATION_COVERAGE as ACCEPTANCE_COVERAGE } from "./lib/config_workbench_operation_coverage.mjs";

const ARTIFACT_ROOT = path.resolve(process.cwd(), "artifacts/playwright/config-workbench-operation");
const REPORT_PATH = path.join(ARTIFACT_ROOT, "report.json");
const SUMMARY_PATH = path.join(ARTIFACT_ROOT, "summary.json");

const EXPECTED_FILES = [
  ...ACCEPTANCE_COVERAGE.screenshotKeys.map((key) => ACCEPTANCE_COVERAGE.screenshotFiles[key]),
  "report.json",
  "summary.json",
];

const REQUIRED_ASSERTIONS = [
  "product_workspace_structural_gap_unified",
  "product_page_region_outer_edges_aligned",
  "product_page_runtime_semantics_present",
  "business_runtime_workspace_structural_gap_unified",
  "menu_workspace_aligned_with_header",
  "mobile_no_horizontal_overflow",
  "no_console_errors",
  "no_request_failures",
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

function assertEmptyArray(actual, message) {
  if (!Array.isArray(actual) || actual.length !== 0) fail(message, { actual });
}

function assertReadyScore(section, message) {
  if (!section || typeof section !== "object") fail(`${message}: section is missing`, { section });
  if (!Number.isInteger(section.score_total) || !Number.isInteger(section.max_score)) {
    fail(`${message}: score fields are invalid`, { score_total: section.score_total, max_score: section.max_score });
  }
  if (section.score_total !== section.max_score) {
    fail(message, { score_total: section.score_total, max_score: section.max_score, score_required: section.score_required });
  }
}

function assertTaskResultsPass(actual = {}, expected = [], message) {
  assertExactList(Object.keys(actual || {}), expected, `${message}: task keys drifted`);
  const failed = Object.entries(actual || {})
    .filter(([, value]) => value?.status !== "pass")
    .map(([key, value]) => ({ key, status: value?.status, value }));
  if (failed.length) fail(message, { failed });
}

function assertDimensionScores(actual = {}, expected = [], expectedScore, message) {
  assertExactList(Object.keys(actual || {}), expected, `${message}: dimension keys drifted`);
  const failed = Object.entries(actual || {})
    .filter(([, value]) => value?.score !== expectedScore)
    .map(([key, value]) => ({ key, score: value?.score, expectedScore, value }));
  if (failed.length) fail(message, { failed });
}

function assertFullCoverage(summaryValue, passed, total, message) {
  if (!Number.isInteger(total) || total <= 0) fail(`${message}: total is invalid`, { summaryValue, passed, total });
  if (passed !== total || summaryValue !== `${total}/${total}`) {
    fail(message, { summaryValue, passed, total, expected: `${total}/${total}` });
  }
}

function assertMetricCount(actual, expected, message) {
  if (actual !== expected) fail(message, { actual, expected });
}

function assertIncludesAll(actual = [], required = [], message) {
  const missing = required.filter((item) => !actual.includes(item));
  if (missing.length) fail(message, { missing, required, actual });
}

function assertExactList(actual = [], expected = [], message) {
  const actualList = Array.isArray(actual) ? actual : [];
  const expectedList = Array.isArray(expected) ? expected : [];
  const missing = expectedList.filter((item) => !actualList.includes(item));
  const extra = actualList.filter((item) => !expectedList.includes(item));
  const orderMismatch = expectedList
    .map((item, index) => ({ index, actual: actualList[index], expected: item }))
    .filter((item) => item.actual !== item.expected);
  if (missing.length || extra.length || orderMismatch.length || actualList.length !== expectedList.length) {
    fail(message, { missing, extra, orderMismatch, actual: actualList, expected: expectedList });
  }
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
  assertEqual(report.metrics?.schema_version, "config_workbench_operation_acceptance_metrics.v1", "config workbench metrics schema drifted");
  assertEqual(report.metrics?.coverage_ratio, 1, "config workbench coverage ratio is not complete");
  assertEqual(report.metrics?.health_passed, true, "config workbench health flag is not true");
  assertExactList(
    Object.keys(ACCEPTANCE_COVERAGE.screenshotFiles || {}),
    ACCEPTANCE_COVERAGE.screenshotKeys,
    "config workbench screenshot coverage file map drifted",
  );
  assertMetricCount(report.metrics?.journey_count, ACCEPTANCE_COVERAGE.journeys.length, "config workbench journey count drifted");
  assertMetricCount(report.metrics?.action_count, ACCEPTANCE_COVERAGE.actions.length, "config workbench action count drifted");
  assertMetricCount(report.metrics?.assertion_count, ACCEPTANCE_COVERAGE.assertions.length, "config workbench assertion count drifted");
  assertMetricCount(report.metrics?.screenshot_required_count, ACCEPTANCE_COVERAGE.screenshotKeys.length, "config workbench screenshot count drifted");
  assertExactList(report.metrics?.journeys, ACCEPTANCE_COVERAGE.journeys, "config workbench journey coverage source drifted");
  assertExactList(report.metrics?.actions, ACCEPTANCE_COVERAGE.actions, "config workbench action coverage source drifted");
  assertExactList(report.metrics?.assertions, ACCEPTANCE_COVERAGE.assertions, "config workbench assertion coverage source drifted");
  assertIncludesAll(report.metrics?.assertions || [], REQUIRED_ASSERTIONS, "config workbench required assertion coverage drifted");
  assertFullCoverage(summary.assertion, report.metrics?.assertion_passed_count, report.metrics?.assertion_count, "config workbench assertion gate is not complete");
  assertFullCoverage(summary.journeys, report.metrics?.journey_passed_count, report.metrics?.journey_count, "config workbench journey gate is not complete");
  assertFullCoverage(summary.actions, report.metrics?.action_passed_count, report.metrics?.action_count, "config workbench action gate is not complete");
  assertFullCoverage(summary.screenshots, report.metrics?.screenshot_captured_count, report.metrics?.screenshot_required_count, "config workbench screenshot gate is not complete");
  if (summary.delivery !== "delivery_ready" || summary.professional !== "professional_ready") fail("config workbench readiness status is not complete", { summary });
  assertEqual(report.product_usability?.schema_version, "config_workbench_product_usability.v1", "config workbench product usability schema drifted");
  assertEqual(report.professional_readiness?.schema_version, "config_workbench_professional_readiness.v1", "config workbench professional readiness schema drifted");
  assertReadyScore(report.product_usability, "config workbench product usability score is not complete");
  assertReadyScore(report.professional_readiness, "config workbench professional readiness score is not complete");
  assertTaskResultsPass(
    report.product_usability?.task_results,
    ACCEPTANCE_COVERAGE.productUsabilityTasks,
    "config workbench product usability tasks are not all pass",
  );
  assertDimensionScores(
    report.product_usability?.dimensions,
    ACCEPTANCE_COVERAGE.productUsabilityDimensions,
    2,
    "config workbench product usability dimensions are not full score",
  );
  assertDimensionScores(
    report.professional_readiness?.dimensions,
    ACCEPTANCE_COVERAGE.professionalDimensions,
    3,
    "config workbench professional dimensions are not full score",
  );
  assertEmptyArray(report.product_usability?.blocking_issues, "config workbench product usability has blocking issues");
  assertEmptyArray(report.product_usability?.risk_items, "config workbench product usability has risk items");
  assertEmptyArray(report.professional_readiness?.blockers, "config workbench professional readiness has blockers");
  assertEqual(report.product_usability?.page_structure?.status, "pass", "config workbench product page structure is not pass");
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
