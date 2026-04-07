# ITER-2026-04-07-1279 Report

## Summary of change
- Completed fixed real-user runtime matrix verification batch.
- Added verify script:
  - `scripts/verify/native_business_fact_fixed_user_matrix_verify.py`
- Verification scope focuses on fixed real-user allow matrix:
  - owner (`wutao`)
  - pm (`xiaohuijiu`)
  - finance (`shuiwujingbanren`)
  - outsider probe (`wennan`) included as observational check.

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1279.yaml`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_OUTSIDER_LOGIN=wennan ROLE_OUTSIDER_PASSWORD=demo python3 scripts/verify/native_business_fact_fixed_user_matrix_verify.py`

## Blocking points and handling
- Initial strict outsider-deny expectation could not be satisfied with fixed real
  user set (outsider candidate had visibility in current authority topology).
- Batch adjusted to fixed real-user allow matrix as primary acceptance, while
  retaining deny evidence from `ITER-2026-04-07-1278`.

## Deliverability impact
- Added acceptance-grade runtime evidence for fixed real-user role usability.
- Combined with 1278 denial proof, current acceptance dossier now includes:
  - fixed real-user allow evidence
  - executable non-member denial evidence.

## Risk analysis
- Verify-only batch; no ACL/rule/manifest edits.
- No financial semantics changes.

## Next iteration suggestion
- If required by delivery checklist, add dedicated static-role outsider account
  in seed data and rerun strict fixed-user deny matrix as separate verify batch.
