# 项目状态读侧一致性收口 v1

状态：Implementation Closure  
批次：ITER-2026-04-13-1833  
依据：ITER-2026-04-13-1832 状态纯投影实现收口

## 1. 收口规则

项目状态读侧冻结为：

```text
业务判断字段：project.project.lifecycle_state
展示/兼容投影：project.project.stage_id
非项目任务阶段：project.task.stage_id
```

读侧不得通过 `project.stage_id` 推断项目业务状态。

## 2. 本轮收口内容

| 文件 | 收口内容 |
| --- | --- |
| `project_state_explain_service.py` | 新增 `lifecycle_state_label()`，状态说明标签由 lifecycle 派生 |
| `project_dashboard_service.py` | 项目 summary 的 `stage_name` 改为 lifecycle 派生标签 |
| `project_dashboard_builders/project_header_builder.py` | header summary 的 `stage_name` / `current_stage` 改为 lifecycle 派生标签 |
| `project_dashboard_builders/base.py` | block project context 的 `stage_label` 改为 lifecycle 派生标签 |
| `project_context_contract.py` | scene project context 的 `stage_label` 改为 lifecycle 派生标签 |
| `project_execution_service.py` | 执行页项目 summary 的 `stage_name` 改为 lifecycle 派生标签 |
| `cost_tracking_service.py` | 成本页项目 summary 的 `stage_name` 改为 lifecycle 派生标签 |
| `project_plan_bootstrap_service.py` | 计划页项目 summary 的 `stage_name` 改为 lifecycle 派生标签 |
| `insight/project_insight_service.py` | insight 的项目阶段获取改为 lifecycle 派生标签 |

## 3. 保留白名单

| 类型 | 规则 |
| --- | --- |
| `project_core.py` | 允许 `stage_id` 用于 lifecycle 投影写入、缺失修补和 signal advisory 诊断 |
| `project_views.xml` | 允许用 xpath 替换原生 header `stage_id`；允许显示 `legacy_stage_id` / `legacy_stage_name` |
| `project.task.stage_id` | 属于任务阶段，不是 `project.project` 主状态 |
| 原生 UI group/search 兼容 | 可保留 `stage_id` 作为 Odoo 投影字段，但不得作为业务真相判断 |

## 4. 已固化验证

新增 `scripts/verify/project_state_read_side_guard.py`：

- 禁止项目读侧 service 直接读取 `project.stage_id`；
- 要求项目 summary/context/explain 使用 `lifecycle_state_label()`；
- 输出 `artifacts/backend/project_state_read_side_guard.json` 与 `.md`。

## 5. 扩样准入影响

本轮完成后，状态读侧不再阻断下一张 bounded create-only 扩样准入任务。

