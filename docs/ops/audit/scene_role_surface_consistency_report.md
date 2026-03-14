# Scene Role Surface Consistency Report

更新时间：2026-03-14 20:05:12

## Summary

- `role_count`: 4
- `r3_scene_count`: 13
- `errors`: 0
- `warnings`: 3

## Role Overrides

| role_code | candidates | candidate_missing | menu_overlap | r3_scene_hits | status |
| --- | ---: | ---: | ---: | ---: | --- |
| executive | 5 | 1 | 0 | 8 | PASS |
| finance | 3 | 0 | 0 | 9 | PASS |
| owner | 2 | 0 | 0 | 0 | PASS |
| pm | 4 | 1 | 0 | 9 | PASS |

## R3 Scene Role Variants

| scene_key | role_variant_count | unknown_roles | status |
| --- | ---: | --- | --- |
| contract.center | 2 |  | PASS |
| contracts.workspace | 2 |  | PASS |
| cost.analysis | 2 |  | PASS |
| cost.cost_compare | 2 |  | PASS |
| cost.project_cost_ledger | 2 |  | PASS |
| finance.center | 2 |  | PASS |
| finance.payment_requests | 2 |  | PASS |
| finance.settlement_orders | 2 |  | PASS |
| finance.workspace | 2 |  | PASS |
| project.management | 2 |  | PASS |
| projects.intake | 2 |  | PASS |
| projects.ledger | 2 |  | PASS |
| projects.list | 2 |  | PASS |

## Warnings

- role_surface_overrides.executive: landing_scene_candidate outside inventory (portal.dashboard)
- role_surface_overrides.owner: no R3 scene role_variants coverage
- role_surface_overrides.pm: landing_scene_candidate outside inventory (portal.dashboard)

