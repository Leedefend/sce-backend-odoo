# Payment Tier Applicability Screen v1

## Purpose

Payment submit succeeds, but approval and completion are blocked because
`validation_status` remains `no` and no `tier.review` records are generated.

This screen classifies the tier-validation configuration in `sc_demo`.

## Screen Result

Tier models:

- `tier.definition`: exists
- `tier.review`: exists

Record counts:

- total `tier.definition`: 0
- `payment.request` tier definitions: 0
- total `tier.review`: 0
- `payment.request` reviews: 0

Relevant fields exist on `tier.definition`:

- `model`
- `model_id`
- `reviewer_id`
- `reviewer_group_id`
- `server_action_id`
- `rejected_server_action_id`
- `approve_sequence`
- `review_type`
- `active`

## Classification

The approval blocker is a missing approval-tier configuration fact.

It is not:

- payment submit logic
- finance authority
- project funding readiness
- mail runtime sender configuration
- frontend behavior

## Next Batch

Open a dedicated approval-tier config replay batch:

- create an active `tier.definition` for `payment.request`
- bind reviewer authority to the finance manager group
- bind approved/rejected server actions already present in
  `payment_request_tier_actions.xml`
- keep the change as runtime configuration replay, not payment model code
- verify rollback-only payment submit creates `tier.review`
- verify manager approval can move the payment to the next lifecycle state
