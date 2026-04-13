# ITER-2026-04-09-1561 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `B2-3 dispatcher purity`

## Architecture declaration
- Layer Target: `Controller protocol adapter layer`
- Module: `intent dispatcher`
- Module Ownership: `smart_core controllers`
- Kernel or Scenario: `kernel`
- Reason: 将 alias/schema 与 permission error detail 规则移出 dispatcher，降低语义耦合。

## Change summary
- 新增：`addons/smart_core/controllers/intent_governance.py`
  - `canon_intent`
  - `resolve_request_schema_key`
- 新增：`addons/smart_core/controllers/intent_permission_details.py`
  - `build_permission_error_details`
- 更新：`addons/smart_core/controllers/intent_dispatcher.py`
  - 移除内联 alias/schema map
  - 移除 `_permission_error_details`
  - 改为调用新 helper
- 更新：`docs/architecture/backend_core_refactor_blueprint_v1.md`
  - 新增 `B2-3 implement (2026-04-09)`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1561.yaml` ✅
- `python3 -m py_compile ...` ✅
- helper wiring grep ✅
- blueprint status grep ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：规则归位为主，无权限事实模型变化。

## Rollback suggestion
- `git restore addons/smart_core/controllers/intent_dispatcher.py addons/smart_core/controllers/intent_permission_details.py addons/smart_core/controllers/intent_governance.py docs/architecture/backend_core_refactor_blueprint_v1.md`

## Next suggestion
- 进入 `B2-4 implement`：legacy compatibility adapter 收口（load_view 兼容补丁外移）。
