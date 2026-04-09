# ITER-2026-04-09-1505 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 2 scene mapping`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService scene mapper`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 接入显式 scene 映射优先级，确保菜单解释先命中 scene 再走后续分支。

## Change summary
- 更新 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 新增 `__init__(env)`，支持按需解析 xmlid -> id。
  - 新增 `scene resolver` 组装流程：
    - `_build_scene_resolver`
    - `_merge_explicit_scene_map`
    - `_merge_scene_registry_mapping`
    - `_resolve_xmlid_to_res_id`
    - `_resolve_scene_key`
  - 显式 scene 命中规则：
    - 优先 `menu_id -> scene_key`
    - 其次 `action_id -> scene_key`
    - 支持从 scene registry 的 `menu_xmlid/action_xmlid` 回填。
  - 命中 scene 后统一输出：
    - `target_type = scene`
    - `delivery_mode = custom_scene`
    - `target.scene_key`
    - `active_match.scene_key`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1505.yaml` ✅
- `rg -n "def _build_scene_resolver|def _resolve_scene_key|custom_scene|scene_key" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅扩展解释层 scene 解析路径；未修改事实层接口与前端实现。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 3：act_window 自定义承接判定（`custom_action`）。
