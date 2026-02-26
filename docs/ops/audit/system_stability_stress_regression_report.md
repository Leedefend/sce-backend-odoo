# System Stability Stress Regression Report

- status: PASS
- total_calls: 3
- target_count: 3
- rounds: 1
- warmup_per_round: 0
- fail_rounds_required: 1
- policy_version: v1
- error_count: 0
- warning_count: 0

| intent | overall_grade | rounds | p50_ms | p95_ms | p99_ms | baseline_p95_ms | fail_rounds | warn_rounds | error_rate | statuses |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| system.init | pass | 1 | 1653.03 | 1653.03 | 1653.03 | 1962.27 | 0 | 0 | 0.000000 | 200 |
| ui.contract | pass | 1 | 193.50 | 193.50 | 193.50 | 295.72 | 0 | 0 | 0.000000 | 200 |
| execute_button | pass | 1 | 26.26 | 26.26 | 26.26 | 27.87 | 0 | 0 | 0.000000 | 200 |

## Errors

- none

## Warnings

- none
