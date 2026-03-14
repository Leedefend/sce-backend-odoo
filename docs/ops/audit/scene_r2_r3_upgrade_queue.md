# Scene R2-R3 Upgrade Queue

更新时间：2026-03-14 21:25:25

## Summary

- `queue_count`: 0
- `p0_count`: 0
- `p1_count`: 0
- `p2_count`: 0

## Queue

| scene_key | name | priority | template | target | upgrade_focus |
| --- | --- | --- | --- | --- | --- |

## Execution Rule

- `P0` 场景优先升级，最小闭环：`role_variants + action_specs + data_sources + product_policy`。
- 升级后必须通过：`scene_role_policy_consistency_guard`、`scene_data_source_schema_guard`、`scene_r3_runtime_guard`。

