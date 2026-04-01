# ITER-2026-03-31-437 Report

## Summary

- Audited the real repository dependency surface around
  `smart_construction_bootstrap`.
- Decided that the safest migration path is **new neutral platform/bootstrap
  module + temporary compatibility shim**, not an in-place direct rename.
- Confirmed that direct rename would immediately impact existing manifests,
  reset scripts, verify scripts, and architecture/runbook documentation.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-437.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-437.md`
- `agent_ops/state/task_results/ITER-2026-03-31-437.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-437.yaml` -> PASS
- `rg -n "smart_construction_bootstrap" addons scripts docs` -> PASS

## Audit Result

Repository references prove that `smart_construction_bootstrap` is still part of
the active install/verify graph:

- dependency edge:
  - `addons/smart_construction_seed/__manifest__.py`
- install/reset path:
  - `scripts/db/reset.sh`
- verification path:
  - `scripts/verify/baseline.sh`
  - `scripts/verify/demo.sh`
- docs/runbooks:
  - `docs/ops/runbook_init_onepage.md`
  - `docs/architecture/module_boundaries.md`
  - `docs/architecture/module_boundaries.zh.md`
  - `docs/architecture/modules.md`

That means a direct rename would be a higher-risk batch because it would force
simultaneous changes across:

- module dependency graph
- fresh DB bootstrap path
- verification scripts
- documentation references

## Outcome

Safest migration strategy:

1. create a new neutral platform/bootstrap module
   - example direction:
     - `smart_platform_bootstrap`
     - `smart_system_bootstrap`
2. keep `smart_construction_bootstrap` as a temporary compatibility shim
3. gradually move repository references and dependencies to the new neutral
   module
4. retire the shim only after:
   - install path is migrated
   - verify path is migrated
   - dependent manifests are migrated
   - docs are migrated

Rejected strategy for the next batch:

- direct in-place rename / relocation of `smart_construction_bootstrap`

## Risk Analysis

- Classification: `PASS`
- The current batch is governance-only and low risk.
- The next real migration batch is no longer pure taxonomy work because it will
  touch:
  - `__manifest__.py`
  - install scripts
  - verification scripts
  - documentation references

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-437.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-437.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-437.json`

## Next Suggestion

- Open a dedicated migration-governance batch that freezes:
  - the target neutral module name
  - shim lifetime and removal condition
  - dependency transition order
  - script/doc migration order
