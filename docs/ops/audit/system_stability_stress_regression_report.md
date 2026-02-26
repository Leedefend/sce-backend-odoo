# System Stability Stress Regression Report

- total_calls: 1400
- target_count: 3
- error_count: 3
- warning_count: 0

| intent | iterations | avg_ms | p95_ms | baseline_p95_ms | non_2xx_count | error_rate | statuses |
|---|---:|---:|---:|---:|---:|---:|---|
| system.init | 200 | 1854.10 | 2096.31 | 1962.27 | 0 | 0.000000 | 200 |
| ui.contract | 200 | 227.28 | 315.27 | 295.72 | 0 | 0.000000 | 200 |
| execute_button | 1000 | 28.34 | 33.18 | 27.87 | 0 | 0.000000 | 200 |

## Errors

- system.init p95 regression: 2096.31 > baseline 1962.27
- ui.contract p95 regression: 315.27 > baseline 295.72
- execute_button p95 regression: 33.18 > baseline 27.87
