# ITER-2026-04-09-1508 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Menu Target Interpreter - Batch 5 url/unavailable adjudication`

## Architecture declaration
- Layer Target: `Navigation interpretation layer`
- Module: `MenuTargetInterpreterService url/unavailable adjudicator`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 为 url 与不可用节点建立统一解释与原因码输出，避免导航行为不确定。

## Change summary
- 更新 `addons/smart_core/delivery/menu_target_interpreter_service.py`
  - 新增 `UNAVAILABLE_REASON_CODES` 标准集合。
  - 新增 `_resolve_url_target`：
    - 命中 `ir.actions.act_url`
    - 输出 `target_type = url` + `delivery_mode = external_url`
    - 可选补充 `target.url`（env 可用时读取）
  - 新增 `_resolve_unavailable_reason`：
    - `ACTION_INVALID`
    - `DELIVERY_UNSUPPORTED`
    - `SCENE_UNRESOLVED`
    - `DIRECTORY_ONLY`
    - `TARGET_MISSING`
  - 在主解释流程接入 URL 分支与 unavailable 原因码归一。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1508.yaml` ✅
- `rg -n "TARGET_MISSING|ACTION_INVALID|external_url|target_type = \"url\"|PERMISSION_DENIED" addons/smart_core/delivery/menu_target_interpreter_service.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅解释层判定增强；未改 facts-only 与前端消费边界。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_target_interpreter_service.py`

## Next suggestion
- 进入 Batch 6：route 统一生成规则接入解释输出。
