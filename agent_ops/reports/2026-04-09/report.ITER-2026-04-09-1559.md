# ITER-2026-04-09-1559 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `B2-1 dispatcher purity`

## Architecture declaration
- Layer Target: `Controller protocol adapter layer`
- Module: `intent dispatcher`
- Module Ownership: `smart_core controllers`
- Kernel or Scenario: `kernel`
- Reason: 将 Tier-1 的 DB 解析与请求归一逻辑从 dispatcher 主体抽离，降低混合职责。

## Change summary
- 新增：`addons/smart_core/controllers/intent_request_normalizer.py`
  - `normalize_dispatch_payload(body)`
  - `resolve_effective_db(...)`
- 更新：`addons/smart_core/controllers/intent_dispatcher.py`
  - `_prepare_dispatch_request` 改为调用新 helper
  - 移除内联 DB 解析/本地 dev 判定分支
- 更新：`docs/architecture/backend_core_refactor_blueprint_v1.md`
  - 新增 `B2-1 implement (2026-04-09)` 记录

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1559.yaml` ✅
- `python3 -m py_compile addons/smart_core/controllers/intent_dispatcher.py addons/smart_core/controllers/intent_request_normalizer.py` ✅
- helper wiring grep ✅
- blueprint status grep ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：行为保持，主要为内部结构外移；未触及 ACL/财务/manifest。

## Rollback suggestion
- `git restore addons/smart_core/controllers/intent_dispatcher.py addons/smart_core/controllers/intent_request_normalizer.py docs/architecture/backend_core_refactor_blueprint_v1.md`

## Next suggestion
- 进入 `B2-2 implement`：抽离 commit/effect policy，dispatcher 只消费执行结果与 envelope。
