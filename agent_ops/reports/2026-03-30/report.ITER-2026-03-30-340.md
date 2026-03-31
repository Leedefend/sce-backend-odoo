# ITER-2026-03-30-340 Report

## Summary

- Added backend native-preview projection for release navigation.
- Preserved existing stable release menu groups.
- Reused role-pruned native scene nav as the only source for additive preview publication.

## Changed Files

- `addons/smart_core/core/delivery_menu_defaults.py`
- `addons/smart_core/delivery/menu_service.py`
- `addons/smart_core/delivery/delivery_engine.py`
- `addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `agent_ops/tasks/ITER-2026-03-30-340.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-340.yaml` -> PASS
- `python3 -m unittest discover -s addons/smart_core/tests -p 'test_delivery_menu_service_native_preview.py'` -> PASS

## Risk Analysis

- Risk level remains low.
- Change is additive and limited to release navigation output assembly.
- Stable product policy semantics, ACL, and business facts were not changed.
- Native preview group only consumes already role-pruned native nav, so it should not widen permissions.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-340.yaml`
- `git restore addons/smart_core/core/delivery_menu_defaults.py`
- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/delivery/delivery_engine.py`
- `git restore addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-340.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-340.json`

## Next Suggestion

- Update the frontend sidebar presenter to show the new native preview group distinctly from stable release groups.
- Run a live `system.init` contract check to confirm `delivery_engine_v1.nav` and `release_navigation_v1.nav` now include the additive preview group for a PM user.
