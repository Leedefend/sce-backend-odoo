# Imported Payment Contract Linkage Screen v1

## Scope

- Database: `sc_demo`
- Mode: read-only screen
- Target: imported `payment.request` rows where `contract_id` is still empty.
- No database writes were performed.

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: `contract_id` on imported payment requests is a business-fact
  completeness issue. It must not be patched in frontend or scene orchestration.

## Deterministic Rule Tested

For each payment request with missing `contract_id`, search
`construction.contract` by:

- same `project_id`
- same `partner_id`
- same direction:
  - payment `type = pay` -> contract `type = in`
  - payment `type = receive` -> contract `type = out`
- contract state is not `cancel`

Only an exact-one result is considered deterministic.

No amount matching, name similarity, free-text matching, or arbitrary first
candidate selection is allowed.

## Result

| Metric | Count |
| --- | ---: |
| Total payment requests | 30102 |
| Missing `contract_id` | 17994 |
| Exact-one deterministic candidate | 0 |
| No candidate | 11248 |
| Multiple candidates | 6746 |

State distribution among missing-contract payments:

| State | Count |
| --- | ---: |
| draft | 10438 |
| done | 7556 |

## Samples

No-candidate samples:

| Payment | State | Project | Partner |
| --- | --- | ---: | ---: |
| 30101 | draft | 551 | 6660 |
| 30096 | draft | 167 | 1698 |
| 30092 | draft | 713 | 1380 |
| 30087 | draft | 554 | 889 |
| 30083 | draft | 673 | 5520 |

Multi-candidate samples:

| Payment | State | Project | Partner | Candidate Count |
| --- | --- | ---: | ---: | ---: |
| 30093 | draft | 223 | 462 | 3 |
| 30090 | draft | 338 | 4398 | 8 |
| 30086 | draft | 609 | 1231 | 2 |
| 30084 | draft | 577 | 4025 | 2 |
| 30077 | draft | 316 | 160 | 3 |

## Classification

The remaining missing-contract payment gap is not safely reducible by
`project + partner + direction`.

This means a write replay batch must not run under this rule. The next screen
needs a stronger source of truth, such as:

- legacy source line linkage fields
- import manifest or external-id relation
- payment detail rows carrying original contract identifiers
- workflow/audit target metadata only if it contains a deterministic contract
  reference

## Decision

Stop before write.

The system can continue operating because the imported continuity guard passed
and new payment flow can run on imported carriers. Historical missing contract
links remain a data-quality/business-fact backlog until a stronger deterministic
evidence source is identified.
