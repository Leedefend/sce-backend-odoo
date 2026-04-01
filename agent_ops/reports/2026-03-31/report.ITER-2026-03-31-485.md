# ITER-2026-03-31-485

## Summary
- 修复了 [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py) 对 `read_group` 计数字段的读取逻辑
- 结论为 `PASS`
- `overview.cost.count` 已与真实 `project.cost.ledger` 行数重新对齐，`维护成本台账` recommendation 误报一并消失

## Scope
- 本批为窄实现批次
- 仅变更：
  - [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py)
  - [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)
- 仅验证：
  - overview 聚合 `read_group` count 读取
  - `project.id = 20` 的 runtime `cost.count`
  - recommendation 输出是否恢复

## Implementation
- 在 [project_overview_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_overview_service.py) 增加 `_group_count(row, groupby)`：
  - 优先兼容 `__count`
  - 如果不存在，则回退读取 `project_id_count`
- 将 contract / cost / payment / pending payment / task / in-progress task 聚合分支统一切到 `_group_count(...)`
- 在 [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py) 增加回归：
  - 新建一条 `project.cost.ledger`
  - 断言 `get_overview([project.id])[project.id]['cost']['count'] == 1`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-485.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `sc_odoo` runtime audit → `PASS`
  - `project.id = 20`
  - `PM / hujun`:
    - `overview_cost_count = 4`
    - `direct_cost_search_count = 4`
    - `actions = []`
  - `executive / wutao`:
    - `overview_cost_count = 4`
    - `direct_cost_search_count = 4`
    - `actions = []`
  - `business_admin / admin`:
    - `overview_cost_count = 4`
    - `direct_cost_search_count = 4`
    - `actions = []`

## Conclusion
- `484` 识别出的 recommendation correctness 残差已经关闭
- 根因确实是 overview 聚合层错误读取 `read_group` count key
- 修复后，overview 事实与 runtime 数据一致，误报 recommendation 不再出现

## Risk
- 结果：`PASS`
- 剩余风险：
  - 本批已把同一服务里的同类 count 读取一并切到兼容逻辑，但更广范围的 recommendation correctness 仍需继续抽样审计
  - 当前 runtime 样本集中 `project.id = 20` 恢复正常，不代表所有 stage / role / recommendation 组合都已完全验收

## Rollback
- 如需回滚本批实现：
  - `git restore addons/smart_construction_core/services/project_overview_service.py`
  - `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- 如需回滚治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-485.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-485.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-485.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续下一张低风险审计批次，扩大 recommendation correctness 抽样，确认 `overview -> next_action` 管线在其他 stage / role / counter 组合上没有新的统计口径残差
