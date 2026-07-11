import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { launchChromium } from './playwright_runtime.mjs';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const baseUrl = process.env.FRONTEND_URL || process.env.BASE_URL || 'http://127.0.0.1:5174';
const dbName = process.env.DB_NAME || process.env.E2E_DB || 'sc_demo';
const loginName = process.env.E2E_LOGIN || process.env.LOGIN || 'wutao';
const password = process.env.E2E_PASSWORD || process.env.PASSWORD || '123456';
const artifactRoot = path.resolve(
  repoRoot,
  process.env.WIZARD_FOOTER_ACTION_ARTIFACT_ROOT || 'artifacts/playwright/wizard-footer-action-contract',
);
const reportPath = path.join(artifactRoot, 'report.json');

const cases = [
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_project_boq_import_wizard',
    actionId: Number(process.env.WIZARD_ACTION_PROJECT_BOQ_IMPORT || 516),
    method: 'action_import',
    label: '导入',
  },
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_project_quick_create_wizard',
    actionId: Number(process.env.WIZARD_ACTION_PROJECT_QUICK_CREATE || 558),
    method: 'action_quick_create',
    label: '创建并进入项目驾驶舱',
  },
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_project_task_from_boq_wizard',
    actionId: Number(process.env.WIZARD_ACTION_PROJECT_TASK_FROM_BOQ || 517),
    method: 'action_generate_tasks',
    label: '生成任务',
  },
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_ui_form_custom_field_wizard_business_config',
    actionId: Number(process.env.WIZARD_ACTION_UI_FORM_CUSTOM_FIELD || 840),
    menuId: Number(process.env.WIZARD_MENU_UI_FORM_CUSTOM_FIELD || 645),
    method: 'action_create_field_policy',
    label: '创建字段并配置显示',
  },
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_quota_import_wizard',
    actionId: Number(process.env.WIZARD_ACTION_QUOTA_IMPORT || 734),
    method: 'action_import',
    label: '导入',
  },
  {
    kind: 'action',
    xmlid: 'smart_construction_core.action_material_plan_to_rfq_wizard',
    actionId: Number(process.env.WIZARD_ACTION_MATERIAL_PLAN_TO_RFQ || 524),
    method: 'action_generate_rfq',
    label: '生成询价单',
  },
  {
    kind: 'model',
    model: 'sc.approval.scope.user.wizard',
    method: 'action_create_user',
    label: '创建并加入岗位',
  },
];

function assert(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function login(page) {
  await page.goto(`${baseUrl}/login?db=${encodeURIComponent(dbName)}`, { waitUntil: 'domcontentloaded' });
  await page.locator('input[placeholder*="账号"]').first().fill(loginName);
  await page.locator('input[placeholder*="密码"]').first().fill(password);
  await Promise.all([
    page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 }).catch(() => {}),
    page.locator('button:has-text("登录")').first().click(),
  ]);
  await page.waitForTimeout(800);
}

function buildParams(testCase) {
  const common = {
    client_type: 'web_pc',
    delivery_profile: 'full',
    render_profile: 'create',
    contract_surface: 'user',
    source_mode: 'governance_pipeline',
    context: { company_id: 1 },
    company_id: 1,
  };
  if (testCase.kind === 'model') {
    return {
      ...common,
      op: 'model',
      model: testCase.model,
      view_type: 'form',
    };
  }
  return {
    ...common,
    op: 'action_open',
    action_id: testCase.actionId,
    ...(testCase.menuId ? { menu_id: testCase.menuId } : {}),
  };
}

async function requestContract(page, token, testCase) {
  const params = buildParams(testCase);
  return page.evaluate(async ({ dbName, token, params }) => {
    const response = await fetch(`/api/v1/intent?db=${encodeURIComponent(dbName)}`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${token}`,
        'x-odoo-db': dbName,
        'x-tenant': 'default',
      },
      body: JSON.stringify({
        intent: 'ui.contract.v2',
        params,
        context: { company_id: 1 },
      }),
    });
    return {
      status: response.status,
      body: await response.json().catch(async () => ({ raw: await response.text() })),
    };
  }, { dbName, token, params });
}

await fs.mkdir(artifactRoot, { recursive: true });
const browser = await launchChromium({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

try {
  await login(page);
  const token = await page.evaluate(
    (db) => sessionStorage.getItem(`sc_auth_token:${db}`) || localStorage.getItem(`sc_auth_token:${db}`) || '',
    dbName,
  );
  assert(token, 'missing auth token after login');

  const results = [];
  for (const testCase of cases) {
    const response = await requestContract(page, token, testCase);
    const data = response.body?.data || {};
    const rules = Array.isArray(data.actionContract?.actionRuleList) ? data.actionContract.actionRuleList : [];
    const matches = rules
      .filter((rule) => rule?.button?.name === testCase.method)
      .map((rule) => ({
        key: rule.actionKey,
        label: rule.label,
        intent: rule.intent,
        sourceWidgetId: rule.sourceWidgetId,
        targetScope: rule.targetScope,
        button: rule.button,
      }));
    results.push({
      ...testCase,
      status: response.status,
      ok: response.body?.ok === true,
      pageInfo: data.pageInfo || null,
      ruleCount: rules.length,
      matches,
      passed: response.body?.ok === true && matches.some((match) => match.targetScope === 'footer'),
      error: response.body?.error || null,
    });
  }

  const failed = results.filter((row) => !row.passed);
  const report = {
    baseUrl,
    dbName,
    checked: results.length,
    failed: failed.length,
    results,
  };
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  assert(!failed.length, 'wizard footer action contract acceptance failed', { failed });
} finally {
  await browser.close();
}
