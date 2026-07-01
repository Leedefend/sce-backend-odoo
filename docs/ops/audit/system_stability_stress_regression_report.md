# System Stability Stress Regression Report

- status: WARN
- total_calls: 6
- target_count: 3
- rounds: 1
- warmup_per_round: 0
- fail_rounds_required: 2
- policy_version: v1
- error_count: 0
- warning_count: 6

| intent | overall_grade | rounds | p50_ms | p95_ms | p99_ms | baseline_p95_ms | fail_rounds | warn_rounds | error_rate | statuses |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| system.init | warn | 1 | 1579.72 | 1718.69 | 1718.69 | 0.00 | 0 | 1 | 0.000000 | 200 |
| ui.contract | warn | 1 | 1024.59 | 1024.86 | 1024.86 | 0.00 | 0 | 1 | 0.000000 | 200 |
| execute_button | warn | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0.000000 |  |

## Errors

- none

## Warnings

- system.init baseline p95 missing, grade defaults to WARN
- system.init has warn rounds 1/1
- ui.contract baseline p95 missing, grade defaults to WARN
- ui.contract has warn rounds 1/1
- execute_button baseline p95 missing, grade defaults to WARN
- execute_button has warn rounds 1/1
