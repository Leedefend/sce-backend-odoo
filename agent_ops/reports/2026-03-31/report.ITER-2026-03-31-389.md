# ITER-2026-03-31-389 Report

## Summary

- Repaired the explicit scene-target consistency drift for `portal.capability_matrix`.
- Aligned the backend scene publication target with the SPA-owned route:
  - from `/s/project.management`
  - to `/s/portal.capability_matrix`
- Kept the batch minimal: only scene publication metadata was changed; no frontend, business-fact, ACL, or high-risk domain files were touched.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-389.yaml`
- `addons/smart_construction_scene/data/sc_scene_layout.xml`
- `addons/smart_construction_scene/profiles/scene_registry_content.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-389.md`
- `agent_ops/state/task_results/ITER-2026-03-31-389.json`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-389.yaml` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_scene DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Architecture Declaration

- Layer Target: `Scene Layer`
- Affected Modules: `addons/smart_construction_scene`
- Kernel or Scenario: `scenario`
- Reason: repair publication-target drift without changing business logic or frontend behavior

## Implementation Notes

### Scene Layout Alignment

- Updated `portal.capability_matrix` scene version payload target in:
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
- New target route:
  - `/s/portal.capability_matrix`

### Registry Profile Alignment

- Updated scene registry source in:
  - `addons/smart_construction_scene/profiles/scene_registry_content.py`
- New target route:
  - `/s/portal.capability_matrix`

This keeps runtime scene facts and SPA route ownership aligned for the same scene key.

## Risk Analysis

- Risk remained low.
- No forbidden path was touched.
- No business facts, payment/settlement/account semantics, manifests, or frontend files were changed.

## Rollback

- `git restore addons/smart_construction_scene/data/sc_scene_layout.xml`
- `git restore addons/smart_construction_scene/profiles/scene_registry_content.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-389.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-389.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-389.json`

## Next Suggestion

- Run a focused post-repair consistency audit and confirm that `能力矩阵` has moved from explicit drift to aligned status.
