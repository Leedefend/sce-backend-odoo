# Phase 15-A First Pilot Readiness

## 1. What Changed
- Goal:
  - Move v0.1 from controlled usability to first-pilot readiness.
- Completed:
  - added `pilot_precheck` runtime block for execution
  - added pilot-readiness guard and aggregate verify target
  - strengthened blocked copy and single-open-task explanations in frontend
  - documented pilot configuration and Odoo native dependency boundaries
- Not completed:
  - multi-task pilot execution remains out of scope

## 2. Impact Scope
- Modules:
  - `addons/smart_construction_core`
  - `frontend/apps/web`
  - `scripts/verify`
  - `docs/ops`
- Startup chain:
  - No
- Contract:
  - Yes, execution runtime blocks now include `pilot_precheck`
- Public intent:
  - No rename, no new public intent

## 3. Risks
- P0:
  - None identified under single-open-task pilot scope
- P1:
  - Projects with incomplete setup or multiple open tasks now surface explicit pilot blockers
- P2:
  - Users may still confuse native kanban visuals with business state unless playbook is followed

## 4. Verification
- Commands:
  - `make restart`
  - `make verify.product.project_execution_entry_contract_guard DB=sc_demo`
  - `make verify.product.project_execution_block_contract_guard DB=sc_demo`
  - `make verify.product.project_execution_pilot_precheck_guard DB=sc_demo`
  - `make verify.frontend_api DB=sc_demo`
  - `make verify.product.v0_1_pilot_readiness DB=sc_demo`
- Result:
  - PASS

## 5. Artifacts
- `artifacts/backend/product_project_execution_entry_contract_guard.json`
- `artifacts/backend/product_project_execution_block_contract_guard.json`
- `artifacts/backend/product_project_execution_pilot_precheck_guard.json`
- `artifacts/backend/product_project_execution_consistency_guard.json`
- `artifacts/backend/system_init_latency_budget_guard.json`

## 6. Rollback
- Commit:
  - revert Phase 15-A commit(s)
- Method:
  - revert backend/frontend/verify/docs changes
  - `make restart`

## 7. Next Batch
- Goal:
  - decide whether first-pilot feedback justifies expanding beyond `single_open_task_only`
- Preconditions:
  - collect pilot operator feedback on precheck friction and blocked reasons
