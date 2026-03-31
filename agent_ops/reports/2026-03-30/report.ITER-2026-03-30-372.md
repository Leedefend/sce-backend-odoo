# ITER-2026-03-30-372 Report

## Summary

- Classified the remaining `smart_construction_core/data/*.xml` files by ownership.
- Confirmed that after `371`, no further obvious demo business-facts files remain in `smart_construction_core/data`.
- Narrowed the remaining issue from “demo facts parked in core” to “some runtime/config seeds may still belong in a different module, but not in demo”.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-372.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-372.md`
- `agent_ops/state/task_results/ITER-2026-03-30-372.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-372.yaml` -> PASS

## Classification

### A. Runtime Baseline / Core Domain Config (`8`)

- `cron_signup_throttle_gc.xml`
- `material_plan_tier_actions.xml`
- `payment_request_tier_actions.xml`
- `project_next_action_rules.xml`
- `project_stage_data.xml`
- `project_stage_requirement_items.xml`
- `sequence.xml`
- `tax.xml`

Reason:
- these records support runtime execution, workflows, transitions, numbering, or guarded baseline behavior
- they are not demo scenario facts

### B. Governance / Extension / Admin Bootstrap (`4`)

- `sc_cap_config_admin_user.xml`
- `sc_extension_params.xml`
- `sc_extension_runtime_sync.xml`
- `sc_subscription_default.xml`

Reason:
- these files bootstrap extension registration, admin defaults, or subscription/runtime behavior
- they are still data, but not demo business facts

### C. Orchestration / Capability Seeds (`2`)

- `sc_capability_group_seed.xml`
- `sc_scene_seed.xml`

Reason:
- these are not demo facts either
- but they may be candidates for a later ownership move out of `smart_construction_core`, depending on whether capability/scene semantics should live in scene/platform-oriented modules instead of domain core

## Main Conclusion

- The “move demo data out of core” line is now materially cleaner after `371`.
- There are no further obvious demo fact files under `smart_construction_core/data`.
- The next remaining question is different:
  - not `move to demo`
  - but `should some orchestration/bootstrap seeds move to scene/platform ownership?`

## Risk Analysis

- Risk remains low because this batch is audit-only.
- No code or data files were changed.
- The main remaining work is architectural classification, not demo-data relocation.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-372.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-372.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-372.json`

## Next Suggestion

- Open a governance audit on the remaining non-demo data ownership:
  - which seeds should stay in `smart_construction_core`
  - which should move to `smart_construction_scene` or another platform-aligned module
