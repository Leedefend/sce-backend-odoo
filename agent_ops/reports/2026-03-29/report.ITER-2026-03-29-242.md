# ITER-2026-03-29-242

## Summary
- Fixed project form governance pruning so `notebook/page` containers are kept when parser output includes empty `children` alongside non-empty `tabs/pages`.
- Live `ui.contract(action_open)` for `project.project` now preserves page structure for `description`, `settings`, and `sc_system`.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-29-242.yaml`
- `addons/smart_core/utils/contract_governance.py`
- `agent_ops/scripts/project_form_layout_field_gap_audit.py`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-242.yaml`
- `python3 -m py_compile addons/smart_core/utils/contract_governance.py agent_ops/scripts/project_form_layout_field_gap_audit.py`
- `make verify.smart_core`
- `make restart`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/project_form_layout_field_gap_audit.py --db sc_demo --login sc_fx_pm --password prod_like --container sc-backend-odoo-dev-odoo-1 --action-id 449 --record-id 3'`

## Result
- `container_probe.governed_page_fields` now includes:
  - `description`
  - `settings`
  - `sc_system`
- `live_http.live_page_fields` now includes:
  - `description`
  - `settings`
  - `sc_system`
- `per_page_gap = {}`

## Risk
- Medium-low.
- Change is isolated to governed form layout pruning for container nodes.
- No ACL/schema/business fact changes.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-29-242.yaml addons/smart_core/utils/contract_governance.py agent_ops/reports/2026-03-29/report.ITER-2026-03-29-242.md agent_ops/state/task_results/ITER-2026-03-29-242.json`

## Next
- Refresh the frontend and verify tabs render from live contract.
- If any remaining mismatch exists, focus on frontend detail renderer consuming preserved `page/group` hierarchy rather than backend contract completeness.
