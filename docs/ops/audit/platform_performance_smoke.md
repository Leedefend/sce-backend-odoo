# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 1637.86 | 1750.52 | 589784 | 200 | 4000.00 | 3000000 |
| ui.contract | 989.19 | 1026.26 | 1108374 | 200 | 3000.00 | 3000000 |
| execute_button | 16.87 | 18.50 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
