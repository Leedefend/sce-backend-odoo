# Intent Concurrent Smoke Report

- workers: 12
- rounds: 4
- request_count: 12
- error_count: 0
- warning_count: 1

| intent | count | statuses | shape_variants | p95_ms |
|---|---:|---|---:|---:|
| system.init | 4 | 200 | 1 | 15071.64 |
| ui.contract | 4 | 200 | 1 | 6757.30 |
| execute_button | 4 | 404 | 1 | 861.92 |

## Errors

- none

## Warnings

- execute_button has non-ok responses (non-5xx)
