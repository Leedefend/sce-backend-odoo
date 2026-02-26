# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2060.69 | 2198.22 | 251993 | 200 | 4000.00 | 3000000 |
| ui.contract | 231.86 | 296.24 | 128380 | 200 | 3000.00 | 3000000 |
| execute_button | 26.42 | 28.42 | 574 | 404 | 2500.00 | 500000 |

## Errors

- none
