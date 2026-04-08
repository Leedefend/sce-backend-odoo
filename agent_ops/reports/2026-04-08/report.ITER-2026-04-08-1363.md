# ITER-2026-04-08-1363 Report

## Batch
- Batch: `1/1`

## Summary of change
- Root-cause定位到后端 `action_open` 语义传递链：`ActionResolver.as_action_info()` 未保留 `domain/context`，导致自定义消费面与原生 action 可能发生过滤语义漂移。
- 已实施后端语义修复（不做前端特判）：
  - `addons/smart_core/app_config_engine/services/resolvers/action_resolver.py`
    - `as_action_info()` 对 dict/record 都补齐 `domain/context`
    - `materialize_server_action()` 结果补齐 `domain/context`
- 已新增回归测试：
  - `addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
    - `test_action_resolver_action_info_keeps_domain_and_context`

## Verification result
- PASS
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1363.yaml`
  - `python3 -m py_compile addons/smart_core/app_config_engine/services/resolvers/action_resolver.py addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
- FAIL
  - `python3 -m unittest addons.smart_core.tests.test_action_dispatcher_server_mapping`
  - 失败原因：当前执行环境缺少 `odoo` Python 包（`ModuleNotFoundError: No module named 'odoo'`）

## Risk analysis
- 结论：`FAIL`（触发 stop condition: `acceptance_command_failed`）
- 风险级别：low（代码改动局限于 action contract 语义装配与测试）
- 当前阻塞：本地 unittest 执行环境不具备 Odoo 运行时依赖，无法在此上下文完成最终门禁闭环。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/resolvers/action_resolver.py`
- `git restore addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1363.yaml`

## Next suggestion
- 在具备 Odoo 运行时的验证环境中执行：
  - `python3 -m unittest addons.smart_core.tests.test_action_dispatcher_server_mapping`
- 若通过，再进行前端 `/a/<action_id>` 与原生 `/web#action=<id>` 的同口径数据对比回归。
