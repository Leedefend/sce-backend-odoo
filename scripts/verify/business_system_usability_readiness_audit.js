#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const OPERABILITY_PATH = 'artifacts/function-usability-proof/current/all_menu_business_operability_matrix_current.json';
const CRUD_FLOW_PATH = 'artifacts/function-usability-proof/current/all_menu_business_crud_flow_probe_current.json';
const P1_BROWSER_COVERAGE_PATH = 'artifacts/function-usability-proof/current/business_handling_browser_p1_coverage_audit.json';
const CARRYING_PATH = 'artifacts/function-usability-proof/current/formal_business_data_carrying_matrix_current.json';
const OUTPUT_PATH = 'artifacts/function-usability-proof/current/business_system_usability_readiness_audit.json';
const EXCLUDED_HISTORICAL_SOURCES = new Set([]);

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function keyOf(row) {
  return `${row.model}|${Number(row.action_id)}|${Number(row.menu_id)}`;
}

function acceptableRead(row) {
  const status = row.read && row.read.status;
  return status === 'pass' || status === 'empty_ok_if_createable';
}

function acceptableCreate(row) {
  if (row.mode === 'readonly') return row.create && row.create.status === 'not_applicable_readonly';
  return row.create && row.create.status === 'pass';
}

function acceptableEdit(row) {
  const status = row.edit && row.edit.status;
  if (row.mode === 'readonly') return status === 'not_applicable_no_write_right';
  if (!row.record_count) return status === 'not_applicable_empty';
  return status === 'pass';
}

function main() {
  const operability = readJson(OPERABILITY_PATH);
  const crudFlow = readJson(CRUD_FLOW_PATH);
  const p1Coverage = readJson(P1_BROWSER_COVERAGE_PATH);
  const carrying = readJson(CARRYING_PATH);

  const p1Evidence = new Map();
  for (const row of p1Coverage.rows || []) {
    if (row.covered) p1Evidence.set(keyOf(row), row);
  }

  const menuRows = operability.rows || [];
  const menuContractGaps = menuRows
    .filter((row) => !(acceptableRead(row) && acceptableCreate(row) && acceptableEdit(row)))
    .map((row) => ({
      path: row.path,
      model: row.model,
      action_id: row.action_id,
      menu_id: row.menu_id,
      mode: row.mode,
      record_count: row.record_count,
      read: row.read && row.read.status,
      create: row.create && row.create.status,
      edit: row.edit && row.edit.status,
    }));

  const businessWriteRows = menuRows.filter((row) => row.mode === 'business_write');
  const browserCrudCoveredRows = businessWriteRows.filter((row) => p1Evidence.has(keyOf(row)));
  const browserCrudMissingRows = businessWriteRows
    .filter((row) => !p1Evidence.has(keyOf(row)))
    .map((row) => ({
      path: row.path,
      model: row.model,
      action_id: row.action_id,
      menu_id: row.menu_id,
      record_count: row.record_count,
      reason: 'no_real_browser_create_edit_view_evidence_for_this_menu',
    }));

  const historyBlockingRows = (carrying.gap_rows || [])
    .filter((row) => !EXCLUDED_HISTORICAL_SOURCES.has(row.legacy_source_model));
  const historyTargetMenuGaps = []
    .concat(carrying.target_without_menu || [])
    .concat(carrying.target_without_target_tree_menu || []);

  const result = {
    ok: false,
    decision: 'not_ready_for_full_business_use',
    inputs: {
      operability: OPERABILITY_PATH,
      crud_flow: CRUD_FLOW_PATH,
      p1_browser_coverage: P1_BROWSER_COVERAGE_PATH,
      carrying: CARRYING_PATH,
    },
    criteria: {
      all_menus_contract_view_create_edit_closed: menuContractGaps.length === 0 && operability.ok === true,
      all_menus_actual_create_edit_view_flow_closed: crudFlow.ok === true && crudFlow.failure_count === 0,
      p1_business_paths_have_real_browser_evidence: p1Coverage.ok === true && p1Coverage.missing_count === 0,
      historical_business_data_fully_carried: historyBlockingRows.length === 0 && historyTargetMenuGaps.length === 0,
    },
    counts: {
      target_menu_count: menuRows.length,
      readonly_menu_count: menuRows.filter((row) => row.mode === 'readonly').length,
      business_write_menu_count: businessWriteRows.length,
      menu_contract_gap_count: menuContractGaps.length,
      actual_crud_checked_count: crudFlow.checked || 0,
      actual_crud_pass_count: crudFlow.pass_count || 0,
      actual_crud_not_applicable_count: crudFlow.not_applicable_count || 0,
      actual_crud_failure_count: crudFlow.failure_count || 0,
      browser_crud_covered_count: browserCrudCoveredRows.length,
      browser_crud_missing_count: browserCrudMissingRows.length,
      historical_carrying_gap_count: historyBlockingRows.length,
      historical_carrying_excluded_count: (carrying.gap_rows || []).length - historyBlockingRows.length,
      historical_target_menu_gap_count: historyTargetMenuGaps.length,
    },
    menu_contract_gaps: menuContractGaps,
    actual_crud_failures: crudFlow.failures || [],
    browser_crud_missing_rows: browserCrudMissingRows,
    historical_carrying_blockers: historyBlockingRows.map((row) => ({
      legacy_source_model: row.legacy_source_model,
      legacy_source_name: row.legacy_source_name,
      source_records: row.source_records,
      state: row.state,
      indirect_carrying_targets: row.indirect_carrying_targets,
      carrying_targets: row.carrying_targets,
    })),
    historical_target_menu_gaps: historyTargetMenuGaps,
  };

  result.ok = Object.values(result.criteria).every(Boolean);
  result.decision = result.ok ? 'ready_for_full_business_use' : 'not_ready_for_full_business_use';

  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify({
    ok: result.ok,
    decision: result.decision,
    criteria: result.criteria,
    counts: result.counts,
    output: OUTPUT_PATH,
  }, null, 2));
  if (!result.ok) process.exit(1);
}

main();
