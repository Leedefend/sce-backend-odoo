# Project Create-Only Write Rollback v1

## Purpose

This document defines the rollback requirement for a later 30-row create-only
project skeleton write batch. It does not execute rollback and does not write
database records in this iteration.

## Rollback Identity

Rollback must use only the sample `legacy_project_id` values from:

```text
data/migration_samples/project_sample_v1.csv
```

Do not use project name, company text, `PROJECT_CODE`, `other_system_id`, or
`other_system_code` as the rollback key.

## Pre-Write Backup Requirement

Before a later write batch starts:

1. Export target identity snapshot.
2. Confirm the 30 sample `legacy_project_id` values do not exist.
3. Save a timestamped pre-write snapshot artifact.
4. Record target database name, row count, and identity fields.

## Rollback Strategy

If the later write batch creates only the 30 sample project skeleton rows and no
dependent records, rollback may delete only records whose `legacy_project_id`
matches the 30-row sample.

Rollback must not delete:

- records without `legacy_project_id`;
- records created outside the sample;
- records matched only by project name;
- company, partner, user, contract, payment, supplier, tax, bank, cost,
  settlement, or attachment records.

## Rollback Preconditions

Rollback is allowed only if:

- every rollback target has `legacy_project_id` in the 30-row sample;
- no row has dependent records created by the import batch;
- no target row has been manually edited after the import batch;
- the rollback script produces a dry-run list before deletion.

If any condition is uncertain, stop and require manual database review.

## Post-Rollback Checks

After rollback:

- the 30 sample `legacy_project_id` values no longer exist in `project.project`;
- non-sample project records remain unchanged;
- verification gate passes;
- rollback result artifact records deleted row IDs and identities.

## Current Gate Conclusion

Rollback is design-ready only for a narrow create-only batch with no dependent
records. It is not approved for upsert/update rollback or for deleting any
record outside the 30-row sample identity set.
