# Delivery Business Success Report

- steps: 5
- error_count: 0
- warning_count: 0

| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |
|---|---|---|---:|---|---:|---|
| system.init |  | admin | 200 | ok | 2116.04 | True |
| ui.contract |  | admin | 200 | ok | 2142.2 | True |
| execute_button |  | admin | 200 | DRY_RUN | 20.62 | True |
| payment.submit | payment.request.submit | sc_fx_finance | 200 | submit | 243.16 | True |
| payment.approve | payment.request.approve | sc_fx_finance | 200 | approved | 122.86 | True |

## Errors

- none

## Warnings

- none
