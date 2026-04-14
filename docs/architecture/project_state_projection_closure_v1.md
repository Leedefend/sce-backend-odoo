# 项目状态纯投影实现收口 v1

状态：Implementation Closure  
批次：ITER-2026-04-13-1832  
依据：ITER-2026-04-13-1829 / 1830 / 1831

## 1. 收口目标

将 `project.project` 状态实现收口为：

```text
lifecycle_state = business truth
stage_id = Odoo UI projection
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
business signals -/-> stage_id
```

本轮不新增字段、不新增生命周期枚举、不导入数据、不扩大样本。

## 2. 已收口路径

| 路径 | 原行为 | 收口后行为 |
| --- | --- | --- |
| `write({"stage_id": ...})` 且未写 `lifecycle_state` | 可在防越级范围内独立写入 stage | 仅允许写入与当前 `lifecycle_state` 投影一致的 stage；不一致则触发 `P0_PROJECT_STAGE_PROJECTION_ONLY` |
| `write({"lifecycle_state": ..., "stage_id": ...})` | 若同时传入 stage，可能尊重传入值 | `lifecycle_state` 优先，覆盖为生命周期映射 stage |
| `_sync_stage_from_signals()` | 根据 BOQ/task/material/settlement/payment 信号推进 `stage_id` | 降级为只读 advisory，返回/记录信号建议，不写库 |
| `action_sc_stage_sync()` | 调用 signal sync 并可能推进 stage | 调用 advisory，不写库 |
| `init()` 老项目缺 stage 修补 | 写默认 stage | 改为按 `lifecycle_state` 投影修补 stage |

## 3. 保留路径

| 路径 | 保留原因 |
| --- | --- |
| `_get_stage_for_lifecycle()` | lifecycle 到 stage 的映射函数 |
| `_sync_stage_from_lifecycle()` | 唯一的 stage 投影修补路径 |
| `create()` lifecycle 默认与 stage 映射 | 新建记录必须具备生命周期投影 stage |
| `write({"lifecycle_state": ...})` | 生命周期变更后同步投影 stage |
| `project.stage` 数据 | Odoo 原生 UI stage 承载字典 |

## 4. `_sync_stage_from_signals` 处理结论

处理方式：降级为 advisory。

该方法仍可计算信号建议并输出以下信息：

- `project_id`
- `project_name`
- `lifecycle_state`
- `current_stage_id`
- `current_stage_key`
- `lifecycle_stage_id`
- `signal_stage_id`
- `signal_stage_key`
- `would_diverge_from_lifecycle`

但它不再执行任何 `stage_id` 写入，也不再通过上下文绕过 standalone stage 写入收口。

## 5. 原生页面状态展示复核

`addons/smart_construction_core/views/core/project_views.xml` 中原生项目表单 header 已将 `stage_id` 状态栏替换为 `lifecycle_state` 状态栏。

本轮未修改视图文件，复核结论：

- 页面主状态展示字段：`lifecycle_state`
- `stage_id` 不作为 header 主状态展示
- 施工信息页存在 `lifecycle_state` 字段展示，用于业务事实可见性

## 6. 剩余边界

- `_sc_compute_stage_key()` 仍保留为 advisory 计算依赖，不再是 stage 写入依据；
- 后续如要彻底删除 signal advisory，需要另开清理批次；
- bounded create-only 扩样仍需通过本轮验证与扩样准入文档确认。

