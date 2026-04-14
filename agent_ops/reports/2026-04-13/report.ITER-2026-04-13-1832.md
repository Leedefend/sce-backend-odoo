# ITER-2026-04-13-1832 项目状态纯投影实现收口专项

## 任务结论

- 结果：PASS
- 层级：Business Fact Model Implementation
- 模块：smart_construction_core project.project state projection
- 范围：只收口 project.project 状态实现；不导入数据、不扩样、不改前端/菜单/ACL。

## 修改文件

- `agent_ops/tasks/ITER-2026-04-13-1832.yaml`
- `addons/smart_construction_core/models/core/project_core.py`
- `docs/architecture/project_state_projection_closure_v1.md`
- `docs/architecture/project_state_projection_validation_v1.md`
- `docs/migration_alignment/project_state_closure_expand_readiness_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1832.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1832.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## 被收口的 stage 写入路径

| 路径 | 结果 |
| --- | --- |
| standalone `write({"stage_id": ...})` | 收紧为只能写入与当前 lifecycle 投影一致的 stage |
| 同时写 `lifecycle_state` 与 `stage_id` | lifecycle 优先，覆盖传入 stage |
| `_sync_stage_from_signals()` | 降级为 advisory，不写库 |
| `action_sc_stage_sync()` | 调用 advisory，不写库 |
| `init()` 缺 stage 修补 | 改为 lifecycle 投影修补 |

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1832.yaml`：PASS
- `python3 -m py_compile addons/smart_construction_core/models/core/project_core.py`：PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1832.json`：PASS
- `make verify.native.business_fact.static`：PASS
- `DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade`：首次被 fast-mode 升级闸门拦截，未进入 Odoo 升级流程
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade`：PASS
- `make restart`：PASS
- `DB_NAME=sc_demo make odoo.shell.exec` 原生页面/投影/30 条可读性核验：PASS

## 原生页面与 30 条可读性核验

| 项 | 结果 |
| --- | --- |
| 原生 form 视图加载 | PASS |
| Header 主状态字段 | `lifecycle_state` |
| Header `stage_id` 状态栏 | 已替换 |
| 目标 legacy_project_id 数 | 30 |
| 命中项目数 | 30 |
| 缺失/重复 | 0 / 0 |
| lifecycle 投影不一致 | 0 |
| `_sync_stage_from_signals()` 写库 | 否 |
| standalone stage 不一致写入 | 已拦截 |

## 扩样结论

允许进入新的 bounded create-only 扩样准入批次；本轮没有导入数据，也没有扩大样本。
