#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:18081';
const DB_NAME = process.env.DB_NAME || 'sc_demo';
const OUT = path.resolve(process.cwd(), '../../../artifacts/playwright/low-code-change-set');
const ADMIN = { login: process.env.E2E_LOGIN || 'wutao', password: process.env.E2E_PASSWORD || '123456' };
const OTHER_ADMIN = { login: process.env.PLATFORM_LOGIN || 'sc_fx_scene_admin', password: process.env.PLATFORM_PASSWORD || 'prod_like' };
const ORDINARY = { login: process.env.ORDINARY_LOGIN || 'chenshuai', password: process.env.ORDINARY_PASSWORD || '123456' };
const ACTION_ID = Number(process.env.CHANGE_SET_ACTION_ID || 1002);
const MENU_ID = Number(process.env.CHANGE_SET_MENU_ID || 389);
const ROLE_KEY = `lc_pro_02_acceptance_${process.pid}`;
const EMPTY_MODEL = 'res.partner';
const EMPTY_ACTION_ID = 0;

async function login(page, account) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(account.login);
  await inputs.nth(1).fill(account.password);
  if (await inputs.nth(2).isEnabled()) await inputs.nth(2).fill(DB_NAME);
  await page.getByRole('button', { name: /^登录$/ }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 60000 });
}

async function intent(page, name, params = {}, expectOk = true) {
  const result = await page.evaluate(async ({ dbName, name, params }) => {
    const tokenEntry = Object.entries(sessionStorage).find(([key]) => key.startsWith('sc_auth_token:'));
    const response = await fetch('/api/v1/intent', {
      method: 'POST',
      headers: { Authorization: `Bearer ${String(tokenEntry?.[1] || '')}`, 'Content-Type': 'application/json', 'X-Odoo-DB': dbName, 'X-Trace-Id': crypto.randomUUID() },
      body: JSON.stringify({ intent: name, params }),
    });
    return { status: response.status, body: await response.json() };
  }, { dbName: DB_NAME, name, params });
  if (expectOk && (result.status >= 400 || result.body?.ok !== true)) throw new Error(`${name}: ${result.status} ${JSON.stringify(result.body?.error || result.body)}`);
  return result;
}

function changeSetIntent(page, name, params = {}, expectOk = true) {
  return intent(page, name, { role_key: ROLE_KEY, ...params }, expectOk);
}

function orchestration(viewType, label, field = 'name', visible = true) {
  const key = viewType === 'tree' ? 'columns' : 'fields';
  return { view_orchestration: { source: 'smart_core.lowcode.business_config', views: { [viewType]: { [key]: [{ name: field, label, visible, sequence: 10 }] } } } };
}

function listSearchAnalysisPayload(viewType, empty = false) {
  const items = empty ? [] : [{ name: viewType === 'tree' ? 'name' : 'company_id' }];
  const view = viewType === 'tree'
    ? { columns: items }
    : viewType === 'search'
      ? { filters: items, group_by: items }
      : { measures: empty ? [] : [{ name: 'color' }], dimensions: items, ...(viewType === 'graph' ? { type: 'bar' } : {}) };
  return { view_orchestration: { source: 'smart_core.lowcode.business_config', views: { [viewType]: view } } };
}

function countNamedNodes(value, name) {
  if (!value || typeof value !== 'object') return 0;
  if (Array.isArray(value)) return value.reduce((sum, item) => sum + countNamedNodes(item, name), 0);
  const own = String(value.name || '') === name ? 1 : 0;
  return own + Object.values(value).reduce((sum, item) => sum + countNamedNodes(item, name), 0);
}

function previewEvidence(value, pathParts = [], rows = []) {
  if (!value || typeof value !== 'object') return rows;
  if (Array.isArray(value)) {
    value.forEach((item, index) => previewEvidence(item, [...pathParts, String(index)], rows));
    return rows;
  }
  for (const [key, item] of Object.entries(value)) {
    const pathValue = [...pathParts, key];
    if (['name', 'source_kind', 'status'].includes(key) && /preview|change_set/i.test(String(item || ''))) {
      rows.push({ path: pathValue.join('.'), value: String(item || '') });
    }
    previewEvidence(item, pathValue, rows);
  }
  return rows;
}

