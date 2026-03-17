# Scene Coverage Matrix v1

## 成熟度定义

- `R0`：Registry-only
- `R1`：Seeded
- `R2`：Profiled
- `R3`：Productized

## 场景矩阵（当前）

| scene_key | maturity | note |
| --- | --- | --- |
| projects.list | R3 | 本轮样板：scene-ready 列表消费路径已接入 |
| projects.intake | R3 | 本轮样板：scene-ready 表单校验消费已接入 |
| project.management | R2 | 已有 profile，待完整 provider 产品化 |
| contracts.workspace | R2 | 已有场景定义，待动作/权限编排细化 |
| finance.workspace | R2 | 已有场景定义，待数据 provider 产品化 |
| workspace.home | R3 | 已有专用 provider 与页面编排 |
| portal.dashboard | R2 | profile 可用，待统一 scene-ready 消费 |
| my_work.workspace | R2 | 已接入场景路由，待表层编排加强 |

## 规则

- 所有新增场景必须先标注成熟度后开发。
- Wave 主线目标：`projects.list`、`projects.intake` 维持 `R3`。

