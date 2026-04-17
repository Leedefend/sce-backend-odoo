# No-Contract Payment Operation Gap Screen v1

## Scope

- Mode: read-only screen
- Target: remaining imported payments without parent `contract_id` after
  exact-one contract replay
- Code changes: none
- Database writes: none

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: whether a payment may be submitted without `contract_id` is a payment
  business rule. It must be resolved in backend business semantics, not by
  frontend special cases or scene orchestration.

## Current Business Fact Baseline

After exact-one contract replay:

| Classification | Count |
| --- | ---: |
| Remaining parent missing `contract_id` | 15250 |
| Remaining exact-one line contract candidates | 0 |
| Remaining multi-line-contract excluded | 143 |
| Remaining no-line-contract | 15107 |

The remaining no-line-contract records include valid old business facts such as
daily expense, invoice payment, deduction, or other non-contract outflow.

## Static Operation Finding

`payment.request.action_submit` still blocks submit when `contract_id` is empty:

```text
if not rec.contract_id:
    raise UserError("请先选择关联合同后再提交付款/收款申请。")
```

`payment.request.available_actions` has the same precheck:

```text
if not record.contract_id:
    return False, REASON_MISSING_PARAMS
```

This means the deterministic replay fixed contract-basis payments, but the new
system still cannot fully support no-contract daily spending through the normal
submit action.

## Interpretation

This is not a frontend issue.

The backend payment operation rule still encodes a mandatory-contract
assumption. That assumption conflicts with the confirmed old and current
business facts:

- some payments are contract-basis and should carry `contract_id`
- some payments are enterprise daily spending and should not require
  `contract_id`

## Stop Decision

Stop before code change.

Fixing this requires touching payment business semantics in:

```text
addons/smart_construction_core/models/core/payment_request.py
addons/smart_construction_core/handlers/payment_request_available_actions.py
```

Those paths match the repository `*payment*` high-risk stop condition. The
current AGENTS rules do not provide an automatic exception for changing payment
business semantics, so this must be opened as a dedicated high-risk backend task
with explicit scope and verification.

## Required Next Task

Open a dedicated backend business-fact rule adjustment:

```text
No-contract payment submit support
```

Required rule shape:

- allow `payment.request` submit without `contract_id` when no settlement is
  selected and the payment is a normal daily/non-contract outflow
- continue to block canceled contracts when a contract is selected
- continue to validate settlement consistency when settlement is selected
- keep attachment, funding, lifecycle, data-validator, and tier-validation
  checks intact
- update available-actions precheck to match `action_submit`

This must be verified with:

- rollback-only no-contract payment submit flow
- contract-selected payment submit flow
- settlement-selected consistency flow
- imported business continuity guard
