## Summary

- corrected the delivery audit to replay the real frontend `ui.contract(action_open)` payload instead of a simplified probe
- confirmed the remaining structure drift is still real on the live HTTP path
- no backend business code or frontend renderer code changed in this batch

## Key Outcome

- container-side `UiContractHandler.handle()` with the exact frontend payload returns:
  - `group = 11`
  - `notebook = 1`
  - `page = 3`
- live HTTP `/api/v1/intent -> ui.contract(action_open)` with the same payload still returns:
  - `group = 9`
  - `notebook = 1`
  - `page = 3`
- this proves the remaining structure loss happens after the in-process handler result and before or during final HTTP delivery

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-237.yaml`
- `agent_ops/scripts/project_form_delivery_gap_audit.py`
- `agent_ops/reports/2026-03-29/report.ITER-2026-03-29-237.md`
- `agent_ops/state/task_results/ITER-2026-03-29-237.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-237.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_delivery_gap_audit.py`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/project_form_delivery_gap_audit.py --db sc_demo --login sc_fx_pm --password prod_like --container sc-backend-odoo-dev-odoo-1 --action-id 449 --record-id 3'`

## Risk

- low risk, diagnostics only
- no schema, ACL, record-rule, or user-facing business logic changed
- the remaining discrepancy is now narrowed to the HTTP delivery path, so further backend fixes can be targeted

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-237.yaml`

## Next Suggestion

- inspect the final HTTP delivery step after `UiContractHandler.handle()` returns, focusing on response shaping or alternate live path behavior that still reduces `group` from `11` to `9`
- use the corrected audit script as the only baseline for this chain
