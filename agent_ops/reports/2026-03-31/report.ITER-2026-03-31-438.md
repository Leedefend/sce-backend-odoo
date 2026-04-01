# ITER-2026-03-31-438 Report

## Summary

- Froze the transition plan for moving `smart_construction_bootstrap` into a
  neutral namespace.
- Selected `smart_platform_bootstrap` as the preferred target name.
- Fixed the compatibility-shim lifetime and the dependency/script/doc migration
  order.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-438.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-438.md`
- `agent_ops/state/task_results/ITER-2026-03-31-438.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-438.yaml` -> PASS
- `rg -n "smart_platform_|smart_system_" addons docs scripts` -> PASS
- `sed -n '1,220p' docs/architecture/platform_naming_alignment_v1.md` -> PASS

## Audit Result

### Target Name Decision

Preferred target physical module name:

- `smart_platform_bootstrap`

Reasons:

- repository architecture vocabulary is consistently `platform`-centric rather
  than `system`-centric
- `docs/architecture/platform_naming_alignment_v1.md` already uses platform
  naming as the long-term logic baseline
- there is no existing `smart_platform_*` or `smart_system_*` physical module,
  so this choice is still open and should be frozen before implementation

Rejected fallback name:

- `smart_system_bootstrap`

It is acceptable in principle, but it is less aligned with the repository's
current architecture vocabulary.

### Compatibility Shim Lifetime

Keep `smart_construction_bootstrap` as a compatibility shim until all of the
following are true:

1. dependent manifests stop requiring it
2. DB reset/install scripts stop installing it directly
3. verify scripts stop asserting its installation
4. docs/runbooks stop referencing it as the canonical bootstrap module

Shim removal condition:

- zero active manifest/script/verify/doc references remain

### Transition Order

Freeze the migration order as:

1. create `smart_platform_bootstrap`
2. turn `smart_construction_bootstrap` into a compatibility shim
3. migrate dependent manifests
   - first known edge: `addons/smart_construction_seed/__manifest__.py`
4. migrate install/reset scripts
   - `scripts/db/reset.sh`
5. migrate verify scripts
   - `scripts/verify/baseline.sh`
   - `scripts/verify/demo.sh`
6. migrate docs/runbooks
   - `docs/ops/runbook_init_onepage.md`
   - `docs/architecture/module_boundaries.md`
   - `docs/architecture/module_boundaries.zh.md`
   - `docs/architecture/modules.md`
7. remove shim only after the compatibility conditions are satisfied

## Outcome

The frozen low-risk transition plan is now:

- target module name: `smart_platform_bootstrap`
- migration strategy:
  - new module first
  - compatibility shim second
  - dependency/script/verify/doc migration third
- no direct in-place rename as the first implementation step

## Risk Analysis

- Classification: `PASS`
- This batch stayed governance-only.
- The next eligible step is no longer low-risk governance because it will
  require:
  - `addons/**`
  - `__manifest__.py`
  - install/verify script edits

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-438.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-438.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-438.json`

## Next Suggestion

- Open a dedicated high-risk migration implementation batch for:
  - creating `smart_platform_bootstrap`
  - wiring the compatibility shim
  - updating manifest/script/verify/doc references in the frozen order
