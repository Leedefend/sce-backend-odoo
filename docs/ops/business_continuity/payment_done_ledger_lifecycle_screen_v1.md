# Payment Done Ledger Lifecycle Screen v1

## Purpose

Payment submit and approval now work on imported funded projects after the
funding carrier, mail sender, and approval-tier facts were replayed.

This screen checks the next lifecycle segment:

- approved payment request to `done`
- payment ledger registration path

The screen used rollback-only runtime records and did not persist test payment
or ledger data.

## Screen Result

Sample state before completion:

- payment state after manager approval: `approved`
- validation_status after manager approval: `validated`

Direct completion result:

```text
ValidationError: 付款未结清，无法完成。
```

Manual ledger-before-done result:

```text
UserError: 付款申请未关联结算单，不能登记付款。
```

## Classification

The payment request can now reach the approved business state, but cannot reach
the completed business state until ledger registration can happen.

Ledger registration requires a linked settlement business fact. A standalone
approved payment request without `settlement_id` is not enough to continue to
`done`.

This is not:

- approval-tier configuration
- finance user authority
- funding carrier readiness
- mail sender runtime configuration
- frontend behavior

## Architecture Boundary

This belongs to the business-fact layer.

The next fix must not make the frontend bypass lifecycle state, and must not
fabricate ledger facts in scene orchestration. The system needs a clear
settlement/payment linkage path for daily operation.

## Next Batch

Open a dedicated settlement prerequisite screen:

- identify whether daily payable work should start from settlement and then
  generate payment requests
- verify which imported or newly created business facts can provide
  `payment.request.settlement_id`
- classify whether the blocker is missing settlement data, missing settlement
  creation flow, or missing payment-from-settlement action exposure
- keep the first batch read-only unless the linkage source is certain
