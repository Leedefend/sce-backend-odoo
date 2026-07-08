# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 3136.21 | 3257.48 | 1913244 | 200 | 4000.00 | 3000000 |
| ui.contract | 1307.87 | 1339.18 | 740586 | 200 | 3000.00 | 3000000 |
| execute_button | 20.49 | 22.36 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
