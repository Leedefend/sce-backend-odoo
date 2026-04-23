# Receipt Blocker Policy Snapshot v1

Status: `PASS`

Generated at: `2026-04-15T09:05:00+00:00`

This snapshot classifies receipt rows that remain outside `receipt_sc_v1` after
contract-optional expansion. It performs no DB writes and does not create
settlement, ledger, payment-completion, or accounting facts.

## Counts

- receipt loadable records: `3411`
- remaining blocked records: `4001`
- DB writes: `0`
- Odoo shell: `false`

## Policy Counts

| Policy | Rows |
|---|---:|
| defer_project_anchor_missing | 90 |
| discard_deleted | 49 |
| discard_non_enterprise_partner_text | 1952 |
| discard_zero_or_negative_amount | 1908 |
| review_project_like_partner_text | 2 |

## Decision

`receipt_blockers_policy_classified_continue_mainline`

Rows classified as `discard_*` should not block the rebuild bus. Rows classified
as `review_*` require a separate owner review before partner supplementation.
