# Project Import GO/NO-GO v4

## Decision

- GO: create a dedicated high-risk write batch for 30-row create-only project
  skeleton import, if `sc_demo` is confirmed to be the intended empty target.
- NO-GO: do not run upsert/update import.

This document is a gate decision only. It does not import data.

## Evidence

| Evidence | Value |
| --- | ---: |
| target database | `sc_demo` |
| target identity rows | 0 |
| sample rows | 30 |
| safe fields | 22 |
| target dry-run create | 30 |
| target dry-run update | 0 |
| target dry-run error | 0 |
| rollback design | present |
| write runbook | present |

## GO Conditions

A later write batch may start only if all conditions hold:

- user explicitly authorizes a database write batch;
- a new task contract declares write-mode scope;
- the task remains create-only;
- target identity rows remain 0 immediately before write;
- dry-run remains `create=30`, `update=0`, `error=0`;
- rollback plan is accepted;
- no forbidden field or relation mapping is added.

## NO-GO Conditions

Do not proceed if:

- target identity rows are greater than 0;
- any row is classified as update;
- any dry-run error exists;
- any company, specialty, lifecycle/state, user, partner, contract, payment,
  supplier, tax, bank, cost, settlement, or attachment write is requested;
- importer implementation cannot prove it writes only safe fields;
- rollback cannot be scoped by the 30 sample `legacy_project_id` values.

## Current Conclusion

The project skeleton import line is ready for a separately authorized 30-row
create-only write batch design and implementation.

It remains NO-GO for general production import and NO-GO for update/upsert.
