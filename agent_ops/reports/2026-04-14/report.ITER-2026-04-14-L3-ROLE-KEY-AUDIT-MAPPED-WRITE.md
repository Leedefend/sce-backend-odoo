# ITER-2026-04-14-L3-ROLE-KEY-AUDIT-MAPPED-WRITE Report

## Summary

Audited legal role keys and target distribution, froze the L3 historical member
sample mapping, and wrote the first three L3 checklist rows with a legal role
key.

## Result

PASS.

- Legal role keys: `manager`, `cost`, `finance`, `cashier`, `material`,
  `safety`, `quality`, `document`
- Frozen mapping: `historical_project_member_l3_sample -> manager / 项目经理`
- Sample rows: 3
- Created responsibility records: 3
- DB writes: 3
- Post audit matched records: 3
- Rollback eligible rows: 3
- ACL / record rule changes: 0

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-14-L3-ROLE-KEY-AUDIT-MAPPED-WRITE.yaml`: PASS
- `python3 -m py_compile scripts/migration/project_member_l3_role_key_audit_mapped_write.py`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_member_l3_role_key_audit_mapped_write.py`: PASS
- JSON artifact checks: PASS
- `make verify.native.business_fact.static`: PASS

## Recovery Note

The first write attempt committed the three `manager` responsibility rows and
then failed while writing the rollback CSV due to a script CSV field mismatch.
The script was fixed to be idempotent by RUN_ID. The recovery run detected the
same three records, avoided duplicate writes, and generated the write result,
post audit, and rollback target list.
