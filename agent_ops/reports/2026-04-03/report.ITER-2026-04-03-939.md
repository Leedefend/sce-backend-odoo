# ITER-2026-04-03-939

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: delivery policy guard
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `scripts/verify/product_delivery_policy_guard.py`
  - `agent_ops/tasks/ITER-2026-04-03-939.yaml`
- implementation:
  - replaced strict `menu_keys == nav_menu_keys` with release-core policy checks:
    - all policy menu keys must exist in runtime nav;
    - extension keys are allowed only under `release.native_preview.` prefix;
    - scene/capability strict checks remain unchanged.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-939.yaml`: PASS
- `python3 -m py_compile scripts/verify/product_delivery_policy_guard.py`: PASS
- `... make verify.product.delivery_policy_guard DB_NAME=sc_demo`: PASS
  - artifact: `artifacts/backend/product_delivery_policy_guard.json`
- `... make verify.release.operator_surface.v1 DB_NAME=sc_demo`: FAIL
  - downstream failure moved to `verify.edition.session_context_guard`
  - failure type: Playwright navigation timeout in `scripts/verify/edition_session_context_guard.mjs`

## Risk Analysis

- medium: this batch successfully removed `delivery_policy_guard` blocker, but release chain remains blocked by next gate (`edition.session_context_guard`).
- stop condition triggered: acceptance_failed.

## Rollback Suggestion

- `git restore scripts/verify/product_delivery_policy_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-939.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-939.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-939.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `blocked`

## Next Iteration Suggestion

- open low-cost governance line for `verify.edition.session_context_guard` timeout drift (`scan -> screen -> verify`) before any implementation change.
