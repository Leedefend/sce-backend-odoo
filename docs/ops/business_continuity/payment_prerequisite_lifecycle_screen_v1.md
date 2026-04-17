# Payment Prerequisite Lifecycle Screen v1

## Purpose

The prior screen confirmed that approved payment requests cannot reach `done`
unless payment ledger registration is possible. Ledger registration requires a
linked upstream business fact.

This screen classifies that prerequisite and the daily operating path that must
exist before payment completion can work.

All runtime records were created in rollback-only shell sessions.

## Metadata Result

Relevant models:

- `payment.request`: exists, 30102 records
- `payment.ledger`: exists, 12194 records
- `sc.settlement.order`: exists, 0 records
- `purchase.order`: exists, 0 records

Relevant relations:

- `payment.request.settlement_id` points to `sc.settlement.order`
- `sc.settlement.order.payment_request_ids` points back to `payment.request`
- `payment.ledger.payment_request_id` points to `payment.request`
- `sc.settlement.order.purchase_order_ids` points to `purchase.order`

Relevant menu/action metadata exists:

- `结算单`: `sc.settlement.order`
- `结算单（按项目）`: `sc.settlement.order`
- `付款记录`: `payment.ledger`
- `付款/收款申请`: `payment.request`

## Rollback Flow Result

Creating a settlement order with project, partner, currency, and contract works,
but the order starts in `draft`.

Settlement submit was blocked by existing imported payment requests that have
no settlement link:

```text
SC.VAL.3WAY.001: 付款申请未关联结算单
```

Creating a payment request linked to a draft settlement order was blocked:

```text
[SC_GUARD:P0_PAYMENT_SETTLEMENT_NOT_READY]
结算单状态为 draft
```

Direct settlement approval was blocked:

```text
缺少采购订单来源，无法批准结算单。
```

For downstream classification only, forcing the rollback-only settlement order
to `approve` showed the next guard:

```text
[SC_GUARD:P0_PAYMENT_OVER_BALANCE]
结算单剩余额度不足（剩余额度：0.0）
```

## Classification

The remaining payment operability blocker is upstream of payment approval.

The new-system daily path needs real settlement facts before payment can be
completed:

- settlement order must exist
- settlement order must be approved or completed
- settlement order must have payable/remaining amount
- settlement order approval expects purchase order source facts

Therefore, the next blocker is not:

- frontend rendering
- approval-tier configuration
- payment request submission
- finance manager authority
- ledger button exposure alone

## Business-Fact Gap

Current imported data has many payment requests and ledgers, but no
`sc.settlement.order` records and no `purchase.order` records.

This means old business facts were partially loaded at payment/ledger level, but
the new-system settlement prerequisite carrier is empty. Daily new-system
operation cannot complete payment until the settlement source path is usable.

## Next Batch

Open a dedicated procurement-to-settlement prerequisite screen:

- classify whether the correct source for payable settlement is `purchase.order`
  or a contract-backed settlement order materialized directly from imported
  contract/payment facts
- inspect whether purchase order creation can be driven from existing contract
  facts in rollback-only mode
- decide whether the next implementation is purchase source replay, settlement
  order replay, or action exposure for an existing hidden flow
- keep the next batch read-only unless the source-of-truth is certain
