# ITER-2026-03-30-353 Report

## Summary

- Removed direct `sc.scene` and `sc.scene.tile` seed records from the industry fact data file [sc_scene_seed.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/sc_scene_seed.xml).
- Preserved all `sc.capability` seed facts in the same file.
- Completed the first safe cleanup step for scene-data pollution inside `smart_construction_core`.

## Changed Files

- `addons/smart_construction_core/data/sc_scene_seed.xml`
- `agent_ops/tasks/ITER-2026-03-30-353.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-353.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-353.yaml` -> PASS
- `bash -lc "if rg -n 'model=\"sc.scene|model=\"sc.scene.tile' addons/smart_construction_core/data/sc_scene_seed.xml; then exit 1; fi"` -> PASS

## Boundary Result

- `smart_construction_core/data/sc_scene_seed.xml` now only contains capability facts.
- Direct scene records are no longer seeded from the industry fact-layer file.
- Scene ownership for those records is expected to stay with `smart_construction_scene`, which already contains scene-side records and updates around `smart_construction_core.sc_scene_default`.

## Risk Analysis

- Risk level is medium but controlled.
- This batch avoids the higher-risk runtime migration of scene maps that still live in [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/core_extension.py).
- Remaining scene-semantics pollution still exists in runtime extension hooks and role-surface metadata; that must be migrated in a separate batch instead of being hard-removed here.

## Rollback

- `git restore addons/smart_construction_core/data/sc_scene_seed.xml`
- `git restore agent_ops/tasks/ITER-2026-03-30-353.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-353.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-353.json`

## Next Suggestion

- Start the next cleanup batch on the runtime scene semantics still mixed into [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/core_extension.py).
- That next batch must migrate active scene hooks into the scene layer before removing them from the industry core module.