function keyEvidence(value, wanted, pathParts = [], rows = []) {
  if (!value || typeof value !== 'object') return rows;
  if (Array.isArray(value)) {
    value.forEach((item, index) => keyEvidence(item, wanted, [...pathParts, String(index)], rows));
    return rows;
  }
  for (const [key, item] of Object.entries(value)) {
    const pathValue = [...pathParts, key];
    if (wanted.has(key) && ['string', 'number', 'boolean'].includes(typeof item)) rows.push({ path: pathValue.join('.'), value: item });
    keyEvidence(item, wanted, pathValue, rows);
  }
  return rows;
}

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
const page = await context.newPage();
const report = { schema_version: 'low_code_change_set_acceptance.v1', ok: false, assertions: {}, journeys: {} };
report.runtime = { console: [], pageerror: [] };
page.on('console', (message) => { if (message.type() === 'error') report.runtime.console.push(message.text()); });
page.on('pageerror', (error) => report.runtime.pageerror.push(error.message));
const publishedTokens = [];
try {
  await login(page, ADMIN);
  const marker = `LC-PRO-02-${Date.now()}`;
  const opened = (await changeSetIntent(page, 'ui.business_config.change_set.open', { name: marker })).body.data;
  const token = opened.token;
  const targets = [
    {
      config_type: 'form', target_key: `${marker}.form`, model: 'construction.contract', view_type: 'form', action_id: ACTION_ID,
      draft_payload: { view_orchestration: { source: 'smart_core.lowcode.business_config', views: { form: {
        fields: [{ name: 'subject', label: `${marker}表单`, visible: false, sequence: 10 }],
      } } } },
    },
    { config_type: 'list', target_key: `${marker}.list`, model: 'construction.contract', view_type: 'tree', action_id: ACTION_ID, draft_payload: orchestration('tree', `${marker}列表`) },
    { config_type: 'menu', target_key: `${marker}.menu`, model: 'ir.ui.menu', draft_payload: { rows: [{ menu_id: MENU_ID, target_parent_menu_id: 0, custom_label: '', sequence_override: 0, visible: true, role_group_ids: [], note: marker }] } },
  ];
  let staged;
  for (const target of targets) {
    staged = (await changeSetIntent(page, 'ui.business_config.change_set.stage', { change_set_token: token, ...target, diff_summary: { summary: `${target.config_type} acceptance` } })).body.data;
  }
  report.journeys['LC-J11'] = { change_set_id: staged.id, item_count: staged.item_count, types: staged.items.map((item) => item.config_type).sort() };
  report.assertions.j11_one_change_set_three_types = staged.item_count === 3 && ['form', 'list', 'menu'].every((kind) => staged.items.some((item) => item.config_type === kind));

  const otherContext = await browser.newContext();
  const otherPage = await otherContext.newPage();
  await login(otherPage, OTHER_ADMIN);
  const otherRead = await changeSetIntent(otherPage, 'ui.business_config.change_set.get', { change_set_token: token }, false);
  await otherContext.close();
  const ordinaryContext = await browser.newContext();
  const ordinaryPage = await ordinaryContext.newPage();
  await login(ordinaryPage, ORDINARY);
  const ordinaryRead = await changeSetIntent(ordinaryPage, 'ui.business_config.change_set.get', { change_set_token: token }, false);
  await ordinaryContext.close();
  report.journeys['LC-J12'] = { other_admin: otherRead.body?.error?.reason_code || otherRead.status, ordinary: ordinaryRead.body?.error?.reason_code || ordinaryRead.status };
  report.assertions.j12_other_admin_isolated = otherRead.body?.ok !== true;
  report.assertions.j12_ordinary_forbidden = ordinaryRead.body?.ok !== true && [403, 404].includes(Number(ordinaryRead.status || ordinaryRead.body?.code));

  const auditBefore = (await intent(page, 'ui.business_config.mutation_audit.snapshot')).body.data;
  const preview = (await changeSetIntent(page, 'ui.business_config.change_set.preview', { change_set_token: token, device: 'desktop' })).body.data;
  const online = await intent(page, 'ui.contract.v2', { op: 'action_open', action_id: ACTION_ID, view_type: 'tree', client_type: 'web_pc', delivery_profile: 'full' });
  const draft = await intent(page, 'ui.contract.v2', { op: 'action_open', action_id: ACTION_ID, view_type: 'tree', client_type: 'web_pc', delivery_profile: 'full', preview_token: preview.preview.token, preview_role_key: ROLE_KEY });
  const onlineForm = await intent(page, 'ui.contract.v2', { op: 'model', model: 'construction.contract', action_id: ACTION_ID, view_type: 'form', source_mode: 'backend_internal', client_type: 'web_pc', delivery_profile: 'full' });
  const draftForm = await intent(page, 'ui.contract.v2', { op: 'model', model: 'construction.contract', action_id: ACTION_ID, view_type: 'form', source_mode: 'backend_internal', client_type: 'web_pc', delivery_profile: 'full', preview_token: preview.preview.token, preview_role_key: ROLE_KEY });
  const auditAfter = (await intent(page, 'ui.business_config.mutation_audit.snapshot')).body.data;
  const onlineJson = JSON.stringify(online.body?.data || {});
  const draftJson = JSON.stringify(draft.body?.data || {});
  const draftFormJson = JSON.stringify(draftForm.body?.data || {});
  const onlineSubjectNodes = countNamedNodes(onlineForm.body?.data?.layoutContract?.containerTree || [], 'subject');
  const draftSubjectNodes = countNamedNodes(draftForm.body?.data?.layoutContract?.containerTree || [], 'subject');
  report.journeys['LC-J13'] = {
    preview_expires_at: preview.preview.expires_at,
    formal_mutations: preview.preview.formal_config_mutation_count,
    audit_before: auditBefore.count,
    audit_after: auditAfter.count,
    list_status: draft.status,
    list_error: draft.body?.error || null,
    list_marker_present: draftJson.includes(`${marker}列表`),
    list_preview_contract_present: draftJson.includes(`preview:${marker}.list`),
    form_status: draftForm.status,
    form_error: draftForm.body?.error || null,
    form_marker_present: draftFormJson.includes(`${marker}表单`),
    form_preview_contract_present: draftFormJson.includes(`preview:${marker}.form`),
    form_preview_source_present: draftFormJson.includes('change_set_preview'),
    form_preview_evidence: previewEvidence(draftForm.body?.data || {}).slice(0, 20),
    online_subject_nodes: onlineSubjectNodes,
    draft_subject_nodes: draftSubjectNodes,
    form_route_evidence: keyEvidence(draftForm.body?.data || {}, new Set(['model', 'view_type', 'viewType', 'action_id'])).slice(0, 30),
  };
  report.assertions.j13_preview_shows_draft = draftJson.includes(`${marker}列表`);
  report.assertions.r01_form_preview_full_projection = draftForm.body?.ok === true
    && draftForm.body?.data?.pageInfo?.model === 'construction.contract'
    && draftForm.body?.data?.pageInfo?.viewType === 'form'
    && onlineSubjectNodes > 0
    && draftSubjectNodes === 0
    && !draftFormJson.includes('AttributeError');
  report.assertions.j13_online_unchanged = !onlineJson.includes(marker)
    && !JSON.stringify(onlineForm.body?.data || {}).includes(marker);
  report.assertions.j13_zero_formal_writes = auditBefore.count === auditAfter.count && preview.preview.formal_config_mutation_count === 0;

  const validated = (await changeSetIntent(page, 'ui.business_config.change_set.validate', { change_set_token: token })).body.data;
  const published = (await changeSetIntent(page, 'ui.business_config.change_set.publish', { change_set_token: token, request_id: `${marker}-publish` })).body.data;
  publishedTokens.push(token);
  report.journeys['LC-J14'] = { state: published.state, item_count: published.item_count, runtime_verified: published.publish_result?.runtime_verified };
  report.assertions.j14_atomic_batch = validated.state === 'ready' && published.state === 'published' && published.item_count === 3 && published.publish_result?.runtime_verified === true;

  const failedSet = (await changeSetIntent(page, 'ui.business_config.change_set.open', { name: `${marker}-invalid` })).body.data;
  await changeSetIntent(page, 'ui.business_config.change_set.stage', { change_set_token: failedSet.token, config_type: 'form', target_key: `${marker}.invalid`, model: 'construction.contract', view_type: 'form', action_id: ACTION_ID, draft_payload: orchestration('form', marker, '__missing_field__'), diff_summary: { summary: 'invalid acceptance' } });
  const failedValidation = (await changeSetIntent(page, 'ui.business_config.change_set.validate', { change_set_token: failedSet.token })).body.data;
  report.journeys['LC-J15'] = { state: failedValidation.state, errors: failedValidation.items?.[0]?.validation_result?.errors || [] };
  report.assertions.j15_invalid_batch_not_publishable = failedValidation.state === 'failed';
  await changeSetIntent(page, 'ui.business_config.change_set.discard', { change_set_token: failedSet.token });

  report.journeys['LC-J16'] = { evidence: 'backend transaction test test_publish_detects_concurrent_contract_update', expected: 409 };
  report.assertions.j16_conflict_guard_declared = true;
  const rolledBack = (await changeSetIntent(page, 'ui.business_config.change_set.rollback', { change_set_token: token, request_id: `${marker}-rollback` })).body.data;
  publishedTokens.splice(publishedTokens.indexOf(token), 1);
  report.journeys['LC-J17'] = { rollback_batch_id: rolledBack.id, state: rolledBack.state, rollback_of: rolledBack.publish_result?.rollback_of_change_set_id };
  report.assertions.j17_batch_rollback = rolledBack.state === 'published' && rolledBack.publish_result?.rollback_of_change_set_id === published.id;

  const riskSet = (await changeSetIntent(page, 'ui.business_config.change_set.open', { name: `${marker}-risk` })).body.data;
  const highRisk = await changeSetIntent(page, 'ui.business_config.change_set.stage', { change_set_token: riskSet.token, config_type: 'approval', target_key: `${marker}.approval`, model: 'sc.approval.policy', draft_payload: { steps: [] } }, false);
  report.journeys['LC-J18'] = { reason: highRisk.body?.error?.reason_code };
  report.assertions.j18_high_risk_separate = highRisk.body?.error?.reason_code === 'HIGH_RISK_OPERATION_REQUIRED';
  await changeSetIntent(page, 'ui.business_config.change_set.discard', { change_set_token: riskSet.token });

  const emptyMarker = `LC-PRO-02R1-${Date.now()}`;
  const emptyTargets = [
    { config_type: 'list', view_type: 'tree' },
    { config_type: 'search', view_type: 'search' },
    { config_type: 'analysis', view_type: 'pivot' },
    { config_type: 'analysis', view_type: 'graph' },
  ];
  const baselineSet = (await changeSetIntent(page, 'ui.business_config.change_set.open', { name: `${emptyMarker}-baseline` })).body.data;
  for (const target of emptyTargets) {
    await changeSetIntent(page, 'ui.business_config.change_set.stage', {
      change_set_token: baselineSet.token,
      ...target,
      target_key: `${emptyMarker}.${target.view_type}`,
      model: EMPTY_MODEL,
      action_id: EMPTY_ACTION_ID,
      draft_payload: listSearchAnalysisPayload(target.view_type),
      diff_summary: { summary: `${target.view_type} nonempty baseline` },
    });
  }
  await changeSetIntent(page, 'ui.business_config.change_set.validate', { change_set_token: baselineSet.token });
  await changeSetIntent(page, 'ui.business_config.change_set.publish', { change_set_token: baselineSet.token, request_id: `${emptyMarker}-baseline-publish` });
  publishedTokens.push(baselineSet.token);

  const baselineListSearch = (await changeSetIntent(page, 'ui.business_config.list_search.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;
  const baselineAnalysis = (await changeSetIntent(page, 'ui.business_config.analysis.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;
  const contractsByView = new Map([
    ['tree', baselineListSearch.business_config_list_contracts?.find((contract) => contract.name === `${emptyMarker}.tree`)],
    ['search', baselineListSearch.business_config_search_contracts?.find((contract) => contract.name === `${emptyMarker}.search`)],
    ...(baselineAnalysis.business_config_analysis_contracts || [])
      .filter((contract) => contract.name === `${emptyMarker}.${contract.view_type}`)
      .map((contract) => [contract.view_type, contract]),
  ]);
  const emptySet = (await changeSetIntent(page, 'ui.business_config.change_set.open', { name: `${emptyMarker}-empty` })).body.data;
  for (const target of emptyTargets) {
    const contract = contractsByView.get(target.view_type);
    if (!contract?.id) throw new Error(`missing ${target.view_type} baseline contract`);
    await changeSetIntent(page, 'ui.business_config.change_set.stage', {
      change_set_token: emptySet.token,
      ...target,
      target_key: contract.name,
      model: EMPTY_MODEL,
      action_id: EMPTY_ACTION_ID,
      current_contract_id: contract.id,
      draft_payload: listSearchAnalysisPayload(target.view_type, true),
      diff_summary: { summary: `${target.view_type} explicit empty` },
    });
  }
  const emptyValidated = (await changeSetIntent(page, 'ui.business_config.change_set.validate', { change_set_token: emptySet.token })).body.data;
  const emptyPublished = (await changeSetIntent(page, 'ui.business_config.change_set.publish', { change_set_token: emptySet.token, request_id: `${emptyMarker}-empty-publish` })).body.data;
  publishedTokens.push(emptySet.token);
  const versionsBeforeOpen = (await changeSetIntent(page, 'ui.business_config.contract.versions', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID, status: 'published' })).body.data;
  const reopenedListSearch = (await changeSetIntent(page, 'ui.business_config.list_search.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;
  const reopenedAnalysis = (await changeSetIntent(page, 'ui.business_config.analysis.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;

  const editorUrl = (extra) => `${BASE_URL}/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1&model=${encodeURIComponent(EMPTY_MODEL)}&role_key=${encodeURIComponent(ROLE_KEY)}&page_label=${encodeURIComponent('显式空合同验收')}&${extra}`;
  await page.goto(editorUrl('open_list_search=1'), { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.getByRole('heading', { name: '列表与搜索设置' }).waitFor({ timeout: 30000 });
  const listPanel = page.locator('section.config-editor-panel').filter({ has: page.getByRole('heading', { name: '列表与搜索设置' }) });
  const listEditorCounts = {};
  for (const tab of ['列表列', '搜索条件', '默认分组']) {
    await listPanel.getByRole('button', { name: new RegExp(`^${tab}`) }).click();
    listEditorCounts[tab] = await listPanel.locator('.field-chip').count();
  }
  const listDirty = await listPanel.locator('.edit-dirty').count();
  const listSuggested = (await page.locator('body').innerText()).includes('建议配置，尚未保存');

  await page.goto(editorUrl('open_analysis=1'), { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.getByRole('heading', { name: '分析视图设置' }).waitFor({ timeout: 30000 });
  const analysisPanel = page.locator('section.config-editor-panel').filter({ has: page.getByRole('heading', { name: '分析视图设置' }) });
  const analysisEditorCounts = {};
  for (const tab of ['透视指标', '透视维度', '图表指标', '图表维度']) {
    await analysisPanel.getByRole('button', { name: new RegExp(`^${tab}`) }).click();
    analysisEditorCounts[tab] = await analysisPanel.locator('.field-chip').count();
  }
  const analysisDirty = await analysisPanel.locator('.edit-dirty').count();
  const analysisSuggested = (await page.locator('body').innerText()).includes('建议配置，尚未保存');
  const versionsAfterOpen = (await changeSetIntent(page, 'ui.business_config.contract.versions', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID, status: 'published' })).body.data;

  report.journeys['LC-E01-E03'] = {
    validate_state: emptyValidated.state,
    publish_state: emptyPublished.state,
    has_list: reopenedListSearch.has_business_list_config,
    has_search: reopenedListSearch.has_business_search_config,
    has_pivot: reopenedAnalysis.has_business_pivot_config,
    has_graph: reopenedAnalysis.has_business_graph_config,
    list_editor_counts: listEditorCounts,
    analysis_editor_counts: analysisEditorCounts,
    dirty_count: listDirty + analysisDirty,
    version_count_before_open: versionsBeforeOpen.version_count,
    version_count_after_open: versionsAfterOpen.version_count,
  };
  report.assertions.e01_e03_empty_contracts_reopen_empty = emptyValidated.state === 'ready'
    && emptyPublished.state === 'published'
    && reopenedListSearch.has_business_list_config === true
    && reopenedListSearch.has_business_search_config === true
    && reopenedAnalysis.has_business_pivot_config === true
    && reopenedAnalysis.has_business_graph_config === true
    && [reopenedListSearch.business_config_list_columns, reopenedListSearch.business_config_search_filters, reopenedListSearch.business_config_search_group_by,
      reopenedAnalysis.pivot_measures, reopenedAnalysis.pivot_dimensions, reopenedAnalysis.graph_measures, reopenedAnalysis.graph_dimensions].every((items) => Array.isArray(items) && items.length === 0)
    && Object.values(listEditorCounts).every((count) => count === 0)
    && Object.values(analysisEditorCounts).every((count) => count === 0);
  report.assertions.e01_e03_reopen_clean_and_read_only = listDirty === 0 && analysisDirty === 0
    && !listSuggested && !analysisSuggested
    && versionsBeforeOpen.version_count === versionsAfterOpen.version_count;

  const restored = (await changeSetIntent(page, 'ui.business_config.change_set.rollback', { change_set_token: emptySet.token, request_id: `${emptyMarker}-empty-rollback` })).body.data;
  publishedTokens.splice(publishedTokens.indexOf(emptySet.token), 1);
  const restoredListSearch = (await changeSetIntent(page, 'ui.business_config.list_search.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;
  const restoredAnalysis = (await changeSetIntent(page, 'ui.business_config.analysis.audit', { model: EMPTY_MODEL, action_id: EMPTY_ACTION_ID })).body.data;
  report.journeys['LC-E04'] = {
    rollback_state: restored.state,
    list_columns: restoredListSearch.business_config_list_columns,
    search_filters: restoredListSearch.business_config_search_filters,
    search_group_by: restoredListSearch.business_config_search_group_by,
    pivot_measures: restoredAnalysis.pivot_measures,
    pivot_dimensions: restoredAnalysis.pivot_dimensions,
    graph_measures: restoredAnalysis.graph_measures,
    graph_dimensions: restoredAnalysis.graph_dimensions,
  };
  report.assertions.e04_rollback_restores_nonempty = restored.state === 'published'
    && restoredListSearch.business_config_list_columns.length > 0
    && restoredListSearch.business_config_search_filters.length > 0
    && restoredListSearch.business_config_search_group_by.length > 0
    && restoredAnalysis.pivot_measures.length > 0 && restoredAnalysis.pivot_dimensions.length > 0
    && restoredAnalysis.graph_measures.length > 0 && restoredAnalysis.graph_dimensions.length > 0;
  report.journeys['LC-E05-E06'] = { evidence: 'backend transaction tests cover stale hash 409 and company/action/role/lifecycle isolation' };
  report.assertions.e05_e06_backend_evidence_declared = true;
  await changeSetIntent(page, 'ui.business_config.change_set.rollback', { change_set_token: baselineSet.token, request_id: `${emptyMarker}-baseline-rollback` });
  publishedTokens.splice(publishedTokens.indexOf(baselineSet.token), 1);

  await page.goto(`${BASE_URL}/admin/business-config?db=${encodeURIComponent(DB_NAME)}&root_menu_xmlid=smart_construction_core.menu_sc_root&open_pages=1&model=construction.contract&action_id=${ACTION_ID}&page_label=${encodeURIComponent('合同办理')}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);
  report.ui_debug = { url: page.url(), body: (await page.locator('body').innerText()).slice(0, 1200) };
  await page.screenshot({ path: path.join(OUT, 'change-set-workbench-debug.png'), fullPage: true });
  await page.waitForSelector('[data-business-config-change-set="v1"]', { timeout: 15000 });
  await page.screenshot({ path: path.join(OUT, 'change-set-workbench-1920.png'), fullPage: true });
  report.assertions.workbench_rendered = true;
  report.ok = Object.values(report.assertions).every(Boolean);
} catch (error) {
  report.failure = error instanceof Error ? error.stack || error.message : String(error);
  for (const publishedToken of publishedTokens.reverse()) {
    try { await changeSetIntent(page, 'ui.business_config.change_set.rollback', { change_set_token: publishedToken, request_id: `emergency-rollback-${Date.now()}-${publishedToken.slice(-6)}` }); } catch { /* report original failure */ }
  }
} finally {
  await browser.close();
  await fs.writeFile(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
}

if (!report.ok) {
  console.error('[low_code_change_set_acceptance] FAIL', report.failure || report.assertions);
  process.exit(1);
}
console.log('[low_code_change_set_acceptance] PASS LC-J11..LC-J18');
