# ITER-2026-03-30-358 Report

## Summary

- Moved `my_work` scene-key ownership into `smart_construction_scene` by introducing a dedicated scene-target helper for item, section, and summary payloads.
- Removed direct scene-key assignment from `smart_construction_core.handlers.my_work_summary` business row builders so they now emit business facts only.
- Kept the output contract shape stable by continuing to expose `scene_key` and `target.scene_key`, but those values are now resolved by the scene layer instead of the industry module.

## Changed Files

- `addons/smart_construction_scene/services/my_work_scene_targets.py`
- `addons/smart_construction_scene/services/__init__.py`
- `addons/smart_construction_core/services/my_work_aggregate_service.py`
- `addons/smart_construction_core/handlers/my_work_summary.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-358.md`
- `agent_ops/state/task_results/ITER-2026-03-30-358.json`
- `agent_ops/tasks/ITER-2026-03-30-359.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-358.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_core/handlers/my_work_summary.py addons/smart_construction_core/services/my_work_aggregate_service.py addons/smart_construction_scene/services/my_work_scene_targets.py addons/smart_construction_scene/services/__init__.py` -> PASS
- `make verify.smart_core` -> PASS

## Notes

- A direct bare-python attempt to run `python3 -m unittest discover -s addons/smart_construction_core/tests -p 'test_my_work_backend.py'` failed because the plain interpreter environment does not load the `odoo` package. This was treated as a local runner limitation rather than a code regression, and the authoritative gated verification remained `make verify.smart_core`.

## Risk Analysis

- Risk remains low because the batch preserves the existing payload fields and only migrates who computes their scene semantics.
- `project_execution_item_projection_service` rows may still pass explicit `scene_key` values through the aggregation path; that is intentional for this batch because deeper capability/projection cleanup is the next residual slice.
- No ACL, manifest, payment model, or settlement model paths were touched.

## Rollback

- `git restore addons/smart_construction_scene/services/my_work_scene_targets.py`
- `git restore addons/smart_construction_scene/services/__init__.py`
- `git restore addons/smart_construction_core/services/my_work_aggregate_service.py`
- `git restore addons/smart_construction_core/handlers/my_work_summary.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-358.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-358.json`
- `git restore agent_ops/tasks/ITER-2026-03-30-359.yaml`

## Next Suggestion

- Continue with the `P3` residual slice:
  - move `scene_key` ownership out of `capability_registry`, `project_execution_item_projection_service`, and `project_risk_alert_service`
  - keep business capability/projection facts in `smart_construction_core`
  - let `smart_construction_scene` own the scene target interpretation layer
