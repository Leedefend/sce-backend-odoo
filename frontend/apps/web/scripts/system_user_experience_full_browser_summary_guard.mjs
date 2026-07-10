import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..", "..", "..");

const CONFIG_SUMMARY_PATH = path.join(ROOT_DIR, "artifacts", "playwright", "config-workbench-operation", "summary.json");
const CONFIG_REPORT_PATH = path.join(ROOT_DIR, "artifacts", "playwright", "config-workbench-operation", "report.json");
const SHELL_REPORT_PATH = path.join(ROOT_DIR, "artifacts", "playwright", "system-user-experience-shell", "report.json");
const BUSINESS_FORM_REPORT_PATH = path.join(ROOT_DIR, "artifacts", "playwright", "business-form-user-perspective", "report.json");
const OUTPUT_PATH = path.join(ROOT_DIR, "artifacts", "playwright", "system-user-experience-full-browser", "summary.json");

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

function countArray(value) {
  return Array.isArray(value) ? value.length : 0;
}

async function main() {
  const [configSummary, configReport, shellReport, businessFormReport] = await Promise.all([
    readJson(CONFIG_SUMMARY_PATH),
    readJson(CONFIG_REPORT_PATH),
    readJson(SHELL_REPORT_PATH),
    readJson(BUSINESS_FORM_REPORT_PATH),
  ]);

  const configOk = configSummary.ok === true
    && configSummary.assertion === "64/64"
    && configSummary.journeys === "10/10"
    && configSummary.actions === "19/19"
    && configSummary.screenshots === "9/9"
    && configSummary.delivery === "delivery_ready"
    && configSummary.professional === "professional_ready"
    && configSummary.consoleErrors === 0
    && configSummary.requestFailed === 0
    && configReport.ok === true;
  const shellFailures = countArray(shellReport.failures);
  const shellOk = shellReport.ok === true
    && shellReport.caseCount >= 5
    && shellFailures === 0
    && countArray(shellReport.consoleErrors) === 0
    && countArray(shellReport.requestFailed) === 0;
  const businessFormResults = Array.isArray(businessFormReport.results) ? businessFormReport.results : [];
  const businessFormFailures = businessFormResults.filter((row) => row?.ok !== true);
  const businessFormOk = businessFormReport.ok === true
    && businessFormResults.length >= 20
    && businessFormFailures.length === 0
    && countArray(businessFormReport.errors) === 0
    && countArray(businessFormReport.consoleErrors) === 0;

  const payload = {
    ok: configOk && shellOk && businessFormOk,
    reportPath: OUTPUT_PATH,
    gates: {
      config_workbench: {
        ok: configOk,
        assertions: configSummary.assertion,
        journeys: configSummary.journeys,
        actions: configSummary.actions,
        screenshots: configSummary.screenshots,
        delivery: configSummary.delivery,
        professional: configSummary.professional,
        consoleErrors: configSummary.consoleErrors,
        requestFailed: configSummary.requestFailed,
      },
      shell: {
        ok: shellOk,
        caseCount: shellReport.caseCount,
        failures: shellFailures,
        consoleErrors: countArray(shellReport.consoleErrors),
        requestFailed: countArray(shellReport.requestFailed),
      },
      business_form_user_perspective: {
        ok: businessFormOk,
        caseCount: businessFormResults.length,
        failures: businessFormFailures.length,
        errors: countArray(businessFormReport.errors),
        consoleErrors: countArray(businessFormReport.consoleErrors),
      },
    },
  };

  await fs.mkdir(path.dirname(OUTPUT_PATH), { recursive: true });
  await fs.writeFile(OUTPUT_PATH, `${JSON.stringify(payload, null, 2)}\n`, "utf8");

  if (!payload.ok) fail("system user experience full browser summary is not ok", payload.gates);
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
