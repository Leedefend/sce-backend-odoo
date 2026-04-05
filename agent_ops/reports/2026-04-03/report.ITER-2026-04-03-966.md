# ITER-2026-04-03-966

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
  - `frontend/apps/web/src/layouts/AppShell.vue`
  - `agent_ops/tasks/ITER-2026-04-03-966.yaml`
  - `agent_ops/reports/2026-04-03/report.ITER-2026-04-03-966.md`
  - `agent_ops/state/task_results/ITER-2026-04-03-966.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - backend now emits unified system-menu projection rooted at `root:system_menu`.
  - released policy entries are merged into native groups by scene anchor with dedupe (`menu_id/scene_key/route/menu_xmlid`).
  - release strategy markers are removed from user-facing payload path (`group:native_preview*` removed).
  - frontend disables release metadata rendering/badges and summary chips.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-966.yaml`: PASS
- `python3 addons/smart_core/tests/test_delivery_menu_service_native_preview.py`: PASS (`Ran 4 tests`, `OK`)
- `... make restart` (prod-sim): PASS
- `... make verify.portal.login_browser_smoke.host`: PASS
  - artifact: `artifacts/codex/login-browser-smoke/20260404T234120Z`
- `! rg -n "正式发布|原生预发布|group:native_preview" $LATEST/case_login_success.json`: PASS

## Risk Analysis

- low: scope is navigation projection and rendering metadata only; no business fact/ACL changes.

## Rollback Suggestion

- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `git restore frontend/apps/web/src/layouts/AppShell.vue`
- `git restore agent_ops/tasks/ITER-2026-04-03-966.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-966.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-966.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `accepted`

## Next Iteration Suggestion

- run manual user login visual check to confirm grouped system-menu readability on sidebar.
