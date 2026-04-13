# ITER-2026-04-10-1642 Report

## Batch
- Batch: `A/4`
- Mode: `implement`
- Stage: `api.onchange registry closure`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core v2 api onchange registry closure`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 按四批节奏启动 api.onchange 主链，先完成注册层闭环。

## Change summary
- 更新：`addons/smart_core/v2/intents/registry.py`
  - 新增 `api.onchange` 注册元数据（canonical_intent/intent_class/tags/request_schema）
- 新增：`addons/smart_core/v2/intents/schemas/api_onchange_schema.py`
  - 最小请求 schema 校验占位
- 更新：`addons/smart_core/v2/intents/schemas/__init__.py`
  - 导出 `ApiOnchangeRequestSchemaV2`
- 更新：`addons/smart_core/v2/handlers/api/__init__.py`
  - 导出 `ApiOnchangeHandlerV2`
- 新增：`addons/smart_core/v2/handlers/api/onchange.py`
  - 最小 handler 占位，返回 registry_closure 标记
- 新增：`scripts/verify/v2_api_onchange_registry_audit.py`
  - 专项审计 `api.onchange` 注册闭环与迁移对比接入

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1642.yaml` ✅
- `python3 scripts/verify/v2_api_onchange_registry_audit.py --json` ✅
- `python3 scripts/verify/v2_intent_comparison_audit.py --json` ✅
- `python3 -m py_compile addons/smart_core/v2/intents/registry.py addons/smart_core/v2/intents/schemas/api_onchange_schema.py addons/smart_core/v2/handlers/api/onchange.py scripts/verify/v2_api_onchange_registry_audit.py` ✅
- `rg -n "intent_name=\"api.onchange\"|canonical_intent=\"api.onchange\"|intent_class=\"api\"|tags=\(" addons/smart_core/v2/intents/registry.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批只完成注册与寻址闭环，不进入 onchange 执行语义。

## Rollback suggestion
- `git restore addons/smart_core/v2/intents/registry.py addons/smart_core/v2/intents/schemas/api_onchange_schema.py addons/smart_core/v2/intents/schemas/__init__.py addons/smart_core/v2/handlers/api/__init__.py addons/smart_core/v2/handlers/api/onchange.py scripts/verify/v2_api_onchange_registry_audit.py`

## Next suggestion
- 进入 `1643`（B/4）：打通 `api.onchange` 的 dispatcher->schema->handler->envelope 最小执行闭环。
