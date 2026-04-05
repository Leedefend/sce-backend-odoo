# ITER-2026-04-05-976

- status: PASS
- mode: implement
- layer_target: Delivery Simulation Runtime Alignment
- module: release gate and checklist policy baseline
- risk: low
- publishability: accepted

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-976.yaml`
  - `scripts/verify/extension_modules_guard.sh`
  - `scripts/ops/apply_extension_modules.sh`
  - `docs/ops/release_checklist_v0.3.0-stable.md`
  - `docs/ops/releases/templates/release_checklist_TEMPLATE.md`
  - `docs/ops/releases/templates/release_checklist_TEMPLATE.zh.md`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-976.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-976.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed `smart_construction_portal` from hard-required extension module gate.
  - kept `smart_scene` as recommended non-blocking hint in extension gate output.
  - aligned extension auto-apply policy with the new required token set.
  - synchronized release checklist docs with custom-frontend delivery baseline.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-976.yaml`: PASS
- `... make verify.extension_modules.guard DB_NAME=sc_prod_sim`: PASS
  - output now allows release with `smart_construction_core` baseline
  - emits informational hint when `smart_scene` is missing
- `... make policy.apply.extension_modules DB_NAME=sc_prod_sim`: PASS

## Risk Analysis

- low: governance-only policy and docs alignment; no business model, ACL, or
  financial semantics were modified.

## Rollback Suggestion

- `git restore scripts/verify/extension_modules_guard.sh`
- `git restore scripts/ops/apply_extension_modules.sh`
- `git restore docs/ops/release_checklist_v0.3.0-stable.md`
- `git restore docs/ops/releases/templates/release_checklist_TEMPLATE.md`
- `git restore docs/ops/releases/templates/release_checklist_TEMPLATE.zh.md`
- `git restore agent_ops/tasks/ITER-2026-04-05-976.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-976.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-976.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `accepted`

## Next Iteration Suggestion

- if you want to promote `smart_scene` from recommendation to hard requirement,
  open a dedicated staged governance task after scene-kernel delivery capability
  reaches mandatory baseline.
