# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 1983.46 | 2235.34 | 2002905 | 200 | 4000.00 | 3000000 |
| ui.contract | 1187.56 | 1241.87 | 739944 | 200 | 3000.00 | 3000000 |
| execute_button | 18.56 | 19.77 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
