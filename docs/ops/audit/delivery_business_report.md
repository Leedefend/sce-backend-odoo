# Delivery Business Success Report

- steps: 12
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 1907.19 | True |
| ui.contract |  | admin | 200 | ok | 312.21 | True |
| execute_button |  | admin | 200 | DRY_RUN | 26.3 | True |
| payment.submit | payment.request.submit | demo_role_finance | 403 | unknown | 23.33 | False |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 24.29 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 38.29 | False |
| payment.submit | owner.payment.request.submit | demo_role_finance | 403 | unknown | 21.82 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 23.91 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 21.76 | True |
| payment.approve | owner.payment.request.approve | demo_role_finance | 403 | unknown | 24.84 | False |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 23.43 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 21.45 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
