# ITER-2026-04-10-1584 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `v2 validator/policy + readonly intent`

## Architecture declaration
- Layer Target: `Platform kernel shadow refactor layer`
- Module: `smart_core v2 validator/policy/read-only intent`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 在 v2 影子重构中补齐职责层并行能力，持续摆脱旧模块职责耦合。

## Change summary
- 新增：`addons/smart_core/v2/validators/base.py`
  - `BaseIntentValidatorV2` / `DefaultIntentValidatorV2`
- 新增：`addons/smart_core/v2/policies/permission_policy.py`
  - `PermissionPolicyV2`
- 更新：`addons/smart_core/v2/dispatcher.py`
  - 接入 validator + permission policy
  - 注入 `registry_snapshot` 到 handler context
- 新增：`addons/smart_core/v2/handlers/system/registry_list.py`
  - 只读意图 `system.registry.list`
- 更新：`addons/smart_core/v2/intents/registry.py`
  - 注册 `system.registry.list`（authenticated）
- 更新：`addons/smart_core/v2/services/system_service.py`
  - 增加 `list_registered_intents`
- 更新：`addons/smart_core/v2/builders/system_builder.py`
  - 增加 `build_registry_list_contract`
- 更新：`docs/architecture/backend_core_refactor_blueprint_v1.md`
  - 新增 `v2 validator-policy-readonly intent batch (2026-04-10)`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1584.yaml` ✅
- `python3 -m py_compile ...v2...` ✅
- validator/policy/intent/service symbol grep ✅
- blueprint 锚点 grep ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅在 v2 影子层新增职责模板与只读意图，未切换旧链路。

## Rollback suggestion
- `git restore addons/smart_core/v2 docs/architecture/backend_core_refactor_blueprint_v1.md`

## Next suggestion
- 下一批将 v2 加入 parser/builder 约束模板，并迁移首个真实 `meta` 只读意图做对照输出。
