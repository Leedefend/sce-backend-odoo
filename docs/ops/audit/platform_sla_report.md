# Platform SLA Report

- iterations: 6
- target_count: 3
- error_count: 0
- warning_count: 1

| intent | p95_ms | p95_limit | max_payload_bytes | payload_limit | statuses |
|---|---:|---:|---:|---:|---|
| system.init | 1962.27 | 8000.00 | 246080 | 3500000 | 200 |
| ui.contract | 295.72 | 5000.00 | 128080 | 3500000 | 200 |
| execute_button | 27.87 | 3000.00 | 574 | 600000 | 404 |

## Errors

- none

## Warnings

- execute_button has non-2xx statuses in SLA run: [404]
