# Delivery Business Success Report

- steps: 6
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 4405.0 | True |
| ui.contract |  | admin | 200 | ok | 1455.09 | True |
| execute_button |  | admin | 200 | DRY_RUN | 23.35 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 182.39 | True |
| payment.approve | payment.request.approve | demo_role_finance | 400 | PAYMENT_TIER_INCOMPLETE | 78.23 | False |
| payment.reject | payment.request.reject | demo_role_finance | 200 | rejected | 60.43 | True |

## Errors

- none

## Warnings

- none
