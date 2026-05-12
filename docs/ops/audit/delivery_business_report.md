# Delivery Business Success Report

- steps: 6
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 885.92 | True |
| ui.contract |  | admin | 200 | ok | 1146.93 | True |
| execute_button |  | admin | 200 | DRY_RUN | 19.49 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 127.95 | True |
| payment.approve | payment.request.approve | demo_role_finance | 400 | PAYMENT_TIER_INCOMPLETE | 71.37 | False |
| payment.reject | payment.request.reject | demo_role_finance | 200 | rejected | 54.57 | True |

## Errors

- none

## Warnings

- none
