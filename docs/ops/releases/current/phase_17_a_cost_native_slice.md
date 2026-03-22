# Phase 17-A: Cost Native Slice

## Goal
Implement the first v0.2 slice on top of Odoo native accounting facts without breaking the v0.1 baseline.

## Delivered
- Froze cost native mapping with:
  - primary carrier = `account.move`
  - secondary context = `project.project`
  - readonly aggregation boundary
- Added `cost_tracking_native_adapter` for read-only native fact access.
- Added platform orchestrator:
  - `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py`
- Added handlers:
  - `cost.tracking.enter`
  - `cost.tracking.block.fetch`
- Wired `project.execution` next actions to `cost.tracking.enter`.
- Added verifies:
  - `verify.product.cost_tracking_entry_contract_guard`
  - `verify.product.cost_tracking_block_contract_guard`
  - `verify.product.project_flow.execution_cost`

## Guard Result
- `verify.product.native_alignment_guard` must remain PASS because:
  - no `project.cost.*` shadow intent family was introduced
  - no `addons/smart_construction_core/(handlers|services)/project_cost*` path was introduced

## Follow-up
- Keep cost slice read-only until native write-side orchestration is explicitly designed.
