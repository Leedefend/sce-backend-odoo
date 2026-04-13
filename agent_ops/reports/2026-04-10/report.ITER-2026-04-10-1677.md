# ITER-2026-04-10-1677 Report

## Batch
- Batch: `P1-Batch6`
- Mode: `implement`
- Stage: `focus intent promotion rollback state machine`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core focus-intent promotion rollback governance`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 为三条 focus intents 建立可审计的 promotion/rollback 路径，并接入治理主门禁。

## Change summary
- 新增：`scripts/verify/v2_focus_intent_promotion_state_machine_audit.py`
  - 读取 `v2_focus_intent_compare_failure_summary` 的 `allow_v2_candidate` 信号。
  - 基于当前 `v2_intent_route_policy` 输出三条 focus intents 的 `transition_plan`。
  - 强约束：当 `allow_v2_candidate=false` 且仍存在 `v2_primary` 时直接 `FAIL`（`v2_primary_without_candidate`）。
- 新增：`artifacts/v2/v2_focus_intent_promotion_state_machine_v1.json`
  - 冻结状态机快照（focus intents / allowed states / allowed actions / hard fail 条件）。
- 更新：`scripts/verify/v2_app_governance_gate_audit.py`
  - 将 `v2_focus_intent_promotion_state_machine_audit.py` 纳入 blocking checks。
- 更新：`artifacts/v2/v2_app_governance_output_schema_v1.json`
  - 将新增状态机审计加入 `expected_checks`。
- 更新：`docs/ops/v2_app_governance_gate_usage_v1.md`
  - 补充状态机审计用法与阻断语义说明。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1677.yaml` ✅
- `python3 scripts/verify/v2_focus_intent_promotion_state_machine_audit.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_compare_failure_summary.py --json` ✅
- `python3 scripts/verify/v2_dual_track_route_policy_audit.py --json` ✅
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅
- `python3 scripts/verify/v2_app_governance_output_schema_audit.py --json` ✅
- `python3 -m py_compile scripts/verify/v2_focus_intent_promotion_state_machine_audit.py scripts/verify/v2_app_governance_gate_audit.py` ✅
- `rg -n "v2_focus_intent_promotion_state_machine_audit.py|allow_v2_candidate|rollback_to_v2_shadow" ...` ✅

## Core outcome
- 当前三条 focus intents 处于 `v2_shadow`，且 `allow_v2_candidate=true`。
- 状态机输出一致的升级建议：三条均 `candidate_ready`，动作 `promote_to_v2_primary`。
- governance gate 保持全绿（24/24），并新增状态机审计为阻断检查。

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批仅新增治理审计与快照，不改变业务事实、权限、财务、ACL 语义。

## Rollback suggestion
- `git restore scripts/verify/v2_focus_intent_promotion_state_machine_audit.py artifacts/v2/v2_focus_intent_promotion_state_machine_v1.json scripts/verify/v2_app_governance_gate_audit.py artifacts/v2/v2_app_governance_output_schema_v1.json docs/ops/v2_app_governance_gate_usage_v1.md`

## Next suggestion
- 进入 `1678`：在独立低风险批次中按状态机建议执行三条 focus intents 的 `v2_shadow -> v2_primary` 受控提升，并保留一键回滚到 `v2_shadow` 的策略快照。
