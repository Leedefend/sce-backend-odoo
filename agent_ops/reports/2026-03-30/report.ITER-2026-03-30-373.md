# ITER-2026-03-30-373 Report

## Summary

- Audited the remaining non-demo seed ownership in `smart_construction_core/data`.
- Determined that the remaining files split into three ownership outcomes:
  - should stay in domain core
  - should likely move to scene/platform-aligned ownership
  - should be treated as governance/bootstrap rather than demo

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-373.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-373.md`
- `agent_ops/state/task_results/ITER-2026-03-30-373.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-373.yaml` -> PASS

## Ownership Result

### A. Should Stay In `smart_construction_core`

These are domain runtime baselines or core workflow facts:

- `project_stage_data.xml`
- `project_stage_requirement_items.xml`
- `project_next_action_rules.xml`
- `material_plan_tier_actions.xml`
- `payment_request_tier_actions.xml`
- `sequence.xml`
- `tax.xml`
- `cron_signup_throttle_gc.xml`

Reason:
- they define domain runtime behavior, numbering, or module-local execution baselines
- they are not scene orchestration assets and not demo data

### B. Better Candidate For Scene / Platform-Aligned Ownership

- `sc_scene_seed.xml`
- `sc_capability_group_seed.xml`

Reason:
- these records define capability grouping and capability-entry semantics
- `smart_core` and `smart_construction_scene` already consume `sc.capability`
- their role is much closer to orchestration and capability exposure than to domain business facts

### C. Governance / Extension Bootstrap Candidates

- `sc_extension_params.xml`
- `sc_extension_runtime_sync.xml`
- `sc_subscription_default.xml`
- `sc_cap_config_admin_user.xml`

Reason:
- these are not demo facts and not classic domain runtime data
- they belong to extension registration, subscription/governance bootstrap, or admin bootstrap
- if the long-term rule is “industry core only keeps models/actions/menus/permissions”, these are more plausible move candidates than the domain workflow seeds

## Main Conclusion

- The “move demo facts to demo” line is now basically complete for `smart_construction_core/data`.
- The next meaningful cleanup line is different:
  - move orchestration/bootstrap seeds out of core
  - not move more business demo facts

## Risk Analysis

- Risk remains low because this batch is audit-only.
- But the next implementation batch would touch active seed ownership, so it needs a precise migration slice.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-373.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-373.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-373.json`

## Next Suggestion

- Open one focused migration batch for:
  - `sc_scene_seed.xml`
  - `sc_capability_group_seed.xml`
- Keep the domain runtime baseline files in core for now.
- Treat the extension/bootstrap files as a separate later cleanup line.
