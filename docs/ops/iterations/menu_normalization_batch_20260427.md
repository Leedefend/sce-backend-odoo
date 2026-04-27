# Menu Normalization Batch 20260427

## 1. 本轮变更
- 目标：补齐 `nav_explained` 菜单解释结果中的权威判别字段。
- 完成：
  - `MenuTargetInterpreterService` 新增加性字段：`scene_key`、`native_action_id`、`native_model`、`native_view_mode`、`confidence`、`compatibility_used`。
  - 保持既有 `target_type`、`delivery_mode`、`route`、`target`、`entry_target` 输出不变。
  - 单测覆盖 scene、native bridge、scene-known act_window、compat custom action 四类输出。
- 未完成：未执行 live `/api/menu/navigation` 快照导出，本批只做解释器纯后端契约小切片。

## 2. 影响范围
- 模块：`addons/smart_core/delivery`、`addons/smart_core/tests`
- 启动链：否
- contract/schema：是，加性字段；不改 public intent / route / contract_version
- default_route：否
- 前端：否

## 3. 风险
- P0：无，未改启动链、public route、数据库结构。
- P1：前端若未来开始强类型消费 `nav_explained`，需同步 schema 类型。
- P2：`confidence` 目前是解释器本地分层值，后续若引入策略/权限评分需要单独批次扩展。

## 4. 验证
- `python3 -m py_compile addons/smart_core/delivery/menu_target_interpreter_service.py addons/smart_core/tests/test_menu_target_interpreter_entry_target.py`：PASS
- `python3 addons/smart_core/tests/test_menu_target_interpreter_entry_target.py`：PASS，6 tests
- `git diff --check -- addons/smart_core/delivery/menu_target_interpreter_service.py addons/smart_core/tests/test_menu_target_interpreter_entry_target.py`：PASS
- `make verify.smart_core`：PASS，outdir=`/tmp/smart_core_verify`
- `make verify.contract.snapshot`：PASS，更新 `docs/contract/exports/intent_catalog.json` 测试引用计数
- `make verify.restricted`：FAIL，仓库无该 target；以 `verify.smart_core` 作为本批实际可用后端门禁。
- `make verify.backend.guard`：FAIL，仓库无该 target；以路径级 diff check 与 `verify.smart_core` 覆盖本批后端小切片。

## 5. 产物
- logs：`/tmp/smart_core_verify`
- snapshot：`docs/contract/exports/intent_catalog.json`
- e2e：N/A，未涉及前端

## 6. 回滚
- 方法：回退本批对 `addons/smart_core/delivery/menu_target_interpreter_service.py` 与 `addons/smart_core/tests/test_menu_target_interpreter_entry_target.py` 的改动。
- 数据/升级：无需 `-u`，无需数据回滚。

## 7. 下一批次
- 目标：对 `/api/menu/navigation` live 输出做 snapshot/smoke，确认新增字段在真实 `nav_explained.flat/tree` 中稳定出现。
- 前置条件：确认执行环境 DB 与登录账号，避免把 live 环境问题混入解释器契约判断。
