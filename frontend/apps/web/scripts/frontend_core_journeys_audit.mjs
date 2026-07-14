#!/usr/bin/env node

import fs from 'node:fs';

const reportPath = process.env.FRONTEND_ROLE_JOURNEY_REPORT
  || 'artifacts/playwright/frontend-productization-fixture/report.json';

function fail(message) {
  console.error(`[frontend_core_journeys_audit] FAIL ${message}`);
  process.exitCode = 2;
}

if (!fs.existsSync(reportPath)) {
  fail(`missing authoritative browser report: ${reportPath}`);
} else {
  const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  const requiredChecks = [
    'finance_login',
    'finance_navigation_preserved',
    'finance_company_a_isolation',
    'finance_company_b_switch_refresh',
    'finance_company_a_switch_back',
    'company_request_context_refresh',
    'project_member_role_label',
    'project_member_sensitive_nav_absent',
    'project_a_member_project_isolation',
    'project_member_action_denied',
    'project_member_menu_denied',
    'project_member_sensitive_record_denied',
    'project_member_out_of_scope_record_403',
    'denial_payload_non_leakage',
    'logout_login_role_cache_isolation',
    'pm_login_and_navigation',
    'owner_login_and_navigation',
  ];
  const checks = new Set(Array.isArray(report.checks) ? report.checks : []);
  const missing = requiredChecks.filter((check) => !checks.has(check));
  const j02 = report.journeys?.J02;
  const j03 = report.journeys?.J03;
  const errors = [
    ...(report.network_console?.finance_errors || []),
    ...(report.network_console?.member_errors_before_expected_denial || []),
  ];
  if (report.pass !== true) fail('browser report is not passing');
  else if (missing.length) fail(`missing checks: ${missing.join(', ')}`);
  else if (j02?.status !== 'PASS' || j02?.steps?.length !== 3) fail('J02 A-B-A evidence is incomplete');
  else if (j03?.status !== 'PASS' || j03?.steps?.length < 6) fail('J03 role isolation evidence is incomplete');
  else if (errors.length) fail(`unexpected browser errors: ${errors.join(' | ')}`);
  else if (report.network_console?.sensitive_payload_leakage !== false) fail('sensitive payload leakage was not disproved');
  else console.log(`[frontend_core_journeys_audit] PASS report=${reportPath} checks=${requiredChecks.length}`);
}
