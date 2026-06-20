# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2071.77 | True |
| ui.contract |  | admin | 200 | ok | 1090.15 | True |
| execute_button |  | admin | 200 | DRY_RUN | 21.8 | True |
| payment.submit | payment.request.submit | sc_fx_finance | 200 | submit | 108.73 | True |
| payment.approve | payment.request.approve | sc_fx_finance | 200 | approved | 85.19 | True |

## Errors

- none

## Warnings

- none
