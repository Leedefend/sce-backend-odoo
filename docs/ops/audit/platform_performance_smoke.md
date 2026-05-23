# Platform Performance Smoke

- target_count: 3
- iterations: 8
- error_count: 0
- warning_count: 0

| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |
|---|---:|---:|---:|---|---:|---:|
| system.init | 2628.07 | 2708.00 | 761359 | 200 | 4000.00 | 3000000 |
| ui.contract | 1134.05 | 1205.44 | 725872 | 200 | 3000.00 | 3000000 |
| execute_button | 22.30 | 23.54 | 717 | 200 | 2500.00 | 500000 |

## Errors

- none
