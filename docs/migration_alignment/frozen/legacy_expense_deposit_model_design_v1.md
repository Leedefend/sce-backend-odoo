# Legacy Expense Deposit Model Design v1

Status: `PASS`

## Scope

This batch adds a neutral carrier for loadable old expense, financial outflow,
and deposit-related business facts:

```text
sc.legacy.expense.deposit.fact
```

The source screen found `11167` candidate rows with project anchors and positive
amounts.

## Boundary

Included:

- source table and source record id
- project anchor
- optional partner anchor/text
- source family and direction
- source amount and amount source field
- old document number/date/state
- old note and pid

Excluded:

- `account.move`
- settlement facts
- payment ledger facts
- new approval runtime facts
- target business state mutation

## Semantics

This carrier is a historical/legacy business fact holder. It does not claim
that money has been paid, received, posted, settled, or approved in the new
system. Those meanings require later dedicated model or accounting design.

## Idempotency

SQL uniqueness:

```text
unique(legacy_source_table, legacy_record_id, import_batch)
```

## Next Gate

Generate XML assets only after this model is accepted. The asset generator must:

- require project external id resolution
- require positive amount
- preserve source family and direction
- keep partner optional
- avoid accounting, settlement, payment ledger, and approval runtime fields
