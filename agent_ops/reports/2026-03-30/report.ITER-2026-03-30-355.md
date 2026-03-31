# ITER-2026-03-30-355 Report

## Summary

- Removed direct `scene_key` and scene `route` fields from workspace business rows built in [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/core_extension.py).
- Moved workspace collection to scene resolution into [workspace_home_scene_content.py](/mnt/e/sc-backend-odoo/addons/smart_construction_scene/profiles/workspace_home_scene_content.py) by adding exact source-key mapping for:
  - `task_items`
  - `payment_requests`
  - `risk_actions`
  - `project_actions`
- This keeps business action facts in `smart_construction_core` while letting the scene layer decide the final scene target.

## Changed Files

- `addons/smart_construction_core/core_extension.py`
- `addons/smart_construction_scene/profiles/workspace_home_scene_content.py`
- `agent_ops/tasks/ITER-2026-03-30-355.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-355.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-355.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_core/core_extension.py addons/smart_construction_scene/profiles/workspace_home_scene_content.py` -> PASS
- `python3 -m unittest discover -s addons/smart_core/tests -p 'test_workspace_home_source_routing_helper.py'` -> PASS
- `bash -lc "sed -n '80,280p' addons/smart_construction_core/core_extension.py | rg -n 'scene_key|route'"` -> PASS (no matches)

## Boundary Result

- `smart_construction_core` workspace collections now carry only business facts such as:
  - title
  - description
  - status
  - count
  - source detail
  - business ids / amounts / deadlines

- `smart_construction_scene` now owns the exact scene routing decision for the workspace business collections:
  - `task_items -> task.center`
  - `payment_requests -> finance.payment_requests`
  - `risk_actions -> risk.center`
  - `project_actions -> project.management`

## Risk Analysis

- Risk level remained medium because this batch changed the effective scene-resolution path for workspace business rows.
- The migration remained low-blast-radius because:
  - source keys were already stable collection identifiers
  - the workspace source-routing helper already supports provider-owned resolution
  - exact mappings were added before removing core-side scene fields
- No ACL, financial semantics, or frontend code were changed in this batch.

## Rollback

- `git restore addons/smart_construction_core/core_extension.py`
- `git restore addons/smart_construction_scene/profiles/workspace_home_scene_content.py`
- `git restore agent_ops/tasks/ITER-2026-03-30-355.yaml`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-355.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-355.json`

## Next Suggestion

- Continue scanning `smart_construction_core` for any remaining scene-oriented payload fields embedded in business-fact rows or ext facts.
- After that, the industry fact layer can be considered materially cleaned of scene semantics for this line.
