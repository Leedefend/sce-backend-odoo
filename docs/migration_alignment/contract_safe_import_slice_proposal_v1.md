# Contract Safe Import Slice Proposal v1

Iteration: `ITER-2026-04-13-1839`

Decision: `NO-GO for contract write`

## Candidate Target Fields

These fields are candidates for a future contract skeleton slice, not approved for writing in this batch:

| Target field | Source | Current decision |
|---|---|---|
| `subject` | `HTBT` fallback `DJBH`/`HTBH` | candidate |
| `type` | inferred from `FBF` / `CBF` own-company rule | candidate after review |
| `project_id` | `XMID -> project.project.legacy_project_id` | candidate only when known written project matched |
| `partner_id` | counterparty text | blocked |
| `date_contract` | `f_HTDLRQ` | candidate after date preprocessing |
| `date_start` | `f_GCKGRQ` | candidate after date preprocessing |
| `date_end` | `JGRQ` | candidate after date preprocessing |
| `note` | selected source text | candidate after text policy |

## Fields Explicitly Deferred

| Field / area | Reason |
|---|---|
| `name` | system-generated sequence; legacy `HTBH` needs reference-code policy |
| `state` | workflow state should not be replayed in first slice |
| `category_id` | dictionary mapping not frozen |
| `contract_type_id` | dictionary mapping not frozen |
| explicit `tax_id` mapping | tax semantics not frozen |
| computed amount fields | target amounts are computed from line and tax |
| `line_ids` | no target-ready structured line source identified |
| attachments | `f_FJ` references need attachment strategy |
| `analytic_id` | accounting-related relation; out of first slice |
| `budget_id` | budget/BOQ relation not mapped |

## Safe Candidate Count

The dry-run required all of the following for a safe skeleton candidate:

- legacy `Id` exists
- subject exists
- project maps to known written project ID
- direction is `out` or `in`
- exactly one partner match
- `DEL != 1`

Result:

- safe skeleton candidates: 0

## Required Before Any Write

1. Add or confirm a legacy contract identity field on `construction.contract`.
2. Decide legacy contract number policy for `HTBH` and `DJBH`.
3. Resolve partner matching for `FBF` / `CBF`.
4. Freeze contract direction rule.
5. Freeze tax/default tax behavior for create-only contracts.
6. Keep state as `draft` in first slice.
7. Exclude `DEL=1`.

Conclusion:

Do not create a contract sample yet. Continue with contract field alignment and partner master-data matching.
