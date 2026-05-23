# System Stability Stress Regression Report

- status: PASS
- total_calls: 9
- target_count: 3
- rounds: 1
- warmup_per_round: 1
- fail_rounds_required: 2
- policy_version: v1
- error_count: 0
- warning_count: 0

| intent | overall_grade | rounds | p50_ms | p95_ms | p99_ms | baseline_p95_ms | fail_rounds | warn_rounds | error_rate | statuses |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| system.init | pass | 1 | 4663.71 | 4904.79 | 4904.79 | 3634.85 | 1 | 0 | 0.000000 | 200 |
| ui.contract | pass | 1 | 1945.92 | 2207.27 | 2207.27 | 3192.28 | 0 | 0 | 0.000000 | 200 |
| execute_button | pass | 1 | 59.20 | 66.23 | 66.23 | 75.56 | 0 | 0 | 0.000000 | 200 |

## Errors

- none

## Warnings

- none
