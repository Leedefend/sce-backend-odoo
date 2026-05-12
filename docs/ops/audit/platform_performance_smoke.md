# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 714.88 | 818.98 | 1263609 | 200 | 4000.00 | 3000000 |
| ui.contract | 644.38 | 731.26 | 632742 | 200 | 3000.00 | 3000000 |
| execute_button | 23.88 | 29.10 | 718 | 200 | 2500.00 | 500000 |

## Errors

- none
