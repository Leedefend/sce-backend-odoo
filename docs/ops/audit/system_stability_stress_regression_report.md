# System Stability Stress Regression Report

- status: WARN
- total_calls: 1400
- target_count: 3
- rounds: 1
- warmup_per_round: 20
- fail_rounds_required: 1
- error_count: 0
- warning_count: 1

| intent | overall_grade | rounds | p50_ms | p95_ms | p99_ms | baseline_p95_ms | fail_rounds | warn_rounds | error_rate | statuses |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| system.init | warn | 1 | 1797.76 | 2075.29 | 2308.39 | 1962.27 | 0 | 1 | 0.000000 | 200 |
| ui.contract | pass | 1 | 215.96 | 309.76 | 372.95 | 295.72 | 0 | 0 | 0.000000 | 200 |
| execute_button | pass | 1 | 28.48 | 35.11 | 39.85 | 27.87 | 0 | 0 | 0.000000 | 200 |

## Errors

- none

## Warnings

- system.init has warn rounds 1/1
