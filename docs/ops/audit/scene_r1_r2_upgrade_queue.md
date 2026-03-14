# Scene R1-R2 Upgrade Queue

更新时间：2026-03-14 20:39:10

## Summary

- `queue_count`: 6
- `r0_count`: 2
- `r1_count`: 4
- `p0_count`: 4
- `p1_count`: 2
- `p2_count`: 0
- `route_missing_count`: 2

## Queue

| scene_key | name | maturity | target | priority | template | prerequisite |
| --- | --- | --- | --- | --- | --- | --- |
| my_work.workspace | 我的工作 | R1 | R2 | P0 | Workspace | route_ready |
| portal.capability_matrix | 能力矩阵 | R1 | R2 | P0 | Workspace | route_ready |
| projects.dashboard | 项目驾驶舱 | R1 | R2 | P0 | Dashboard | route_ready |
| scene_smoke_default | Scene Smoke Default | R1 | R2 | P0 | Generic | route_ready |
| data.dictionary | 业务字典 | R0 | R1 | P1 | Generic | route_missing |
| projects.dashboard_showcase | 项目驾驶舱（演示） | R0 | R1 | P1 | List | route_missing |

## Execution Rule

- 先处理 `P0` 场景，按模板落地基础 `page/layout/zone_blocks`。
- `R0` 场景先补齐 `route/target` 再进入 `R1→R2`。
- `scene_smoke_default` 仅维持测试最小形态，不纳入业务主线深度产品化。

