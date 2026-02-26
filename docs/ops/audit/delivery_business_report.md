# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 3424.07 | True |
| ui.contract |  | admin | 200 | ok | 414.95 | True |
| execute_button |  | admin | 200 | DRY_RUN | 44.78 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 45.62 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 46.41 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 83.82 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 43.75 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 36.95 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 35.73 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 35.59 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 43.83 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 36.52 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
