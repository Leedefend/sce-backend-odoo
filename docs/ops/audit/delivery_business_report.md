# Delivery Business Success Report

- steps: 6
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 861.47 | True |
| ui.contract |  | admin | 200 | ok | 1189.3 | True |
| execute_button |  | admin | 200 | DRY_RUN | 19.94 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 96.25 | True |
| payment.approve | payment.request.approve | demo_role_finance | 400 | PAYMENT_TIER_INCOMPLETE | 47.65 | False |
| payment.reject | payment.request.reject | demo_role_finance | 200 | rejected | 37.68 | True |

## Errors

- none

## Warnings

- none
