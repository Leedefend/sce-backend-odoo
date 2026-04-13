# ITER-2026-04-09-1564 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `C1-1 intent_router env/cursor policy extraction`

## Architecture declaration
- Layer Target: `Core dispatch orchestration layer`
- Module: `intent_router`
- Module Ownership: `smart_core core`
- Kernel or Scenario: `kernel`
- Reason: 将 env 构建与 cursor 生命周期管理逻辑外移，提升 router 纯分发可维护性。

## Change summary
- 新增：`addons/smart_core/core/intent_env_policy.py`
  - `build_dispatch_envs(params, add_ctx)`
  - `finalize_dispatch_cursor(extra_cursor, dispatch_succeeded, intent, dbname)`
- 更新：`addons/smart_core/core/intent_router.py`
  - `_dispatch` 改为调用 `build_dispatch_envs`
  - `finally` 改为调用 `finalize_dispatch_cursor`
  - 移除内联 `_build_envs` 实现
- 更新：`docs/architecture/backend_core_refactor_blueprint_v1.md`
  - 新增 `C1-1 implement (2026-04-09)`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1564.yaml` ✅
- `python3 -m py_compile addons/smart_core/core/intent_router.py addons/smart_core/core/intent_env_policy.py` ✅
- helper wiring grep ✅
- blueprint status grep ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅做内部结构外移，未改公开 intent 接口形态。

## Rollback suggestion
- `git restore addons/smart_core/core/intent_router.py addons/smart_core/core/intent_env_policy.py docs/architecture/backend_core_refactor_blueprint_v1.md`

## Next suggestion
- 进入 `C1-2 implement`：system_init 内部 data fetch helper 化（先提取，再替换调用）。
