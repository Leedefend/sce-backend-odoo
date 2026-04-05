# ITER-2026-04-03-935

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: delivery menu integrity guard
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `scripts/verify/product_delivery_menu_integrity_guard.py`
  - `agent_ops/tasks/ITER-2026-04-03-935.yaml`
- implementation:
  - replaced strict full-list equality with release-core integrity semantics:
    - core expected keys must match in order;
    - core routes must be non-empty;
    - extension keys allowed only under `release.native_preview.` prefix.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-935.yaml`: PASS
- `python3 -m py_compile scripts/verify/product_delivery_menu_integrity_guard.py`: PASS
- `... make verify.product.delivery_menu_integrity_guard DB_NAME=sc_demo`: PASS
  - artifact confirms core pass + extension capture:
  - `artifacts/backend/product_delivery_menu_integrity_guard.json`
- `... make verify.release.operator_surface.v1 DB_NAME=sc_demo`: FAIL
  - failed at downstream gate `verify.product.delivery_policy_guard`
  - failure summary indicates policy guard still expects strict full menu set equality.

## Risk Analysis

- medium: initial blocker (`menu_integrity_guard`) is resolved, but release chain remains blocked by next strict policy guard.
- stop condition triggered: acceptance_failed.

## Rollback Suggestion

- `git restore scripts/verify/product_delivery_menu_integrity_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-935.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-935.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-935.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `blocked`

## Next Iteration Suggestion

- open dedicated low-cost governance line for `verify.product.delivery_policy_guard` drift (scan -> screen -> verify), then implement alignment in that guard.
