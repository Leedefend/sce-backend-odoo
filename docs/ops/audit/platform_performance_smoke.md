# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 5751.37 | 8499.82 | 639582 | 200 | 30000.00 | 3000000 |
| ui.contract | 654.36 | 772.34 | 345888 | 200 | 3000.00 | 3000000 |
| execute_button | 56.19 | 64.50 | 462 | 200 | 2500.00 | 500000 |

## Errors

- none
