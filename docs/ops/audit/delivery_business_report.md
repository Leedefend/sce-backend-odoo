# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2058.4 | True |
| ui.contract |  | admin | 200 | ok | 347.07 | True |
| execute_button |  | admin | 200 | DRY_RUN | 39.71 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 32.92 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 29.81 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 51.42 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 28.98 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 27.46 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 30.3 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 29.47 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 27.65 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 26.62 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
