# ITER-2026-04-09-1562 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `B2-4 dispatcher purity`

## Architecture declaration
- Layer Target: `Controller protocol adapter layer`
- Module: `intent dispatcher`
- Module Ownership: `smart_core controllers`
- Kernel or Scenario: `kernel`
- Reason: 将 load_view legacy 兼容修补逻辑外移为独立 adapter，完成 B2 收尾。

## Change summary
- 新增：`addons/smart_core/controllers/intent_legacy_compat.py`
  - `apply_legacy_load_view_compat(normalized, intent_name)`
- 更新：`addons/smart_core/controllers/intent_dispatcher.py`
  - `_finalize_dispatch_response` 改为调用 adapter
  - 移除内联 legacy data 修补代码块
- 更新：`docs/architecture/backend_core_refactor_blueprint_v1.md`
  - 新增 `B2-4 implement (2026-04-09)`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1562.yaml` ✅
- `python3 -m py_compile addons/smart_core/controllers/intent_dispatcher.py addons/smart_core/controllers/intent_legacy_compat.py` ✅
- adapter wiring grep ✅
- blueprint status grep ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅兼容层逻辑归位，未改变公开 envelope 与权限事实。

## Rollback suggestion
- `git restore addons/smart_core/controllers/intent_dispatcher.py addons/smart_core/controllers/intent_legacy_compat.py docs/architecture/backend_core_refactor_blueprint_v1.md`

## Next suggestion
- 开启下一线：`C-line`（handler/orchestrator/service/builder 职责拆分）先做 screen 批次。
