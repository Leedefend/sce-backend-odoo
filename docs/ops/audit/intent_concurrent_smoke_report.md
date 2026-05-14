# Intent Concurrent Smoke Report

- workers: 12
- rounds: 4
- request_count: 12
- error_count: 0
- warning_count: 0

| intent | count | statuses | shape_variants | p95_ms |
|---|---:|---|---:|---:|
| system.init | 4 | 200 | 1 | 3854.26 |
| ui.contract | 4 | 200 | 1 | 6022.19 |
| execute_button | 4 | 200 | 1 | 277.26 |

## Errors

- none

## Warnings

- none
