# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2003.36 | True |
| ui.contract |  | admin | 200 | ok | 233.88 | True |
| execute_button |  | admin | 200 | DRY_RUN | 31.07 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 34.19 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 32.36 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 50.63 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 28.92 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 28.54 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 28.06 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 25.26 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 29.52 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 28.76 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
