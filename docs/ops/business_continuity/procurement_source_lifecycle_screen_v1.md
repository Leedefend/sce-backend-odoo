# Procurement Source Lifecycle Screen v1

## Purpose

Payment completion depends on an approved payable settlement with remaining
amount. The prior screen showed that purchase order source facts and settlement
line facts are the likely upstream carriers.

This screen checks whether the source path can support daily operation.

All runtime records were created in rollback-only shell sessions.

## Metadata Result

Relevant record counts in `sc_demo`:

- `purchase.order`: 0
- `purchase.order.line`: 0
- `product.product`: 0
- `sc.settlement.order`: 0
- `sc.settlement.order.line`: 0
- `uom.uom`: 26

The source models exist, but source business data is empty.

## Source Fact Result

Rollback-only creation proved that purchase source facts can be created:

- product source: created in rollback
- purchase order: created in rollback
- purchase order state after confirm: `purchase`
- purchase order amount total: `1.15`

Creating a settlement order with only `purchase_order_ids` did not populate
settlement amount:

- settlement amount total: `0.0`
- settlement remaining amount: `0.0`

The settlement amount carrier is `sc.settlement.order.line`, not the purchase
order total by itself.

## Settlement Line Result

Rollback-only creation with `sc.settlement.order.line` populated the payable
settlement amount:

- settlement amount total: `1.0`
- settlement remaining amount: `1.0`

Settlement submit/approve still hit an existing-data blocker:

```text
SC.VAL.3WAY.001: 付款申请未关联结算单
```

The validation listed imported payment requests such as:

- `PRQ2617639`
- `PRQ2617638`
- `PRQ2617637`
- `PRQ2617636`

## Downstream Classification

For downstream classification only, the rollback transaction forced the new
settlement order to `approve` after submit/approve was blocked by existing
orphan payment requests.

With an approved settlement carrying amount, the downstream payment lifecycle
worked:

- payment submit: `submit`, validation `pending`
- payment approval: `approved`, validation `validated`
- ledger registration: created
- payment done: `done`
- settlement remaining amount after payment: `0.0`

## Classification

The payment lifecycle is operable after approval when the upstream settlement
facts are valid.

The current blockers are upstream business facts:

- no persistent product/purchase source records
- no persistent settlement orders or settlement lines
- existing imported payment requests without settlement links block settlement
  submit/approve via three-way validation

This is not a frontend issue and not a payment approval issue.

## Next Batch

Open a dedicated legacy orphan payment compliance screen:

- count imported payment requests missing `settlement_id`
- classify whether they already have ledger/done facts
- decide whether replay should materialize settlement orders/lines from legacy
  payment facts, or link payments to reconstructed settlement facts
- do not implement until the replay source-of-truth and rollback path are clear
