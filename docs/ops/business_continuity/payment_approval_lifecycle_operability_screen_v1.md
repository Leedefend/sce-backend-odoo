# Payment Approval Lifecycle Operability Screen v1

## Purpose

After finance visibility, funding carrier facts, and dev mail sender facts were
corrected, payment requests can be created and submitted on imported funded
projects. This screen checks whether the same flow can continue through
approval and completion.

The screen used rollback-only runtime records and did not persist test payment
data.

## Screen Result

Sample:

- project_id: 147
- contract_id: 5307
- payment state after submit: `submit`
- validation_status after submit: `no`
- generated `tier.review` count: 0
- finance manager user: `admin`
- finance manager group available: true

Manager actions:

- `action_approve`: blocked by `PAYMENT_TIER_INCOMPLETE`
- `action_set_approved`: callable but state remained `submit`
- `action_done`: blocked by `PAYMENT_TIER_INCOMPLETE`

Observed blocker:

```text
[SC_GUARD:PAYMENT_TIER_INCOMPLETE] 付款申请[...]：审批付款申请 被拒绝
原因：
- tier validation not complete
```

## Classification

This is an approval configuration / tier-validation applicability gap.

It is not:

- finance project visibility
- project funding carrier facts
- mail sender runtime config
- frontend behavior

The submit action calls `request_validation()`, but no tier review records were
created for the sampled payment request.

## Next Batch

Open a dedicated approval-tier screen:

- inspect active `tier.definition` records for `payment.request`
- classify whether definitions are missing, inactive, or condition-mismatched
- verify expected reviewer group/user source
- do not change approval semantics until the tier source is clear
