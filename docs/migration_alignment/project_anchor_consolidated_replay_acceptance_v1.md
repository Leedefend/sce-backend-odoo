# Project Anchor Consolidated Replay Acceptance v1

Status: PASS

Task: `ITER-2026-05-07-PROJECT-ANCHOR-CONSOLIDATED-REPLAY`

## Scope

Consolidate project master replay into a single project-anchor flow for the
partner acceptance database. The replay now combines legacy project master rows
with visible contract-fact project anchors and enriches missing project business
nature from visible contract facts when the evidence is unique.

## Source Composition

| Source lane | Project rows | Evidence |
| --- | ---: | --- |
| `project_master` | 754 | `tmp/raw/project/project.csv` |
| `project_master_contract_enriched` | 1 | project master row with empty `NATURE`, enriched by one visible contract fact |
| `contract_visible_project_anchor` | 43 | visible contract facts whose `XMID` is absent from project master |
| Total replay payload | 798 | unified `fresh_db_project_anchor_replay_payload_v1.csv` |

The 43 contract-visible project anchors cover 48 visible contract rows.

## Acceptance Database Result

Target database: `sc_partner_acceptance`

| Metric | Value |
| --- | ---: |
| Input payload rows | 798 |
| Created rows | 0 |
| Updated rows | 798 |
| Post-write identity count | 798 |
| Replay status | PASS |

The acceptance database has no missing or extra project `legacy_project_id`
values compared with the unified payload.

## Dependent Contract Surface

`construction.contract.operation_strategy` is a stored related field from
`project_id.operation_strategy`. After the consolidated project replay, the
contract layer has no missing project linkage.

| Contract metric | Value |
| --- | ---: |
| Contracts with project strategy `joint` | 6567 |
| Contracts with project strategy `direct` | 283 |
| Contracts without project linkage | 0 |
| Visible income-surface contracts with `joint` | 6551 |
| Visible income-surface contracts with `direct` | 282 |

The 43 contract-visible project anchors are linked by 48 contract rows.

## Operation Strategy Alignment

The replay maps project business nature into the current model field:

| Source business nature | Target `operation_strategy` |
| --- | --- |
| `联营` | `joint` |
| `自营` | `direct` |

Final acceptance distribution:

| `operation_strategy` | Rows |
| --- | ---: |
| `joint` | 760 |
| `direct` | 38 |

Two project master rows still have no confirmed business nature and therefore
remain on the model default `direct`; they are not treated as confirmed direct
business facts:

| Legacy project ID | Project name | Source deleted flag |
| --- | --- | --- |
| `0bb1dac8c9a94e39b421b3a619491c1f` | 公司综合管理平台 | `1` |
| `eb14bf937d704385be6d6c968b71bac5` | 万润苑改造项目 | `1` |

## Deferred Project Gaps

20 contract project IDs remain deferred because they are absent from project
master and do not pass the visible income contract filter. Their raw
`GCYSZJ` amount sums to `43266877.41`.

These deferred contract rows are not present in the current
`construction.contract` table by `legacy_contract_id`, so they are not current
visible contract records with missing project linkage. They remain outside the
visible contract replay policy.

Primary blocker categories:

| Blocker | Meaning |
| --- | --- |
| `non_visible_status` | legacy contract status is outside the visible income-contract filter |
| `missing_subject` | contract title is empty |
| `missing_counterparty` | counterparty is empty |

The deferred rows are retained in:

`artifacts/migration/fresh_db_project_anchor_replay_gap_matrix_v1.csv`

## Artifacts

- `artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_project_anchor_replay_gap_matrix_v1.csv`
- `artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json`

## Decision

`project_anchor_consolidated_replay_accepted`

## Next

Continue with dependent business-fact replay or review the 20 deferred project
gaps before widening the project-anchor inclusion policy.
