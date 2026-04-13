# ITER-2026-04-10-1678 Report

## Batch
- Batch: `P1-Batch7`
- Mode: `implement`
- Stage: `focus intent controlled promotion to v2_primary`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core focus-intent controlled promotion`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 在 `allow_v2_candidate=true` 条件下执行三条 focus intents 受控提升，并固化回滚快照。

## Change summary
- 更新：`artifacts/v2/v2_intent_route_policy_v1.json`
  - 三条 focus intents 从 `v2_shadow` 提升到 `v2_primary`。
- 新增：`artifacts/v2/v2_focus_intent_route_policy_rollback_v1.json`
  - 固化 rollback-ready 快照，三条 focus intents 回退目标统一 `v2_shadow`。
- 更新：`scripts/verify/v2_focus_intent_promotion_state_machine_audit.py`
  - 新增 rollback 快照校验：若 fallback 非 `v2_shadow` 则失败。
- 更新：`docs/ops/v2_app_governance_gate_usage_v1.md`
  - 增补 rollback-ready 快照说明。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1678.yaml` ✅
- `python3 scripts/verify/v2_dual_track_route_policy_audit.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_promotion_state_machine_audit.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_compare_summary.py --json` ✅
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅
- `python3 scripts/verify/v2_app_governance_output_schema_audit.py --json` ✅
- `rg -n "session.bootstrap|meta.describe_model|ui.contract|v2_primary" artifacts/v2/v2_intent_route_policy_v1.json` ✅
- `rg -n "session.bootstrap|meta.describe_model|ui.contract|v2_shadow" artifacts/v2/v2_focus_intent_route_policy_rollback_v1.json` ✅

## Core outcome
- 三条 focus intents 路由决策已切换为 `v2_primary`。
- 状态机审计输出 `state=promoted`、`action=keep`。
- governance gate 维持全绿（24/24），未触发 stop condition。

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅变更路由策略与治理快照，不涉及 ACL、权限、财务与业务事实模型。

## Rollback suggestion
- `git restore artifacts/v2/v2_intent_route_policy_v1.json artifacts/v2/v2_focus_intent_route_policy_rollback_v1.json scripts/verify/v2_focus_intent_promotion_state_machine_audit.py docs/ops/v2_app_governance_gate_usage_v1.md`

## Next suggestion
- 进入 `1679`：执行 `v2_primary` 运行期 smoke 与差异风险屏蔽批次（保留 compare 诊断链可观测，确保可随时回退到 rollback 快照）。
