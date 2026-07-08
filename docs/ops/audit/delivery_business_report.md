# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2475.68 | True |
| ui.contract |  | admin | 200 | ok | 1658.95 | True |
| execute_button |  | admin | 200 | DRY_RUN | 20.71 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 137.96 | True |
| payment.approve | payment.request.approve | demo_role_finance | 200 | approved | 93.92 | True |

## Errors

- none

## Warnings

- none
