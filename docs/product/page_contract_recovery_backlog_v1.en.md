# Page Contract Recovery Backlog (V1)

## Goal

- Establish a stable cadence: frontend stabilization -> design notes -> contract recovery.
- Prevent scattered page changes by tracking recovery status and next actions per page.

## Recovery Cadence

1. Stabilize product expression in frontend first.
2. Publish page design notes.
3. Recover stable semantics into page contract (`texts`/`sections`/`page_mode`).
4. Run minimal regression checks.

## Recovery Matrix

| Page | Current Status | Stabilized in Frontend | Recovered | Pending Recovery | Next Action |
| --- | --- | --- | --- | --- | --- |
| `login` | Round 1 done | Brand area, localized copy, capability chips, normalized error UX, interaction states | `sections(card/form/error)`, `texts` for title/fields/errors/capabilities | Theme token parametrization, tenant branding variants | Add configurable theme tokens in next theming round |
| `project.management` | Not started | N/A | N/A | page_mode, 7-block visual priority, risk emphasis, metric card semantics | Deliver frontend-stable version + `*_design_v1.md` |
| `projects.ledger` | Not started | N/A | N/A | overview layer semantics, status mapping, anomaly signals | Add overview layer and card priority fields |
| `projects.list` | Not started | N/A | N/A | column priority semantics, amount formatting, status localization | Start from list field order and semantic display |
| `task.center` | Not started | N/A | N/A | unified top info layer, status semantics | Converge with list-style page language |
| `risk.center` | Not started | N/A | N/A | workspace top layer, risk-level localization, key status readability | Emphasize risk visibility and anomaly cues |
| `cost.project_boq` | Not started | N/A | N/A | list header convergence, amount/status semantics | Converge with task/risk list patterns |

## 2026-07-04 Contract Coverage Calibration

The `project.management`, `projects.ledger`, `projects.list`, `task.center`,
`risk.center`, and `cost.project_boq` rows are scene-route recovery items, not
standalone `page_contracts_builder.py` page keys. They are currently carried by
the generic `scene` / `action` / `record` page contracts and scene-ready runtime
contracts.

The rows remain `Not started` only for page-specific product design recovery and
dedicated semantic downshift. They should not be interpreted as missing generic
page-contract coverage.

Latest guard evidence:

- `make verify.page_contract.sections_schema.guard verify.page_contract.data_source_semantics.guard verify.page_contract.text_key_coverage.guard` PASS.
- `make verify.frontend.page_contract.sections_coverage.guard verify.frontend.page_contract.key_consistency.guard verify.frontend.page_contract.section_tag_coverage.guard` PASS.

## Priority Semantic Types to Recover

- Page title/subtitle (`texts`).
- Page mode (`page_mode`).
- Key status mapping (technical value -> product value).
- Summary strip and metric label semantics.
- List key-column priority and formats (amount/percentage/update time).

## Scope Boundaries

- Do not change login API / token / session / router guard / app.init.
- Do not change core scene registry/governance/delivery policy.
- Do not change ACL baseline or deploy/rollback core logic.

## Checkpoints

- For each page: output file changes, design intent, contract compatibility, risks.
- For each batch: run `make verify.frontend.build` and `make verify.frontend.typecheck.strict`.
