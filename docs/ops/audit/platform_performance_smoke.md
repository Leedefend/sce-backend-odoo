# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 3101.02 | 3209.91 | 1913243 | 200 | 4000.00 | 3000000 |
| ui.contract | 1304.08 | 1330.83 | 740586 | 200 | 3000.00 | 3000000 |
| execute_button | 20.35 | 23.00 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
