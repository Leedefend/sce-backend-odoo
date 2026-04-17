# Settlement Optional Business Logic Decision v1

## Decision

Settlement order is not a mandatory prerequisite for every payment request.

It is an optional business carrier selected by the user when the business fact
actually has a settlement process.

This decision is based on verified imported facts:

- old data has payment request facts
- old data has ledger facts
- old data has approval facts
- old data does not have settlement order facts
- old data does not have nonzero settlement amount facts

Therefore, forcing every payment request to have `settlement_id` does not match
the user's real business facts.

## Business Rule

Payment request should support two valid paths.

### Path A: With Settlement

When the user selects a settlement order:

- settlement state must be approved or done before payment proceeds
- settlement project, partner, contract, and company must match the payment
- settlement payable balance must not be overpaid
- ledger registration remains linked to the approved payment request
- settlement-related amount and compliance fields remain active

### Path B: Without Settlement

When the user does not select a settlement order:

- payment request can still be submitted, approved, and completed if all other
  required business facts are present
- approval remains required
- funding carrier remains required
- attachments and contract checks remain required
- ledger registration can rely on the approved payment request itself
- settlement balance checks do not apply
- settlement missing state must not block unrelated new settlement transitions

## Historical Data Policy

Completed historical payment requests with ledger evidence are accepted as
historical business facts even when no settlement exists.

Draft historical payment requests without ledger evidence must not be promoted
to completed facts.

No settlement order should be fabricated from old data when no old settlement
source-of-truth exists.

## Implementation Boundary

The later high-risk backend implementation should adjust only the business
logic required for optional settlement:

1. Payment submit/approve:
   - do not require `settlement_id`
   - when `settlement_id` exists, keep current settlement state, consistency,
     compliance, and balance checks

2. Ledger registration:
   - allow ledger registration for approved payment requests without settlement
   - when `settlement_id` exists, keep approved/done settlement requirement

3. Three-way validation:
   - do not report missing settlement as an error for all payment requests
   - keep settlement consistency checks for records that select settlement
   - scope settlement transition validation to the target settlement order and
     its linked payments instead of scanning all historical orphan payments

4. Frontend:
   - consume backend field optionality
   - do not hardcode model-specific bypass behavior

## Non-Goals

This decision does not:

- remove settlement functionality
- weaken checks for payments that explicitly select a settlement order
- fabricate settlement facts from old payment facts
- alter accounting semantics
- change ACL or record rules
- change frontend behavior directly

## Risk

Implementation touches payment and settlement business semantics. It must be a
dedicated high-risk backend batch with exact file allowlist and verification.

This decision batch intentionally stops before code changes.
