# Project member duplicate evidence retention v1

Status: FROZEN  
Iteration: `ITER-2026-04-14-0030ZA`

## Rule

Duplicate neutral evidence rows are retained.

They are not immediate delete targets, because each row preserves a legacy
source identity and import-batch trace.

## Evidence Attributes

Evidence-row attributes include:

- `legacy_member_id`;
- `legacy_project_id`;
- `legacy_user_ref`;
- `legacy_role_text`;
- `role_fact_status`;
- `import_batch`;
- `evidence`;
- `notes`;
- `active`.

## Pair Aggregate Attributes

Pair-level aggregate attributes include:

- `pair_key`;
- `project_id`;
- `user_id`;
- `evidence_count`;
- `role_fact_status_summary`;
- `batch_list`;
- `duplicate_evidence`;
- `first_neutral_id`;
- `last_neutral_id`.

## Future Actions

Future tasks may define archive, collapse, or flag behavior, but this batch does
not implement them.

Any future collapse must retain traceability back to each `legacy_member_id` and
must not create responsibility or permission semantics by itself.
