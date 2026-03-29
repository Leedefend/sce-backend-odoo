# ITER-2026-03-29-247 Report

## Summary

Completed a backend chain boundary audit for:

- intent entry
- `UiContractHandler`
- `ActionDispatcher`
- `ActionResolver`
- native/fallback parse
- `AppViewConfig.get_contract_api`
- `PageAssembler`
- `ContractService.finalize_contract`
- `apply_contract_governance`

No product code under `addons/**` or `frontend/**` was modified in this batch.

## Layer Target

- Layer Target: `smart_core backend contract chain`
- Module: `intent / ui_contract / dispatcher / parser / view-contract / governance`
- Reason: clarify boundary ownership, identify duplication/fuzziness, keep architecture unchanged

## Changed Files

- [agent_ops/tasks/ITER-2026-03-29-247.yaml](/mnt/e/sc-backend-odoo/agent_ops/tasks/ITER-2026-03-29-247.yaml)
- [docs/ops/iterations/delivery_context_switch_log_v1.md](/mnt/e/sc-backend-odoo/docs/ops/iterations/delivery_context_switch_log_v1.md)
- [docs/architecture/backend_intent_dispatch_parse_assembly_boundaries.md](/mnt/e/sc-backend-odoo/docs/architecture/backend_intent_dispatch_parse_assembly_boundaries.md)

## Findings

1. `UiContractHandler.handle()` is the fuzziest boundary.
   It currently mixes request normalization, op inference, dispatch orchestration, render hint injection, governance application, and response envelope shaping.

2. `ActionDispatcher` is relatively clean.
   It already behaves like a proper orchestration layer and should stay focused on subject/action routing.

3. `ActionResolver` has a clear boundary.
   It owns action identity resolution and safe drill-down/materialization and should not absorb assembly logic.

4. Parse and view-projection are split, but `AppViewConfig` still carries too much lifecycle responsibility.
   It currently owns view fetching, parse coordination, fallback coordination, persistence, and API projection.

5. There are two governance concepts at different levels.
   `ContractGovernanceFilterService` is view-level runtime filtering, while `apply_contract_governance()` is page-delivery shaping. The boundary is valid, but the naming is easy to confuse.

6. `PageAssembler` is mostly an aggregation layer, but policy helpers are mixed into it.
   The main policy hotspots are field restriction to layout, relation-entry degradation, and access-policy synthesis.

7. Final normalization belongs to `ContractService.finalize_contract()`.
   This is the real contract assembly normalization layer and should remain the canonical post-assembly normalization point.

8. The biggest duplication risk is post-dispatch shaping.
   Both handler and service entrypoints perform overlapping “final delivery” work, which creates drift risk.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-247.yaml`

## Risk Analysis

- Low implementation risk in this batch because it is audit/documentation only.
- Medium architectural risk remains if cleanup begins without first choosing a single canonical post-dispatch pipeline.
- Highest ambiguity remains around `UiContractHandler` responsibilities and governance naming.

## Rollback

- `git restore docs/architecture/backend_intent_dispatch_parse_assembly_boundaries.md`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/tasks/ITER-2026-03-29-247.yaml`

## Next Suggestion

Run the next batch as a low-risk backend refactor plan, not a cross-module rewrite:

1. define one canonical post-dispatch contract pipeline
2. thin `UiContractHandler` into protocol-only helpers
3. rename/document view-level vs delivery-level governance
4. extract page-policy helpers out of `PageAssembler`
