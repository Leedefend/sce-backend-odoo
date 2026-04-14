# 项目状态实现收口前置清单 v1

状态：Implementation Gate  
批次：ITER-2026-04-13-1831

## 1. 进入实现收口批次的目标

将当前过渡态：

```text
stage_id = UI stage + business signal projection
```

收口为目标态：

```text
stage_id = lifecycle_state 的 UI projection
```

## 2. 需要处理的代码点

以下为下一轮实现批次的候选触点。本轮不修改代码。

| 文件 | 代码点 | 收口方向 |
| --- | --- | --- |
| `addons/smart_construction_core/models/core/project_core.py` | `create()` lifecycle 默认与 stage 映射 | 保留；确保只由 lifecycle 决定 stage |
| `addons/smart_construction_core/models/core/project_core.py` | `write()` 中 `lifecycle_state` 写入逻辑 | 保留；生命周期变更后同步投影 stage |
| `addons/smart_construction_core/models/core/project_core.py` | `write()` 中 `"stage_id" in vals and "lifecycle_state" not in vals` 分支 | 收紧；禁止作为独立业务状态入口 |
| `addons/smart_construction_core/models/core/project_core.py` | `_sync_stage_from_lifecycle` | 保留；作为唯一 stage 投影同步路径 |
| `addons/smart_construction_core/models/core/project_core.py` | `_get_stage_for_lifecycle` | 保留；作为 lifecycle 到 stage 的映射函数 |
| `addons/smart_construction_core/models/core/project_core.py` | `_sync_stage_from_signals` | 移除、禁用或重作用为 advisory；不得独立写 `stage_id` |
| `addons/smart_construction_core/models/core/project_core.py` | `_sc_compute_stage_key` | 若仅服务 signal stage 推进，应移除或改造；不得作为 stage 真相来源 |
| `addons/smart_construction_core/models/core/project_core.py` | `action_sc_stage_sync` | 收紧；不得触发 signal-based `stage_id` 推进 |
| `addons/smart_construction_core/views/core/project_views.xml` | lifecycle statusbar | 保留；用户主状态展示以 lifecycle 为准 |
| `addons/smart_construction_core/data/project_stage_data.xml` | project.stage seed | 保留；作为 UI 投影字典 |

## 3. 应禁止的逻辑

实现收口批次必须禁止：

- `stage_id -> lifecycle_state` 反向同步；
- standalone `stage_id` write 被当作项目业务状态变更；
- `_sync_stage_from_signals` 根据 BOQ/task/material/settlement/payment 等业务信号直接写 `stage_id`；
- 导入器独立写 `stage_id`；
- 用 stage 作为项目真实状态判断条件；
- 在没有 lifecycle transition 的情况下推进 UI stage。

## 4. 可保留的逻辑

实现收口批次应保留：

- `lifecycle_state` 作为业务真相；
- `lifecycle_state -> stage_id` 单向投影；
- lifecycle 状态迁移校验；
- `project.stage` 原生数据记录作为 Odoo UI 投影承载；
- legacy 原始状态字段作为迁移审计字段；
- 已写入 30 条试导数据的 rollback dry-run 能力。

## 5. 完成后验证要求

实现收口完成后至少执行：

| 验证 | 期望 |
| --- | --- |
| 静态扫描 `stage_id` 写入口 | 只剩 lifecycle 投影相关写入；无 signal 独立推进 |
| `write({'lifecycle_state': ...})` 验证 | stage 随 lifecycle 正确映射 |
| `write({'stage_id': ...})` 验证 | 不改变 `lifecycle_state`；不得作为业务状态入口 |
| signal sync 验证 | BOQ/task/material/settlement/payment 信号不再独立推进 `stage_id` |
| 导入 dry-run 验证 | 导入模板不包含独立 `stage_id` 写入 |
| 门禁 | `make verify.native.business_fact.static` PASS |

如实现批次触及 Odoo 模型逻辑，还应按当批任务契约补充模块升级/字段物化或 shell 验证。

## 6. 完成后是否允许恢复扩样

仅当以下条件全部满足，才允许重新进入 bounded create-only 扩样门禁：

- standalone `stage_id` write 已收紧；
- `_sync_stage_from_signals` 不再独立写 `stage_id`；
- lifecycle -> stage 投影验证通过；
- stage -> lifecycle 反写仍不存在；
- `make verify.native.business_fact.static` 通过；
- 本轮 30 条试导数据仍可按 `legacy_project_id` 精确锁定。

满足以上条件后，扩样不是自动开始，而是进入新的 bounded create-only 扩样准入批次。
