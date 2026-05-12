# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 521.97 | 583.60 | 505134 | 200 | 4000.00 | 3000000 |
| ui.contract | 908.92 | 1005.25 | 679451 | 200 | 3000.00 | 3000000 |
| execute_button | 17.85 | 19.43 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
