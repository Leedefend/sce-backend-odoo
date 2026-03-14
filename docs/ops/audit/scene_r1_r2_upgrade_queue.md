# Scene R1-R2 Upgrade Queue

更新时间：2026-03-14 20:55:12

## Summary

- `queue_count`: 0
- `r0_count`: 0
- `r1_count`: 0
- `p0_count`: 0
- `p1_count`: 0
- `p2_count`: 0
- `route_missing_count`: 0

## Queue

| scene_key | name | maturity | target | priority | template | prerequisite |
| --- | --- | --- | --- | --- | --- | --- |

## Execution Rule

- 先处理 `P0` 场景，按模板落地基础 `page/layout/zone_blocks`。
- `R0` 场景先补齐 `route/target` 再进入 `R1→R2`。
- `scene_smoke_default` 仅维持测试最小形态，不纳入业务主线深度产品化。

