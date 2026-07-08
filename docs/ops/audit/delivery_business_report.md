# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2519.87 | True |
| ui.contract |  | admin | 200 | ok | 1625.98 | True |
| execute_button |  | admin | 200 | DRY_RUN | 20.35 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 129.67 | True |
| payment.approve | payment.request.approve | demo_role_finance | 200 | approved | 115.04 | True |

## Errors

- none

## Warnings

- none
