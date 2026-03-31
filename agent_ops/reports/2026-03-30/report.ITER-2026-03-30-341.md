# ITER-2026-03-30-341 Report

## Summary

- Added explicit metadata describing stable release groups versus native preview groups in delivery navigation output.
- Kept the additive native preview publication behavior from `340` unchanged.
- Expanded focused tests so frontend consumers can now rely on machine-readable release-nav semantics.

## Changed Files

- `addons/smart_core/delivery/menu_service.py`
- `addons/smart_core/delivery/delivery_engine.py`
- `addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `agent_ops/tasks/ITER-2026-03-30-341.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-341.yaml` -> PASS
- `python3 -m unittest discover -s addons/smart_core/tests -p 'test_delivery_menu_service_native_preview.py'` -> PASS

## Risk Analysis

- Risk level remains low.
- Metadata is additive; existing group composition and permission pruning stay unchanged.
- Frontend can now consume explicit semantics without inferring from labels, reducing later coupling risk.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-341.yaml`
- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/delivery/delivery_engine.py`
- `git restore addons/smart_core/tests/test_delivery_menu_service_native_preview.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-341.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-341.json`

## Next Suggestion

- Consume `delivery_engine_v1.meta.native_preview_group_key` and the group/leaf counts in the frontend sidebar.
- Run a live PM `system.init` check so the new metadata can be confirmed against a real user session payload.
