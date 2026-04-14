# Contract Mapping Dry-Run Report v1

Iteration: `ITER-2026-04-13-1839`

Status: `PASS`

Decision: `NO-GO for contract write`

## Summary

The contract mapping dry-run completed without database writes and without ORM usage.

The old export contains 1694 contract rows. Direction and project mapping are partially workable, but `partner_id` and legacy rollback identity are not safe yet. The first contract write batch is therefore blocked.

## Statistics

| Metric | Result |
|---|---:|
| total rows | 1694 |
| raw project matches | 1606 |
| known written project matches | 146 |
| direction `out` | 1554 |
| direction `in` | 1 |
| direction `defer` | 139 |
| partner exact matches | 0 |
| `DEL=1` rows | 65 |
| safe skeleton candidates | 0 |

## Blockers

1. No confirmed target legacy contract identity field exists for exact rollback/upsert.
2. Required `partner_id` has 0 exact matches under the conservative text-match rule.
3. Only 146 rows currently map to known written project skeletons.
4. Tax and computed amount semantics are not frozen.
5. Contract line source is not identified.

## GO / NO-GO

Current result: `NO-GO for contract write`.

Allowed next step: contract field alignment and partner mapping preparation.

Recommended next batch:

`ITER-2026-04-13-1840 合同模型字段对齐与 legacy identity 专项 v1`
