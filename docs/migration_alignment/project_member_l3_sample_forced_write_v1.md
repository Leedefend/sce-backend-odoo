# Project member L3 sample forced write v1

Status: FAIL_MODEL_REJECTED_ROLE_KEY  
Iteration: `ITER-2026-04-14-L3-SAMPLE-FORCED-WRITE`

## Scope

This batch force-writes exactly the first three rows from the current L3
checklist into `project.responsibility`.

Forced migration assumption:

- `proposed_role_key = project_member`
- `role_source_evidence = migration_l3_sample_forced_write_v1`
- `business_reviewer = system_migration_task`

## Boundary

This batch must not:

- expand beyond three rows;
- change ACL, security, or record rules;
- change `project.responsibility` model definitions or selection values.

The write uses the existing ORM model surface. If the existing model rejects
`project_member` as a role key, the batch fails rather than changing the model.

## Result

The forced write attempted to create the first three rows through the existing
`project.responsibility` ORM model.

Result:

- status: `FAIL`
- forced role key: `project_member`
- created rows: 0
- database writes: 0
- rollback target rows: 0

Failure reason:

```text
Wrong value for project.responsibility.role_key: 'project_member'
```

This is a target model selection constraint failure, not an approval gate.
