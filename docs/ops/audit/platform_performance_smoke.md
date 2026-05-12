# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 550.24 | 655.55 | 505134 | 200 | 4000.00 | 3000000 |
| ui.contract | 961.56 | 1068.33 | 679452 | 200 | 3000.00 | 3000000 |
| execute_button | 17.60 | 18.76 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
