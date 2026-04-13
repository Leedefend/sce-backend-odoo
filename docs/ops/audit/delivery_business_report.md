# Delivery Business Success Report

- steps: 6
- error_count: 0
- warning_count: 3

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 5605.51 | True |
| ui.contract |  | admin | 200 | ok | 859.1 | True |
| execute_button |  | admin | 200 | DRY_RUN | 44.77 | True |
| payment.submit | owner.payment.request.submit | demo_role_finance | 200 | unknown | 41.6 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 200 | unknown | 40.63 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | unknown | 46.49 | False |

## Errors

- none

## Warnings

- payment.request flow unavailable, fallback to owner.payment.request flow
- owner.payment.request.submit unavailable in fallback mode
- owner.payment.request.approve unavailable in fallback mode
