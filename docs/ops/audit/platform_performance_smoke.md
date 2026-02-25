# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 1590.54 | 2133.08 | 251696 | 200 | 4000.00 | 3000000 |
| ui.contract | 210.33 | 270.22 | 83295 | 200 | 3000.00 | 3000000 |
| execute_button | 24.14 | 24.74 | 574 | 404 | 2500.00 | 500000 |

## Errors

- none
