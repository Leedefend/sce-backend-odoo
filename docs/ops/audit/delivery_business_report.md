# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2520.52 | True |
| ui.contract |  | admin | 200 | ok | 1428.32 | True |
| execute_button |  | admin | 200 | DRY_RUN | 19.85 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 121.42 | True |
| payment.approve | payment.request.approve | demo_role_finance | 200 | approved | 92.15 | True |

## Errors

- none

## Warnings

- none
