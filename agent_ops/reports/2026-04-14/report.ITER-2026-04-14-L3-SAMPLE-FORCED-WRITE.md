# ITER-2026-04-14-L3-SAMPLE-FORCED-WRITE Report

## Summary

Attempted to force-write the first three L3 checklist rows into
`project.responsibility` with `role_key=project_member`.

## Result

FAIL_MODEL_REJECTED_ROLE_KEY.

- Forced sample rows: 3
- Forced role key: `project_member`
- Created rows: 0
- DB writes: 0
- Rollback target rows: 0
- Post audit matched records: 0

Failure:

```text
Wrong value for project.responsibility.role_key: 'project_member'
```

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-14-L3-SAMPLE-FORCED-WRITE.yaml`: PASS
- `python3 -m py_compile scripts/migration/project_member_l3_sample_forced_write.py`: PASS
- `DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/project_member_l3_sample_forced_write.py`: FAIL, model rejected `project_member`
- `python3 -m json.tool artifacts/migration/project_member_l3_sample_forced_write_result_v1.json`: PASS
- `python3 -m json.tool artifacts/migration/project_member_l3_sample_forced_write_post_audit_v1.json`: PASS
- `make verify.native.business_fact.static`: PASS

## Risk

No database record was created because the existing target model only accepts
the frozen role selection values. ACL, record rules, model definitions, and
selection values were not modified.
