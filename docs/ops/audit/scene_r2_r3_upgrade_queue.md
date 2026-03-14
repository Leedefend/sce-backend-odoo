# Scene R2-R3 Upgrade Queue

更新时间：2026-03-14 21:02:58

## Summary

- `queue_count`: 6
- `p0_count`: 3
- `p1_count`: 1
- `p2_count`: 2

## Queue

| scene_key | name | priority | template | target | upgrade_focus |
| --- | --- | --- | --- | --- | --- |
| my_work.workspace | 我的工作 | P0 | Workspace | R3 | role_variants + action_specs + data_sources + product_policy |
| portal.capability_matrix | 能力矩阵 | P0 | Generic | R3 | role_variants + action_specs + data_sources + product_policy |
| projects.dashboard | 项目驾驶舱 | P0 | Dashboard | R3 | role_variants + action_specs + data_sources + product_policy |
| projects.dashboard_showcase | 项目驾驶舱（演示） | P1 | List | R3 | role_variants + action_specs + data_sources + product_policy |
| data.dictionary | 业务字典 | P2 | List | R3 | role_variants + action_specs + data_sources + product_policy |
| risk.center | 风险提醒工作台 | P2 | List | R3 | role_variants + action_specs + data_sources + product_policy |

## Execution Rule

- `P0` 场景优先升级，最小闭环：`role_variants + action_specs + data_sources + product_policy`。
- 升级后必须通过：`scene_role_policy_consistency_guard`、`scene_data_source_schema_guard`、`scene_r3_runtime_guard`。

