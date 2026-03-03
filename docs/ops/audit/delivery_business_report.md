# Delivery Business Success Report

- steps: 9
- error_count: 0
- warning_count: 1

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 1668.73 | True |
| ui.contract |  | admin | 200 | ok | 203.23 | True |
| execute_button |  | admin | 200 | DRY_RUN | 24.91 | True |
| payment.submit | payment.request.submit | sc_fx_finance | 403 | unknown | 24.22 | False |
| payment.submit | payment.request.submit | admin | 400 | BUSINESS_RULE_FAILED | 28.47 | False |
| payment.submit | owner.payment.request.submit | sc_fx_finance | 403 | unknown | 26.09 | False |
| payment.submit | owner.payment.request.submit | admin | 200 | ok | 23.72 | True |
| payment.approve | owner.payment.request.approve | sc_fx_finance | 403 | unknown | 24.86 | False |
| payment.approve | owner.payment.request.approve | admin | 200 | ok | 22.84 | True |

## Errors

- none

## Warnings

- payment.request.submit unavailable, fallback to owner.payment.request.submit
