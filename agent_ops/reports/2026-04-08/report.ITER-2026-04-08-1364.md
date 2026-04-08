# ITER-2026-04-08-1364 Report

## Batch
- Batch: `1/1`

## Summary of change
- 用户问题复现结论：同一 `action_id=542` 下，原生页按 `type=system_param` 过滤显示 3 条；自定义页未携带该过滤语义，出现 17 条混入并导致多列 `--`。
- 后端语义修复（无前端特判）：
  - `addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py`
    - `act_window` 分发时，把动作 `domain/context` 规范化注入页面装配入参 `p`。
  - `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
    - `head` 显式输出有效 `domain/context`（优先 `p`，回退 action），确保消费者链路可读同口径语义。
  - `addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
    - 增加分发透传与 `ui.contract(action_open)` 的 domain 断言回归。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1364.yaml` ✅
- `python3 -m py_compile addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_core/tests/test_action_dispatcher_server_mapping.py` ✅
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_core make mod.upgrade MODULE=smart_core ENV=test DB_NAME=sc_test` ✅
- `make restart ENV=test DB_NAME=sc_test` ✅
- 运行态同口径校验（`localhost:8071`）：✅
  - `ui.contract(action_open, action_id=542)` 返回 `head.domain=[['type','=','system_param']]`
  - 基于该 domain 调 `api.data(list, model=sc.dictionary)` 返回 `3` 条且 `type` 全为 `system_param`

## Risk analysis
- 结论：`PASS`
- 风险级别：low（仅 contract orchestration 语义传递修复；未触达 ACL/财务语义）

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py`
- `git restore addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- `git restore addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1364.yaml`

## Next suggestion
- 在前端 `http://127.0.0.1:5174/a/542?menu_id=352&action_id=542` 手动刷新确认：列表应与原生 `web#action=542` 同为 3 条系统参数。
