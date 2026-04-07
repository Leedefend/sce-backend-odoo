# ITER-2026-04-07-1272 Report

## Summary of change
- Added isolation anchor verification script:
  - `scripts/verify/native_business_fact_isolation_anchor_verify.py`
  - verifies key models carry required `company_id/project_id` anchors.
- Refocused `verify.native.business_fact.stage_gate`:
  - added isolation-anchor verify into main gate.
  - removed `native_business_fact_role_toolbar_panel_surface_consistency_smoke` from gate chain (pause surface-consistency expansion).
- Added project-org isolation docs:
  - `docs/ops/project_org_isolation_design_v1.md`
  - `docs/ops/project_org_isolation_rule_matrix_v1.md`
  - `docs/ops/project_org_isolation_acceptance_v1.md`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1272.yaml`
- FAIL: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`
  - failed at `native_business_fact_isolation_anchor_verify`:
  - `RuntimeError: isolation anchor missing: payment.ledger.company_id`

## Blocking points
- Real blocker identified: `payment.ledger` missing `company_id` isolation anchor.
- Repository guard impact:
  - direct edits under `*payment*` paths are high-risk stop condition in current lane.
  - this batch therefore stops at verified blocker evidence and cannot patch model field directly.

## Deliverability impact
- Positive:
  - isolation acceptance moved from implicit to explicit gate evidence.
  - surface-consistency expansion paused in stage gate as requested.
- Not yet complete:
  - payment/settlement unified isolation skeleton remains incomplete due `payment.ledger.company_id` gap.

## Risk analysis
- No forbidden path touched in this batch.
- Stop condition triggered by acceptance failure.
- Batch result: `FAIL`.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1272.yaml`
  - `git restore scripts/verify/native_business_fact_isolation_anchor_verify.py`
  - `git restore Makefile`
  - `git restore docs/ops/project_org_isolation_design_v1.md`
  - `git restore docs/ops/project_org_isolation_rule_matrix_v1.md`
  - `git restore docs/ops/project_org_isolation_acceptance_v1.md`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1272.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1272.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Open a dedicated high-risk payment-isolation authority task line for `payment.ledger` anchor补齐（`company_id`），then rerun native stage gate.
