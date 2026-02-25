# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 1556.66 | True |
| ui.contract |  | admin | 200 | ok | 235.47 | True |
| execute_button |  | admin | 200 | DRY_RUN | 26.76 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 25.61 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 31.47 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 40.71 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 26.57 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 33.75 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 35.14 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 30.82 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 30.84 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 25.68 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
