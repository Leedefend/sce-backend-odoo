# System Stability Stress Regression Report

- total_calls: 300
- target_count: 3
- error_count: 3
- warning_count: 0

| intent | iterations | avg_ms | p95_ms | baseline_p95_ms | non_2xx_count | error_rate | statuses |
|---|---:|---:|---:|---:|---:|---:|---|
| system.init | 50 | 2518.88 | 2875.90 | 2095.36 | 0 | 0.000000 | 200 |
| ui.contract | 50 | 319.75 | 419.17 | 268.85 | 0 | 0.000000 | 200 |
| execute_button | 200 | 41.33 | 53.36 | 29.83 | 0 | 0.000000 | 200 |

## Errors

- system.init p95 regression: 2875.90 > baseline 2095.36
- ui.contract p95 regression: 419.17 > baseline 268.85
- execute_button p95 regression: 53.36 > baseline 29.83
