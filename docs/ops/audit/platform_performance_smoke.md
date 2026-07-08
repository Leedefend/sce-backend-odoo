# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 3087.43 | 3195.31 | 1913243 | 200 | 4000.00 | 3000000 |
| ui.contract | 1297.09 | 1339.60 | 740586 | 200 | 3000.00 | 3000000 |
| execute_button | 20.59 | 21.79 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
