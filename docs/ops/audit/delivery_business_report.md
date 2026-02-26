# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2591.08 | True |
| ui.contract |  | admin | 200 | ok | 428.17 | True |
| execute_button |  | admin | 200 | DRY_RUN | 31.64 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 29.75 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 28.32 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 46.65 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 26.39 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 31.03 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 28.77 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 33.13 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 37.24 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 33.18 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
