# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2474.59 | 3327.50 | 251696 | 200 | 4000.00 | 3000000 |
| ui.contract | 244.37 | 339.44 | 83295 | 200 | 3000.00 | 3000000 |
| execute_button | 28.21 | 30.79 | 574 | 404 | 2500.00 | 500000 |

## Errors

- none
