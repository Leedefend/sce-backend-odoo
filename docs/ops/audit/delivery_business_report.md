# Delivery Business Success Report

- steps: 9
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 1423.92 | True |
| ui.contract |  | admin | 200 | ok | 224.21 | True |
| execute_button |  | admin | 200 | DRY_RUN | 27.13 | True |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 29.66 | False |
| payment.submit | payment.request.submit | admin | 403 | PERMISSION_DENIED | 50.27 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 24.94 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 30.63 | True |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 29.17 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 25.37 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
