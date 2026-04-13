# ITER-2026-04-10-1622 Report

## Batch
- Batch: `B/4`
- Mode: `implement`
- Stage: `session.bootstrap minimal execution closure`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core v2 session bootstrap execution closure`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 在 1621 注册闭环基础上打通 dispatcher -> schema -> handler -> envelope 最小执行主链。

## Change summary
- 更新：`addons/smart_core/v2/kernel/pipeline.py`
  - 新增 `_apply_request_schema()`
  - dispatcher 在 handler 前执行 schema validate
  - validation/dispatch 异常统一 envelope 返回
- 更新：`addons/smart_core/v2/intents/schemas/session_bootstrap_schema.py`
  - 真实校验 `app_key` 类型
  - 输出 `schema_validated` 标记与规范化 `app_key`
- 更新：`addons/smart_core/v2/handlers/system/session_bootstrap.py`
  - 运行态返回最小执行字段：`intent/session_status/bootstrap_ready`
  - 支持失败路径触发（`raise_handler_error`）
- 新增：`scripts/verify/v2_session_bootstrap_execution_audit.py`
  - 校验主链执行与 schema 参与
- 新增：`scripts/verify/v2_session_bootstrap_failure_path_audit.py`
  - 校验 schema fail / handler fail 失败口径

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1622.yaml` ✅
- `python3 scripts/verify/v2_session_bootstrap_execution_audit.py --json` ✅
- `python3 scripts/verify/v2_session_bootstrap_failure_path_audit.py --json` ✅
- `python3 -m py_compile ...` ✅
- `rg -n "request_schema|validate\(|handler.run|make_envelope|REASON_VALIDATION_FAILED" addons/smart_core/v2/kernel/pipeline.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批聚焦执行闭环，不引入 service/orchestrator 分层与复杂业务。

## Rollback suggestion
- `git restore addons/smart_core/v2/kernel/pipeline.py addons/smart_core/v2/handlers/system/session_bootstrap.py addons/smart_core/v2/intents/schemas/session_bootstrap_schema.py scripts/verify/v2_session_bootstrap_execution_audit.py scripts/verify/v2_session_bootstrap_failure_path_audit.py`

## Next suggestion
- 进入 `1623`（C/4）：把 session.bootstrap 从 handler 内最小逻辑拆到 service/result/builder，完成分层边界闭环。
