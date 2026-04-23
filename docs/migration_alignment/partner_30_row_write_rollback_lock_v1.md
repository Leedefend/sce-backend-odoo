# Partner 30-Row Write Rollback Lock v1

Iteration: `ITER-2026-04-13-1860`

## Rollback Lock

Rollback target list:

- `artifacts/migration/partner_30_row_rollback_target_list_v1.csv`

Rollback key:

- `legacy_partner_source`;
- `legacy_partner_id`.

## Locked Result

- locked targets: 30;
- source: `cooperat_company`;
- write action: `created`;
- rollback dry-run status: not yet run;
- real rollback status: not authorized.

## Required Follow-Up

The next batch must run readonly verification and rollback dry-run lock:

- verify every target legacy identity resolves to exactly one partner;
- verify every target appears in the approved 30-row sample;
- verify no out-of-scope partner is locked;
- verify no duplicate legacy identity exists;
- keep real deletion blocked unless separately authorized.

## No-Delete Rule

This document is not rollback execution authorization.

Deleting by partner name, credit code, tax number, or company text remains forbidden.
