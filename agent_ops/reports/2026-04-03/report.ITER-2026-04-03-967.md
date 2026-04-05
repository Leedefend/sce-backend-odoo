# ITER-2026-04-03-967

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: user-facing menu projection strategy
- risk: low
- publishability: accepted

## Summary of Change

- updated:
  - `addons/smart_core/delivery/menu_service.py`
  - `addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
  - `agent_ops/tasks/ITER-2026-04-03-967.yaml`
  - `agent_ops/reports/2026-04-03/report.ITER-2026-04-03-967.md`
  - `agent_ops/state/task_results/ITER-2026-04-03-967.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - unified projection now keeps native leaf action context from leaf-level fields when `meta.action_id` is absent.
  - merged policy entries now skip no-action/no-model aliases (except `/my-work`) to reduce context-missing click targets.
  - tests updated and expanded for leaf-level action fallback.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-967.yaml`: PASS
- `python3 addons/smart_core/tests/test_delivery_menu_service_native_preview.py`: PASS (`Ran 5 tests`, `OK`)
- `... make restart` (prod-sim): PASS
- `... make verify.portal.login_browser_smoke.host`: PASS
  - artifact: `artifacts/codex/login-browser-smoke/20260405T001725Z`

## Risk Analysis

- low: scene-orchestration projection hardening only; no ACL/business-fact change.

## Rollback Suggestion

- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-967.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-967.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-967.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `accepted`

## Next Iteration Suggestion

- add dedicated unified menu leaf click smoke gate before release decision.
