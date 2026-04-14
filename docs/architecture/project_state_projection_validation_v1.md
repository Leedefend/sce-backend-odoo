# 项目状态纯投影验证记录 v1

状态：Validation Record  
批次：ITER-2026-04-13-1832

## 1. 验证目标

验证本轮实现满足：

- `lifecycle_state -> stage_id` 单向投影保留；
- standalone `stage_id` 不再作为独立业务状态入口；
- signal-based stage sync 不再写库；
- 原生页面主状态展示以 `lifecycle_state` 为主；
- 已写入 30 条项目骨架仍可读。

## 2. 静态验证

| 项 | 结论 |
| --- | --- |
| `python3 -m py_compile addons/smart_construction_core/models/core/project_core.py` | PASS |
| `sc_stage_sync` 上下文绕过 | 已移除 |
| `_sync_stage_from_signals` 写库 | 已移除，改为 advisory |
| standalone `stage_id` 分支 | 已收紧为 lifecycle 投影一致性校验 |
| `write(lifecycle_state + stage_id)` | 已收紧为 lifecycle 优先覆盖 stage |

## 3. 原生页面复核

| 项 | 结论 |
| --- | --- |
| Header 主状态字段 | `lifecycle_state` |
| Header `stage_id` 状态栏 | 已被替换 |
| 是否改前端/菜单/ACL | 否 |

## 4. 运行态验证

| 命令 | 状态 |
| --- | --- |
| `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1832.yaml` | 待执行 |
| `python3 -m py_compile addons/smart_construction_core/models/core/project_core.py` | PASS |
| `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1832.json` | PASS |
| `make verify.native.business_fact.static` | PASS |
| `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade` | PASS |
| `make restart` | PASS |
| `DB_NAME=sc_demo make odoo.shell.exec` 原生页面/投影/30 条可读性核验 | PASS |

## 5. 运行态核验结果

| 项 | 结果 |
| --- | --- |
| 目标 legacy_project_id 数 | 30 |
| 命中项目数 | 30 |
| 缺失 | 0 |
| 重复 | 0 |
| lifecycle 投影不一致 | 0 |
| 原生字段 `lifecycle_state` / `stage_id` / `short_name` | 存在 |
| 原生 form 视图加载 | PASS |
| Header lifecycle statusbar | PASS |
| Header `stage_id` 状态栏替换 | PASS |
| `_sync_stage_from_signals()` 是否写库 | 否，stage 保持不变 |
| standalone `stage_id` 不一致写入 | 已被 `P0_PROJECT_STAGE_PROJECTION_ONLY` 拦截 |

## 6. 验证结论

本轮实现收口验证通过。可进入新的 bounded create-only 扩样准入批次，但本轮未执行扩样。
