# ITER-2026-04-10-1736 Report

## Batch
- Batch: `P1-Batch59`
- Mode: `implement`
- Stage: `FORM-006 action placement remediation`

## Architecture declaration
- Layer Target: `backend scene-orchestration contract supply`
- Module: `form action source/placement normalization`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: 修复 button_box 与 stat_buttons 重复承载同一动作的问题。

## Change summary
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - 增加 form action 去重规则：
    - 区域内去重
    - 跨区域去重（`button_box` 为主源，`stat_buttons` 仅保留差异项）
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 在 v2 runtime contract 路径同步应用相同去重策略。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1736.yaml` ✅
- `make restart` ✅
- `python3 scripts/verify/form_action_dedup_audit.py --json` ✅

## Audit delta
- 修复前（1735）：`total_actions=11`, `duplicate_action_keys=2`, `status=BLOCKED`
- 修复后（1736）：`total_actions=9`, `duplicate_action_keys=0`, `status=PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：仅调整契约动作承载组织，不改变业务动作语义与权限。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore addons/smart_core/v2/services/ui_contract_service.py`

## Next suggestion
- 进入 FORM-004（surface regions）审计或修复批，补齐 header/button_box/statusbar 区域语义完备性。
