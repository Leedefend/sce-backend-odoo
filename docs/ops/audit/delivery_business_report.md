# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | wutao | 200 | ok | 2332.22 | True |
| ui.contract |  | wutao | 200 | ok | 1048.23 | True |
| execute_button |  | wutao | 200 | DRY_RUN | 18.06 | True |
| payment.submit | payment.request.submit | demo_role_finance | 200 | submit | 78.66 | True |
| payment.approve | payment.request.approve | demo_role_finance | 200 | approved | 73.35 | True |

## Errors

- none

## Warnings

- none
