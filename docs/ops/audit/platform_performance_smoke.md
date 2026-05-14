# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 914.99 | 976.55 | 625172 | 200 | 4000.00 | 3000000 |
| ui.contract | 1026.07 | 2078.48 | 681335 | 200 | 3000.00 | 3000000 |
| execute_button | 16.60 | 22.06 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
