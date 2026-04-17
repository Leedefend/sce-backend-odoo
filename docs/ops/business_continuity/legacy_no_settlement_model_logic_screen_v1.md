# Legacy No-Settlement Model Logic Screen v1

## Purpose

The legacy settlement fact existence screen confirmed:

- no old settlement-order rows exist
- no legacy settlement carrier exists
- no nonzero settlement amount aggregate exists
- old available facts are payment/ledger facts

Therefore the next line is not fact supplementation from old settlement data.
This screen locates the new-system business logic that must be adjusted.

## Located Logic

### Global Three-Way Validation

`sc.settlement.order.action_submit()` and `sc.settlement.order.action_approve()`
call:

```python
self.env["sc.data.validator"].validate_or_raise()
```

with no scope.

Because the validator is unscoped, `SC.VAL.3WAY.001` scans all payment requests.
Existing imported payment requests without `settlement_id` then block the new
settlement order being submitted or approved.

### Rule Behavior

`SC.VAL.3WAY.001` requires payable requests in states:

- `approve`
- `approved`
- `done`

to have `settlement_id`.

It also requires approved/done outbound settlement orders to have purchase
orders.

This rule is correct for normal new-system payable operation, but it is too
broad when invoked during a single new settlement order transition.

### Payment-Side Guards

Payment submit/approve already pass a scoped validator call:

```python
self.env["sc.data.validator"].validate_or_raise(scope=scope)
```

Payment ledger registration also correctly requires:

- approved payment request
- linked settlement order
- settlement state in `approve` or `done`

These payment-side guards should remain strict for new daily business.

## Classification

The adjustment should be a validation-scope correction, not a fabricated
settlement replay.

The old data cannot supply settlement facts. The new system should avoid using
historical missing-settlement requests as a global blocker for unrelated new
settlement transitions.

## Recommended Adjustment Boundary

Dedicated high-risk implementation batch:

1. Scope settlement transitions:
   - `sc.settlement.order.action_submit()`
   - `sc.settlement.order.action_approve()`

2. Adjust `SC.VAL.3WAY.001` so that when validation is scoped to
   `sc.settlement.order`, it checks only:
   - the target settlement order records
   - payment requests linked to those settlement orders, if needed

3. Keep payment request submit/approve strict:
   - new payment requests must still satisfy settlement linkage and balance
   - ledger registration must still require approved settlement

4. Preserve historical truth:
   - do not create settlement orders from old data when no old settlement fact
     exists
   - do not auto-upgrade draft/no-ledger historical payments
   - use ledger-backed completed payment facts only as historical evidence, not
     as fabricated settlement facts

## Stop Boundary

Implementing this requires changing backend payment/settlement validation
semantics. That belongs to a dedicated high-risk business-logic batch and should
not be bundled into this read-only screen.

No model, validator, payment, settlement, or frontend code was changed here.
