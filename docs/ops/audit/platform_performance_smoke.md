# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2281.00 | 2397.80 | 202939 | 200 | 4000.00 | 3000000 |
| ui.contract | 882.83 | 977.73 | 735973 | 200 | 3000.00 | 3000000 |
| execute_button | 19.25 | 21.42 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
