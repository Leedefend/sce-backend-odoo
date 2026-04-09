# ITER-2026-04-09-1499 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Batch 2 - action 事实解析器`

## Architecture declaration
- Layer Target: `Platform fact layer`
- Module: `Menu action binding fact parser`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 仅补齐菜单 action 原始绑定事实，不进入导航解释字段。

## Change summary
- 更新 `addons/smart_core/delivery/menu_fact_service.py`
  - 在菜单事实上附加：
    - `action_type`
    - `action_id`
    - `action_model`
    - `action_exists`
    - `action_meta`
    - `action_parse_error`
  - 支持解析 `action_raw`，覆盖 `ir.actions.act_window/server/client/act_url`。
  - 对 `act_window` 输出原始事实：`res_model/view_mode/view_id/domain/context`。
  - 对解析失败、模型不支持、动作缺失均显式标记，不静默吞错。
- 更新 `artifacts/menu/menu_fact_snapshot_v1.json`
  - 补充 `node_schema`，冻结当前事实字段口径。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1499.yaml` ✅
- `rg -n "action_type|action_id|action_model|action_exists|action_meta" addons/smart_core/delivery/menu_fact_service.py` ✅
- `python3 -c "... has_flat ..."` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅事实字段扩展，不涉及前端、ACL、record rules、manifest 与业务语义。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_fact_service.py`
- `git restore artifacts/menu/menu_fact_snapshot_v1.json`

## Next suggestion
- 进入 Batch 3：菜单异常审计器与异常快照输出。
