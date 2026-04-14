# ITER-2026-04-13-1833 项目状态读侧一致性审计与收口专项

## 任务结论

- 结果：PASS
- 层级：Business Fact Read-Side Implementation
- 模块：smart_construction_core project.project state consumers
- 范围：只做项目状态读侧消费收口；不导入数据、不扩样、不改前端/菜单/ACL。

## 修改文件

- `agent_ops/tasks/ITER-2026-04-13-1833.yaml`
- `addons/smart_construction_core/services/project_state_explain_service.py`
- `addons/smart_construction_core/services/project_dashboard_service.py`
- `addons/smart_construction_core/services/project_dashboard_builders/project_header_builder.py`
- `addons/smart_construction_core/services/project_dashboard_builders/base.py`
- `addons/smart_construction_core/services/project_context_contract.py`
- `addons/smart_construction_core/services/insight/project_insight_service.py`
- `addons/smart_construction_core/services/project_execution_service.py`
- `addons/smart_construction_core/services/cost_tracking_service.py`
- `addons/smart_construction_core/services/project_plan_bootstrap_service.py`
- `scripts/verify/project_state_read_side_guard.py`
- `docs/architecture/project_state_read_side_alignment_v1.md`
- `docs/architecture/project_state_consumers_audit_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1833.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1833.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## 收口结果

- 项目级 summary/context/explain/insight 的阶段展示统一改为 `lifecycle_state_label()`。
- `project.stage_id` 不再作为项目业务读侧事实源。
- `project.task.stage_id` 与原生 UI 投影/legacy 字段作为白名单保留。

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1833.yaml`：PASS
- `python3 scripts/verify/project_state_read_side_guard.py`：PASS
- `python3 -m py_compile ...`：PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1833.json`：PASS
- `make verify.native.business_fact.static`：PASS
- `make restart`：PASS
- `DB_NAME=sc_demo make odoo.shell.exec`：首次核验发现断言路径错误，未发现实现错误
- `DB_NAME=sc_demo make odoo.shell.exec` 修正断言后复核：PASS

## 运行态核验

| 项 | 结果 |
| --- | --- |
| form/list/kanban 视图加载 | PASS |
| form header lifecycle statusbar | PASS |
| project payload `stage_name` | lifecycle 派生标签 |
| state explain `stage_label` | lifecycle 派生标签 |
| project context `stage_label` | lifecycle 派生标签 |
| header builder `stage_name` / `current_stage` | lifecycle 派生标签 |
| flow_map | 可生成 |
| next_actions | 可调用 |

## 扩样结论

允许进入 bounded create-only 扩样准入批次；本轮没有导入数据，也没有扩大样本。
