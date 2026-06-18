# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2312.65 | 2477.61 | 202939 | 200 | 4000.00 | 3000000 |
| ui.contract | 887.90 | 982.04 | 735973 | 200 | 3000.00 | 3000000 |
| execute_button | 20.16 | 21.46 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
