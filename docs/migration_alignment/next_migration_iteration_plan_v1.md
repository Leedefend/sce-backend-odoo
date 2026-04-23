# Next Migration Iteration Plan v1

Status: PLAN_READY

Task: `ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN`

## Current Anchor

- Project baseline lane is already migrated.
- Partner L4 create-only lane is closed under the current rule set: remaining create candidates are `0`.
- Project-member neutral carrier lane is closed at `7389` neutral carrier rows, with remaining evidence rows `0`.
- Contract migration must not be opened as a write lane until partner blocked-row remainder is consolidated and the partner baseline is declared stable enough for downstream reference checks.

## Layer Decision

- Layer Target: `Migration Iteration Planning`
- Module: `docs/migration_alignment` and `agent_ops`
- Module Ownership: migration governance surface
- Kernel or Scenario: scenario
- Backend Sub-Layer: migration-governance
- Reason: this batch produces the next migration schedule and gates only. It does not emit business facts, scene orchestration, frontend behavior, or database mutations.

## Next Lane

Open the next low-risk lane as a no-DB partner blocked-remainder consolidation screen.

Recommended task id:

`ITER-2026-04-15-PARTNER-L4-BLOCKED-REMAINDER-CONSOLIDATED-SCREEN`

Objective:

Turn the post-create-only partner L4 blocked remainder into one machine-readable decision table that states which rows are already resolved, which rows need discard evidence, which rows have a clean canonical create/update design, and which rows must stay blocked.

## Why This Lane Comes Next

The frozen migration order keeps partner before contract, receipt, payment/settlement, and file lanes. Partner clean create-only candidates are exhausted, but the remaining blocked population still controls downstream reference readiness. Opening contract writes before this consolidation would mix unresolved partner identity risk into downstream facts.

The next lane is therefore not a DB write. It is a bounded screen that reconciles existing partner L4 reports and creates one current remainder view.

## Inputs

Use existing migration reports and artifacts only. Do not rescan the whole repository.

Primary inputs:

- `docs/migration_alignment/partner_l4_final_postwrite_nodb_refresh_report_v1.md`
- `docs/migration_alignment/partner_l4_remaining365_blocked_screen_report_v1.md`
- `docs/migration_alignment/partner_l4_remaining190_blocked_screen_report_v1.md`
- `docs/migration_alignment/partner_l4_same_tax_company_supplier_conflict_screen_report_v1.md`
- `docs/migration_alignment/partner_l4_same_tax_company_supplier_canonical_write_design_report_v1.md`
- `docs/migration_alignment/partner_l4_same_tax_canonical_102_postwrite_nodb_refresh_report_v1.md`
- `docs/migration_alignment/partner_l4_remaining88_blocked_screen_report_v1.md`
- later partner L4 write and post-write reports already present under `docs/migration_alignment/`

## Stage Plan

### Stage 1: Consolidated No-DB Screen

Scope:

- Read only existing partner L4 artifacts and reports.
- Produce one current blocked-remainder table and one short report.
- Do not write `res.partner`.
- Do not modify migration scripts unless a later dedicated implementation task is opened.

Expected deliverables:

- `docs/migration_alignment/partner_l4_blocked_remainder_consolidated_screen_report_v1.md`
- `agent_ops/state/task_results/ITER-2026-04-15-PARTNER-L4-BLOCKED-REMAINDER-CONSOLIDATED-SCREEN.json`
- optional CSV/JSON artifact under the existing migration artifact location if the active task allowlist declares it.

Decision columns:

- `legacy_row_id`
- `blocking_reason`
- `current_route`
- `resolved_by_existing_write`
- `discard_candidate`
- `canonical_partner_candidate`
- `requires_manual_review`
- `recommended_next_task`

Completion criteria:

- Remaining blocked count is current and traceable.
- Every row has exactly one recommended route.
- The next write-design lane, if any, is bounded by row count and rollback target.
- If no safe route remains, the screen declares partner L4 stable-with-known-discard instead of forcing a write.

### Stage 2: Write Design Only If Stage 1 Finds Safe Candidates

Scope:

- Create a no-DB write design for one route only.
- Include rollback target generation.
- Include duplicate and canonical-tax guard.
- Keep missing-tax, unsafe-name, and ambiguous company/supplier rows out unless the screen has already classified them.

Stop if:

- The design requires fuzzy merge without deterministic source evidence.
- The design would update existing partner identity without a dedicated update-governance task.
- The route touches payment, settlement, accounting, ACL, manifest, or frontend paths.

### Stage 3: Contract Readiness Screen

Open only after Stage 1 declares partner baseline stable enough for downstream references.

Scope:

- No contract DB writes.
- Check whether migrated contract source rows can resolve counterparties against the current partner baseline.
- Produce missing-reference buckets before any contract write task exists.

Stop if:

- Contract data requires unresolved partner identity decisions.
- Any payment, settlement, or accounting semantics are needed to judge readiness.

## Forbidden In This Plan

- DB writes.
- `res.partner` create/update/upsert.
- Contract write or partner backfill.
- Project-member responsibility fact write.
- Payment, settlement, accounting, ACL, record-rule, manifest, frontend, or addon changes.
- Repo-wide scan.

## Verification For This Plan Batch

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.yaml`
- `test -s docs/migration_alignment/next_migration_iteration_plan_v1.md`
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.json >/tmp/ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.json.pretty`
- `make verify.native.business_fact.static`
- `git diff --check`

## Rollback

Restore only the plan batch artifacts:

`git restore agent_ops/tasks/ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.yaml docs/migration_alignment/next_migration_iteration_plan_v1.md agent_ops/state/task_results/ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.json agent_ops/reports/2026-04-15/report.ITER-2026-04-15-NEXT-MIGRATION-ITERATION-PLAN.md docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next Execution Opportunity

Create and run:

`ITER-2026-04-15-PARTNER-L4-BLOCKED-REMAINDER-CONSOLIDATED-SCREEN`

This should be the next migration-mainline task before contract readiness or any downstream write lane.
