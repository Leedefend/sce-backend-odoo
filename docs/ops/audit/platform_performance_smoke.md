# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 1134.11 | 1431.35 | 1263613 | 200 | 4000.00 | 3000000 |
| ui.contract | 1255.80 | 1606.81 | 632743 | 200 | 3000.00 | 3000000 |
| execute_button | 40.39 | 51.01 | 718 | 200 | 2500.00 | 500000 |

## Errors

- none
