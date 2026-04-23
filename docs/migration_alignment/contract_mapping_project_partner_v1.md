# Contract Mapping Project And Partner v1

Iteration: `ITER-2026-04-13-1839`

Status: `PASS`

## Project Mapping

Legacy contract project key: `XMID`

Target relation: `construction.contract.project_id`

Target lookup rule: `XMID -> project.project.legacy_project_id`

| Item | Count |
|---|---:|
| Contract rows | 1694 |
| `XMID` non-empty | 1694 |
| Raw project IDs | 755 |
| Rows matching raw project export | 1606 |
| Known written project IDs from artifacts | 130 |
| Rows matching known written project IDs | 146 |
| Known written match rate | 8.62% |

Conclusion:

Only rows whose `XMID` maps to an existing written `project.project.legacy_project_id` can enter a bounded create-only contract sample. Current known written project coverage is too small for full import but enough for a future limited dry-run after partner and identity blockers are solved.

## Contract Direction Rule

The dry-run used a conservative text rule:

- `CBF` is own company and `FBF` is external -> `type=out`
- `FBF` is own company and `CBF` is external -> `type=in`
- otherwise -> `defer`

Own company names used:

- `四川保盛建设集团有限公司`
- `My Company`

Result:

| Direction | Count |
|---|---:|
| `out` | 1554 |
| `in` | 1 |
| `defer` | 139 |

This rule is plausible for first dry-run classification but should still be reviewed before write.

## Partner Mapping

Target relation: `construction.contract.partner_id`

Partner text fields:

- for inferred `out`: counterparty from `FBF`
- for inferred `in`: counterparty from `CBF`

Match method in this batch:

- exact text match against current `res.partner.display_name` and `res.partner.name`
- no fuzzy creation
- no partner creation
- no fallback to own company

Result:

| Item | Count |
|---|---:|
| Partner baseline records | 85 |
| Exact match rows | 0 |
| Defer rows | 1694 |
| Exact match rate | 0% |

Conclusion:

`partner_id` is a hard blocker for contract import. The next batch must create a partner text-match table and choose one of:

- import required counterparties as controlled partner master data first
- add a legacy counterparty text holding field and defer `partner_id`
- use a migration placeholder partner only if business explicitly approves that semantic compromise

Current recommendation: do not use a placeholder partner by default.
