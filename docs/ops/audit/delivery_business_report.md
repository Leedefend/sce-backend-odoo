# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 1992.46 | True |
| ui.contract |  | admin | 200 | ok | 237.26 | True |
| execute_button |  | admin | 200 | DRY_RUN | 24.85 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 25.88 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 25.5 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 42.65 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 24.19 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 23.87 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 20.72 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 24.59 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 23.97 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 22.48 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
