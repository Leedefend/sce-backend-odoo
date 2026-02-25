# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2199.1 | True |
| ui.contract |  | admin | 200 | ok | 257.85 | True |
| execute_button |  | admin | 200 | DRY_RUN | 28.53 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 31.45 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 31.72 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 44.68 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 25.61 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 25.81 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 25.94 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 23.59 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 25.82 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 23.61 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
