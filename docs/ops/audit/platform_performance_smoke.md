# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 1530.82 | 1816.36 | 246062 | 200 | 4000.00 | 3000000 |
| ui.contract | 182.18 | 248.46 | 81935 | 200 | 3000.00 | 3000000 |
| execute_button | 25.17 | 28.89 | 574 | 404 | 2500.00 | 500000 |

## Errors

- none
