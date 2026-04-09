# ITER-2026-04-09-1506 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 3 custom_action adjudicator`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService custom_action adjudicator`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 对可承接 act_window 提供统一 custom_action 解释结果，避免前端自行判定承接能力。

## Change summary
- 更新 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 新增 `SUPPORTED_CUSTOM_ACTION_VIEW_MODES = {tree,list,form,kanban}`。
  - 新增 `_resolve_custom_action_target`：
    - 仅处理 `ir.actions.act_window`
    - 要求 `action_exists = true`
    - 要求 `res_model` 与 `view_mode` 存在
    - 仅当 `view_mode` 全部属于承接集合时命中
  - 在解释流程中新增 scene 之后的 custom_action 分支：
    - `target_type = action`
    - `delivery_mode = custom_action`
    - `target = {action_id,res_model,view_mode,view_id?}`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1506.yaml` ✅
- `rg -n "def _resolve_custom_action_target|custom_action|act_window|view_mode" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅扩展解释层判定逻辑，facts-only 与前端侧边栏边界未触碰。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 4：native_bridge 判定（复杂 action 显式落原生桥接）。
