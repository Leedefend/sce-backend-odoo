# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2288.26 | 2489.15 | 202939 | 200 | 4000.00 | 3000000 |
| ui.contract | 872.82 | 1004.13 | 735973 | 200 | 3000.00 | 3000000 |
| execute_button | 24.64 | 56.07 | 718 | 200 | 2500.00 | 500000 |

## Errors

- none
