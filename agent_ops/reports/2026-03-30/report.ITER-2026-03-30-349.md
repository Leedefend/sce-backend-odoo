# ITER-2026-03-30-349 Report

## Summary

- Formalized the preview publication boundary into two explicit lanes:
  - native business-fact lane
  - custom-frontend supplement lane
- Locked the product interpretation that original business facts continue to provide `model / menu / action` truth.
- Locked the product interpretation that portal-style entries are no longer evaluated against the abandoned native frontend.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-349.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-349.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-349.yaml` -> PASS

## Policy Output

- Native business-fact lane:
  - owns concrete `model / menu / action`
  - includes `act_window`, `scene_route_only`, and business-valid `actions.server` entries
  - remains the authoritative source for business availability and prerequisite tracing

- Custom-frontend supplement lane:
  - owns portal-style or special-rendering user surfaces
  - may still be published from native menus/actions
  - is not blocked by the abandoned native portal frontend anymore

- Practical effect on the current preview menu set:
  - `项目驾驶舱` and `执行结构` stay in the native-fact lane
  - `工作台 / 生命周期驾驶舱 / 能力矩阵` stay published from native anchors, but their usable surface is now owned by the custom frontend lane

## Risk Analysis

- Risk level remains low because this is governance-only.
- The main ambiguity is now removed, which reduces future rework risk across both backend publication and frontend fulfillment.
- No ACL, business-model, or frontend rendering behavior was changed in this batch.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-349.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-349.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-349.json`

## Next Suggestion

- Start the next implementation batch on the custom frontend lane, using the native fact anchors as source truth for:
  - `工作台`
  - `生命周期驾驶舱`
  - `能力矩阵`
