# Project member neutral expansion strategy v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030NX`  
Database: `sc_demo`

## Purpose

Classify mapped legacy `project_member` rows before expanding the neutral
carrier write.

This batch is readonly. It does not write `sc.project.member.staging`,
`project.responsibility`, ACLs, record rules, or role keys.

## Findings

| Item | Count |
| --- | ---: |
| source rows | 21390 |
| mapped project/user rows | 7389 |
| already neutral rows | 34 |
| remaining relation-unique rows | 0 |
| remaining duplicate-relation evidence rows | 7355 |
| distinct relation keys | 769 |
| duplicate relation keys | 735 |
| placeholder or unmapped user rows | 14001 |

## Interpretation

The first 34-row neutral write consumed all remaining relation-unique rows.

The next expansion pool is not a clean set of new unique project/user relations.
It is a duplicate-relation evidence pool: multiple legacy member rows can map to
the same `project_id/user_id` pair.

These rows may still be valid migration evidence, but they must not be promoted
to `project.responsibility` or interpreted as additional responsibility roles.

## Next Gate

Open a dedicated duplicate-relation evidence carrier write task only if the
task contract explicitly accepts:

- multiple legacy rows per same `project_id/user_id` pair;
- `role_fact_status = missing`;
- no `project.responsibility` write;
- no record-rule or permission-chain wiring;
- rollback by neutral carrier `legacy_member_id` and `import_batch`.

## Artifacts

```text
artifacts/migration/project_member_neutral_expansion_plan_v1.json
artifacts/migration/project_member_neutral_expansion_relation_unique_slice_v1.csv
artifacts/migration/project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv
```
