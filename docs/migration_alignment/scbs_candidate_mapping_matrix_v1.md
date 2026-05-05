# SCBS Candidate Mapping Matrix

Date: 2026-05-05
Source database: `LegacyScbs20260417`
Raw report: `/home/odoo/workspace/legacy_mssql_scbs/reports/scbs_candidate_matrices_raw.txt`
SQL report: `/home/odoo/workspace/legacy_mssql_scbs/reports/scbs_candidate_matrices.sql`

## Purpose

This matrix prepares the review inputs before implementing the new business
entity support models.

It separates three candidate sets:

1. legacy business/accounting entity candidates from `XMID/XMMC`;
2. real project candidates from `GCMC`;
3. partner duplicate candidates from `T_Base_CooperatCompany`.

## Summary

### Business Entity Candidates

| Suggested state | Candidates | Covered rows | Amount / balance signal |
| --- | ---: | ---: | ---: |
| `business_entity_candidate` | 11 | 9590 | 1,776,858,895.29 |
| `low_weight_candidate` | 28 | 234 | 31,473,726.39 |
| `platform_candidate` | 1 | 1048 | 13,207,512.15 |
| `ignored_deleted_candidate` | 1 | 10 | 5,797,600.00 |
| `ignored_test_candidate` | 1 | 1 | 0.00 |

Interpretation:

- The strong business entity candidate set is small: 11 carriers.
- Those 11 carriers carry nearly all meaningful SCBS carrier-weighted facts.
- Low-weight candidates include same-name different-ID records and small
  supplier-contract-only records. These should map through a mapping table, not
  create new entities automatically.
- `公司综合平台` is a platform candidate, not a construction project.
- Deleted/test records should not enter active business dimensions.

### Project Candidates

| Suggested state | Candidates | Covered rows | Amount signal |
| --- | ---: | ---: | ---: |
| `project_candidate` | 29 | 7867 | 453,469,136.98 |
| `single_source_project_candidate` | 12 | 132 | 10,495,094.45 |
| `not_real_project_review` | 2 | 18 | 2,170,006.00 |
| `ignored_test_candidate` | 1 | 5 | 171,793.00 |

Interpretation:

- 29 `GCMC` values have multi-source evidence and should be reviewed as real
  construction project candidates.
- 12 `GCMC` values appear in only one source family. They may still be real
  projects, but need lower-confidence handling.
- `公司综合平台` and `一公司项目` need explicit review because they look like
  organization/accounting labels instead of real projects.

### Partner Duplicate Candidates

| Suggested state | Candidates | Legacy rows | Active rows |
| --- | ---: | ---: | ---: |
| `duplicate_across_carriers` | 429 | 908 | 886 |
| `duplicate_same_carrier_or_empty_tax` | 88 | 179 | 168 |
| `tax_code_conflict` | 32 | 74 | 61 |

Interpretation:

- Partner duplication is not incidental. It is part of how the legacy system
  repeated counterparties under different carriers.
- `duplicate_across_carriers` should not be blindly merged by name because the
  old carrier relationship may be business-significant.
- `tax_code_conflict` must block automatic partner merge until reviewed.

## Top Business Entity Candidates

These are the first-review list for `sc.business.entity`.

| Legacy name | Legacy ID | Sources | Rows | Payment | Contract | Stock | Fund balance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `德阳泰诚硕商贸有限公司` | `95f1fe93331842488d5469ad771a1543` | 5 | 1214 | 25,310,477.16 | 24,840,307.85 | 19,781,304.83 | 313,171,903.58 |
| `四川世旺鑫润商贸有限公司` | `af1d4b6f50504cfd9c6b0b13065fecff` | 5 | 1595 | 44,740,090.02 | 50,823,731.91 | 38,160,987.47 | 171,687,637.15 |
| `四川迈投建筑工程有限公司` | `547603a871bd42c5b19681683626a314` | 4 | 1548 | 40,179,125.37 | 21,075,666.50 | 0.00 | 153,041,944.88 |
| `四川晟博通达商贸有限公司` | `306434aba43f4128b4ab6d8a6b289674` | 5 | 870 | 24,066,460.43 | 32,290,811.96 | 23,409,343.24 | 132,866,747.72 |
| `德阳市博众建材销售有限公司` | `88ca50467a784725aa4b42467b549e21` | 4 | 598 | 25,160,450.00 | 55,442,152.83 | 0.00 | 131,587,834.28 |
| `四川鑫垚建筑劳务有限公司` | `b8bc05aace5149f2af36878e9c030f4c` | 5 | 1124 | 15,042,087.61 | 6,825,616.80 | 10,840.00 | 137,144,888.72 |
| `四川翔驰恒瑞商贸有限公司` | `fa8bdd0d90aa4585bf8c27011d01b6d5` | 5 | 668 | 11,986,790.33 | 11,494,127.66 | 7,229,894.63 | 93,577,028.80 |
| `四川宏政嘉斯建筑工程有限公司` | `ad4866a0a8a24b629a87165d98be5948` | 4 | 735 | 6,016,988.35 | 2,269,923.81 | 0.00 | 64,995,050.89 |
| `四川宏川建筑劳务有限公司` | `8e63129abde54614ae66ef7df8f91046` | 4 | 536 | 3,758,159.67 | 2,746,263.84 | 0.00 | 44,907,855.04 |
| `德阳森元路面工程有限公司` | `0d7cd766eb9f4d23b53761e593148e25` | 4 | 479 | 2,146,165.98 | 2,531,449.40 | 0.00 | 30,092,041.84 |
| `四川嘉易欢悦建筑工程有限公司` | `a5f4079846f345788536d81c916ef70f` | 4 | 223 | 174,900.00 | 70,500.00 | 0.00 | 6,201,344.74 |

Special platform candidate:

| Legacy name | Legacy ID | Sources | Rows | Contract | Fund balance |
| --- | --- | ---: | ---: | ---: | ---: |
| `公司综合平台` | `fb0c4133-f011-44a4-a285-59cfd30aec27` | 4 | 1048 | 1,719,361.15 | 11,488,151.00 |

## Top Project Candidates

These are the first-review list for `project.project` mapping.

| Legacy `GCMC` | Sources | Rows | Amount | Date range |
| --- | ---: | ---: | ---: | --- |
| `旌阳区供水项目——柏隆净水厂` | 3 | 1082 | 80,565,147.13 | 2023-11-03 to 2026-04-13 |
| `高新产业园配套项目（包2）` | 3 | 715 | 53,969,657.86 | 2023-06-12 to 2026-04-13 |
| `高新产业园配套项目（包3）` | 3 | 526 | 41,693,664.61 | 2023-06-29 to 2026-03-23 |
| `三星堆环线基础设施改造` | 3 | 487 | 40,570,598.45 | 2023-04-10 to 2026-02-09 |
| `2023年高标准农田改造提升-东美村` | 3 | 363 | 31,019,536.48 | 2023-10-10 to 2026-03-31 |
| `二重厂西路等4条道路工程` | 3 | 678 | 30,999,034.82 | 2022-11-19 to 2026-03-31 |
| `旌阳区供水项目——柏隆供水管网` | 3 | 426 | 24,169,122.39 | 2024-03-06 to 2026-03-30 |
| `澜沧江西路（苗山街-蓥华山路）` | 3 | 441 | 16,596,414.15 | 2024-10-01 to 2026-04-13 |
| `2024高标准农田建设项目-龙泉村` | 3 | 64 | 16,353,265.39 | 2024-03-01 to 2026-02-11 |
| `龙泉山路二段(赣江路-信江路)` | 3 | 334 | 13,130,246.22 | 2023-06-19 to 2026-02-03 |

## Acceptance Rules For Next Iteration

Business entity acceptance:

- create candidate rows only, under the current main company;
- mark high-weight rows as `candidate`;
- mark `公司综合平台` as platform candidate;
- do not auto-create `res.company`;
- do not auto-merge same-name different-ID legacy rows.

Project mapping acceptance:

- use `GCMC` as the project candidate source;
- exact match is accepted only when name and business context are clear;
- fuzzy match remains a suggestion, not an automatic write;
- non-project labels remain unresolved.

Partner mapping acceptance:

- block auto-merge on `tax_code_conflict`;
- treat cross-carrier duplicates as candidate relationships, not duplicate
  cleanup targets;
- preserve source partner ID for all imported facts.

## Implementation Gate

The next code iteration can add:

- `sc.business.entity`;
- `sc.legacy.business.entity.map`;
- optional fact fields for `business_entity_id` and raw legacy carrier values.

It should not yet project SCBS facts into formal contracts, payments, or stock
documents.

## Candidate Import Status

Implemented and executed against `sc_prod_sim`:

- Candidate CSV: `artifacts/migration/scbs_business_entity_candidates_v1.csv`
- Import script: `scripts/migration/scbs_business_entity_candidate_import.py`
- Result JSON: `artifacts/migration/scbs_business_entity_candidate_import_result_v1.json`
- Preview CSV: `artifacts/migration/scbs_business_entity_candidate_import_preview_v1.csv`
- Rollback target CSV: `artifacts/migration/scbs_business_entity_candidate_import_rollback_targets_v1.csv`

Write result:

| Metric | Value |
| --- | ---: |
| candidate rows | 12 |
| `sc.business.entity` rows | 12 |
| `sc.legacy.business.entity.map` rows | 12 |
| created `res.company` rows | 0 |
| mapping state | all `candidate` |

Idempotency check:

- first write created 12 business entities and 12 mapping rows;
- repeated write created 0 new rows and updated the existing 12 + 12 rows;
- `res.company` remained at 1 row.

Current entity type split:

| Entity type | Count |
| --- | ---: |
| `trade` | 5 |
| `labor` | 2 |
| `platform` | 1 |
| `unknown` | 4 |

This import remains a review staging step only. No mapping has been confirmed,
and no SCBS business fact has been imported into formal business documents.

## Project Candidate Import Status

Implemented and executed against `sc_prod_sim`:

- Candidate CSV: `artifacts/migration/scbs_project_candidates_v1.csv`
- Import script: `scripts/migration/scbs_project_candidate_import.py`
- Target review model: `sc.legacy.project.map`
- Result JSON: `artifacts/migration/scbs_project_candidate_import_result_v1.json`
- Preview CSV: `artifacts/migration/scbs_project_candidate_import_preview_v1.csv`
- Rollback target CSV: `artifacts/migration/scbs_project_candidate_import_rollback_targets_v1.csv`

Write result:

| Metric | Value |
| --- | ---: |
| candidate rows | 43 |
| `project_candidate` rows | 29 |
| `single_source_project_candidate` rows | 12 |
| `not_real_project_review` rows | 2 |
| created `project.project` rows | 0 |
| `sc.legacy.project.map` rows | 43 |

Current mapping split:

| Suggested state | Mapping state | Match method | Rows | Fact rows | Amount signal |
| --- | --- | --- | ---: | ---: | ---: |
| `project_candidate` | `candidate` | `exact` | 1 | 363 | 31,019,536.48 |
| `project_candidate` | `candidate` | `fuzzy` | 12 | 3317 | 191,867,309.96 |
| `project_candidate` | `candidate` | `none` | 16 | 4187 | 230,582,290.54 |
| `single_source_project_candidate` | `candidate` | `fuzzy` | 3 | 34 | 4,724,375.72 |
| `single_source_project_candidate` | `candidate` | `none` | 9 | 98 | 5,770,718.73 |
| `not_real_project_review` | `conflict` | `none` | 2 | 18 | 2,170,006.00 |

Important guardrail:

- `公司综合平台` and `一公司项目` are kept as `conflict` rows with empty
  `project_id`, even if a same-name target record exists.
- Exact target assignment currently exists only for
  `2023年高标准农田改造提升-东美村` -> `project.project` id `666`.
- Fuzzy rows keep candidate suggestions in `evidence` only. They are not
  auto-confirmed and do not write formal project facts.

Idempotency check:

- first write created 43 project mapping rows;
- repeated write created 0 new rows and updated the existing 43 rows;
- `project.project` remained at 785 rows.

## Partner Candidate Import Status

Implemented and executed against `sc_prod_sim`:

- Candidate CSV: `artifacts/migration/scbs_partner_candidates_v1.csv`
- Import script: `scripts/migration/scbs_partner_candidate_import.py`
- Target review model: `sc.legacy.partner.map`
- Result JSON: `artifacts/migration/scbs_partner_candidate_import_result_v1.json`
- Preview CSV: `artifacts/migration/scbs_partner_candidate_import_preview_v1.csv`
- Rollback target CSV: `artifacts/migration/scbs_partner_candidate_import_rollback_targets_v1.csv`

Write result:

| Metric | Value |
| --- | ---: |
| candidate rows | 549 |
| `duplicate_across_carriers` rows | 429 |
| `duplicate_same_carrier_or_empty_tax` rows | 88 |
| `tax_code_conflict` rows | 32 |
| created `res.partner` rows | 0 |
| merged `res.partner` rows | 0 |
| `sc.legacy.partner.map` rows | 549 |

Current mapping split:

| Suggested state | Mapping state | Match method | Rows | Legacy rows | Active rows |
| --- | --- | --- | ---: | ---: | ---: |
| `duplicate_across_carriers` | `candidate` | `exact_name` | 99 | 214 | 205 |
| `duplicate_across_carriers` | `candidate` | `multiple` | 19 | 43 | 39 |
| `duplicate_across_carriers` | `candidate` | `none` | 311 | 651 | 642 |
| `duplicate_same_carrier_or_empty_tax` | `candidate` | `exact_name` | 14 | 28 | 28 |
| `duplicate_same_carrier_or_empty_tax` | `candidate` | `multiple` | 11 | 24 | 22 |
| `duplicate_same_carrier_or_empty_tax` | `candidate` | `none` | 63 | 127 | 118 |
| `tax_code_conflict` | `conflict` | `tax_code` | 7 | 16 | 13 |
| `tax_code_conflict` | `conflict` | `exact_name/multiple/none` | 25 | 58 | 48 |

Important guardrail:

- All `tax_code_conflict` rows stay in `conflict` state.
- Tax-code conflict rows cannot be confirmed unless the reviewer manually
  changes the match method to `manual` and chooses a target partner.
- Candidate import assigned 113 unambiguous target partner suggestions, but no
  row was auto-confirmed.
- `res.partner` remained at 7288 total rows: 7284 active, 4 inactive.

Idempotency check:

- first write created 549 partner mapping rows;
- repeated write created 0 new rows and updated the existing 549 rows.

## Fact Projection Gate

Implemented read-only reconciliation:

- Script: `scripts/migration/scbs_mapping_reconciliation.py`
- Result JSON: `artifacts/migration/scbs_mapping_reconciliation_result_v1.json`
- Summary CSV: `artifacts/migration/scbs_mapping_reconciliation_summary_v1.csv`
- Unresolved examples CSV:
  `artifacts/migration/scbs_mapping_reconciliation_unresolved_examples_v1.csv`
- Markdown report: `artifacts/migration/scbs_mapping_reconciliation_report_v1.md`

Current result: `BLOCK_FORMAL_FACT_PROJECTION`

| Dimension | Candidates | Confirmed | Unconfirmed | Conflicts | Mapped targets | Fact rows | Amount signal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| business entity | 12 | 0 | 12 | 0 | 12 | 10638 | 1,790,066,407.44 |
| project | 43 | 0 | 43 | 2 | 1 | 8017 | 466,134,237.43 |
| partner | 549 | 0 | 549 | 32 | 113 | 1115 | 0.00 |

Interpretation:

- Formal projection into contracts, payments, stock documents, fund ledgers, or
  formal reports is not allowed yet.
- Staging import may proceed if it preserves raw legacy keys, mapping state,
  source table, source primary key, and reconciliation totals.
- The largest blocker is not technical loading; it is business acceptance of
  candidate mappings.

Allowed next iteration:

- add SCBS-specific staging fact models or reuse existing legacy fact models;
- import raw source facts into staging only;
- attach raw fields:
  - `legacy_xmid`
  - `legacy_xmmc`
  - `legacy_gcmc`
  - legacy partner ID/name/tax code
  - source table and source record ID
  - mapping state snapshots
- produce row-count and amount reconciliation by source table.

Blocked until mapping review:

- creating or merging `res.partner`;
- creating new `res.company`;
- auto-confirming fuzzy project matches;
- projecting SCBS facts into formal contracts, payments, inventory, or accounting
  records.

## Fact Staging Import Status

Implemented staging-only fact carrier:

- Model: `sc.legacy.scbs.fact.staging`
- View/menu: `SCBS旧库事实暂存`
- Import CSV: `artifacts/migration/scbs_fact_staging_v1.csv`
- Import script: `scripts/migration/scbs_fact_staging_import.py`
- Reconciliation script: `scripts/migration/scbs_fact_staging_reconciliation.py`
- Import result:
  `artifacts/migration/scbs_fact_staging_import_result_v1.json`
- Reconciliation report:
  `artifacts/migration/scbs_fact_staging_reconciliation_report_v1.md`

Current import result against `sc_prod_sim`:

| Source table | Fact family | Rows | Amount / balance signal | Date range |
| --- | --- | ---: | ---: | --- |
| `T_FK_Supplier` | payment | 9130 | 364,696,413.39 | 2018-09-01 to 2026-04-14 |
| `T_GYSHT_INFO` | supplier contract | 1592 | 274,514,199.25 | 2021-10-10 to 2026-03-31 |
| `T_RK_RKD` | stock in | 703 | 90,338,220.17 | 2021-04-20 to 2024-12-31 |
| `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | fund daily | 3798 | 1,290,762,428.64 | 2024-03-02 to 2026-04-16 |
| total | staging facts | 15223 | 2,020,311,261.45 | |

Mapping attachment coverage after the first staging import:

| Metric | Rows |
| --- | ---: |
| with business entity map | 8745 |
| with project map | 8017 |
| with partner map | 6371 |
| projection ready | 0 |
| staging ready only | 9536 |
| blocked by missing mapping | 5146 |
| blocked by mapping conflict | 541 |

Idempotency check:

- first write created 15223 staging rows;
- repeated write created 0 new rows and updated the existing 15223 rows.

Formal table counts after staging import:

| Model | All | Active | Inactive |
| --- | ---: | ---: | ---: |
| `res.company` | 1 | 1 | 0 |
| `project.project` | 785 | 785 | 0 |
| `res.partner` | 7288 | 7284 | 4 |
| `construction.contract` | 6934 | 6934 | 0 |

Conclusion:

- SCBS facts have been loaded only into staging.
- No staged row is projection-ready because all mapping rows are still
  unconfirmed.
- Formal projection remains blocked by design.

## Fact Partner Candidate Backfill

The first staging reconciliation exposed a real coverage gap: the partner
mapping table only covered duplicate/conflict partner candidates, not normal
single-name counterparties appearing in payment, contract, and stock facts.

Implemented and executed:

- Script: `scripts/migration/scbs_partner_fact_candidate_import.py`
- Result JSON:
  `artifacts/migration/scbs_partner_fact_candidate_import_result_v1.json`
- Preview CSV:
  `artifacts/migration/scbs_partner_fact_candidate_import_preview_v1.csv`
- Rollback target CSV:
  `artifacts/migration/scbs_partner_fact_candidate_import_rollback_targets_v1.csv`

Result:

| Metric | Value |
| --- | ---: |
| fact partner candidates created | 431 |
| created `res.partner` rows | 0 |
| merged `res.partner` rows | 0 |

After rerunning staging import, partner map attachment improved:

| Metric | Before | After |
| --- | ---: | ---: |
| staged facts with partner map | 6371 | 11409 |
| blocked rows | 5146 | 213 |
| blocked amount | 401,674,462.28 | 36,132,820.19 |
| staging-ready rows | 9536 | 14469 |
| conflict rows | 541 | 541 |
| projection-ready rows | 0 | 0 |

Current blocker report:

- Result JSON:
  `artifacts/migration/scbs_fact_staging_blocker_report_result_v1.json`
- Summary CSV:
  `artifacts/migration/scbs_fact_staging_blocker_summary_v1.csv`
- Missing mapping worklist:
  `artifacts/migration/scbs_fact_staging_missing_mapping_worklist_v1.csv`
- Conflict mapping worklist:
  `artifacts/migration/scbs_fact_staging_conflict_mapping_worklist_v1.csv`
- Markdown report:
  `artifacts/migration/scbs_fact_staging_blocker_report_v1.md`

Remaining blocked rows are now concentrated in:

- missing business-entity mappings: 49 payment rows, 153 supplier-contract rows,
  6 stock-in rows;
- missing project mappings: 5 supplier-contract rows;
- no remaining missing partner mappings after fact partner candidate backfill.

Remaining conflict rows are concentrated in:

- tax-code conflict partner mappings;
- the explicit non-project label `公司综合平台` in project mapping.

## Fact Dimension Candidate Backfill

The second staging reconciliation exposed the final missing-map gap: a small
set of low-weight or same-name-different-ID business carrier values from live
facts, plus one test project label, were not present in the first candidate
matrix.

Implemented and executed:

- Script: `scripts/migration/scbs_fact_dimension_backfill_import.py`
- Result JSON:
  `artifacts/migration/scbs_fact_dimension_backfill_result_v1.json`
- Preview CSV:
  `artifacts/migration/scbs_fact_dimension_backfill_preview_v1.csv`
- Rollback target CSV:
  `artifacts/migration/scbs_fact_dimension_backfill_rollback_targets_v1.csv`

Result:

| Metric | Value |
| --- | ---: |
| fact business-entity mapping candidates created | 29 |
| fact project mapping candidates created | 1 |
| created `sc.business.entity` rows | 0 |
| created `project.project` rows | 0 |
| created `res.company` rows | 0 |

After rerunning staging import, missing-map blockage is now closed:

| Metric | Before dimension backfill | After dimension backfill |
| --- | ---: | ---: |
| staged facts with business entity map | 8745 | 8977 |
| staged facts with project map | 8017 | 8022 |
| blocked rows | 213 | 0 |
| blocked amount | 36,132,820.19 | 0.00 |
| staging-ready rows | 14469 | 14672 |
| conflict rows | 541 | 551 |
| conflict amount | 45,501,236.24 | 51,298,836.24 |
| projection-ready rows | 0 | 0 |

The 10-row conflict increase is expected:

- 9 rows use test business carrier values such as `测试项目`;
- 1 row uses the test project label `测试项目`;
- these are mapped as review/conflict or ignored candidates instead of being
  silently dropped or treated as production dimensions.

Current staging reconciliation:

| Gate state | Rows | Amount / balance signal |
| --- | ---: | ---: |
| `staging_ready` | 14672 | 1,969,012,425.21 |
| `conflict` | 551 | 51,298,836.24 |
| `blocked` | 0 | 0.00 |
| `projection_ready` | 0 | 0.00 |

Formal table counts remain unchanged after all staging and backfill steps:

| Model | All | Active | Inactive |
| --- | ---: | ---: | ---: |
| `res.company` | 1 | 1 | 0 |
| `project.project` | 785 | 785 | 0 |
| `res.partner` | 7288 | 7284 | 4 |
| `construction.contract` | 6934 | 6934 | 0 |

Current remaining work is no longer technical missing-map coverage. It is
business review:

- confirm or ignore 29 low-weight business-entity mapping candidates;
- confirm or keep ignored the one test project candidate;
- resolve 551 conflict-stage fact rows, mostly partner tax-code conflicts plus
  explicit non-project/test labels;
- only then promote selected staged facts into formal business or reporting
  projections.

## Mapping Decision Workbook

Implemented the business-review handoff layer:

- Export script: `scripts/migration/scbs_mapping_decision_workbook.py`
- Apply script: `scripts/migration/scbs_mapping_decision_apply.py`
- Workbook CSV:
  `artifacts/migration/scbs_mapping_decision_workbook_v1.csv`
- Workbook result:
  `artifacts/migration/scbs_mapping_decision_workbook_result_v1.json`
- Action summary:
  `artifacts/migration/scbs_mapping_decision_action_summary_v1.csv`
- Priority top list:
  `artifacts/migration/scbs_mapping_decision_priority_top_v1.csv`
- Split workbook manifest:
  `artifacts/migration/scbs_mapping_decision_split_workbooks_manifest_v1.csv`
- Split workbook result:
  `artifacts/migration/scbs_mapping_decision_split_workbooks_result_v1.json`
- Batch validation result:
  `artifacts/migration/scbs_mapping_decision_batch_validate_result_v1.json`
- Batch validation summary:
  `artifacts/migration/scbs_mapping_decision_batch_validate_summary_v1.csv`
- Readiness report:
  `artifacts/migration/scbs_mapping_decision_readiness_report_v1.md`
- Readiness report result:
  `artifacts/migration/scbs_mapping_decision_readiness_report_result_v1.json`
- Priority-1 browser review page:
  `artifacts/migration/scbs_review_01_manual_partner_required_v1.html`
- Apply dry-run result:
  `artifacts/migration/scbs_mapping_decision_apply_result_v1.json`
- Apply preview:
  `artifacts/migration/scbs_mapping_decision_apply_preview_v1.csv`
- Decision validation result:
  `artifacts/migration/scbs_mapping_decision_validate_result_v1.json`
- Decision validation rows:
  `artifacts/migration/scbs_mapping_decision_validate_rows_v1.csv`
- Projection simulation:
  `artifacts/migration/scbs_mapping_decision_projection_simulation_v1.csv`
- Projection blocked examples:
  `artifacts/migration/scbs_mapping_decision_projection_blocked_examples_v1.csv`
- Partner target candidate report:
  `artifacts/migration/scbs_partner_target_candidate_report_v1.csv`
- Partner target candidate result:
  `artifacts/migration/scbs_partner_target_candidate_report_result_v1.json`
- Project target candidate report:
  `artifacts/migration/scbs_project_target_candidate_report_v1.csv`
- Project target candidate result:
  `artifacts/migration/scbs_project_target_candidate_report_result_v1.json`
- Business entity consolidation detail:
  `artifacts/migration/scbs_business_entity_consolidation_detail_v1.csv`
- Business entity consolidation summary:
  `artifacts/migration/scbs_business_entity_consolidation_summary_v1.csv`
- Business entity consolidation result:
  `artifacts/migration/scbs_business_entity_consolidation_report_result_v1.json`

Current workbook scope:

| Dimension | Mapping rows needing decision | Related fact rows | Related amount signal |
| --- | ---: | ---: | ---: |
| business entity | 41 | 8977 | 1,827,337,733.83 |
| project | 44 | 8022 | 466,306,030.43 |
| partner | 842 | 11409 | 729,524,418.61 |
| total review rows | 927 | n/a | n/a |

Current action split:

| Dimension | Suggested action | Mapping rows | Fact rows | Amount signal | Rows with target |
| --- | --- | ---: | ---: | ---: | ---: |
| business entity | `confirm_or_ignore_business_entity` | 39 | 8967 | 1,821,540,133.83 | 12 |
| partner | `confirm_or_ignore_partner` | 751 | 6912 | 532,521,571.39 | 211 |
| project | `confirm_or_ignore_project` | 41 | 7999 | 463,964,231.43 | 1 |
| partner | `choose_target_partner` | 50 | 3453 | 93,944,906.84 | 0 |
| partner | `review_non_counterparty_label` | 8 | 519 | 59,726,710.14 | 1 |
| partner | `manual_partner_required` | 31 | 523 | 43,331,230.24 | 0 |
| business entity | `ignore_or_conflict_test_value` | 2 | 10 | 5,797,600.00 | 0 |
| project | `ignore_if_not_real_project` | 2 | 18 | 2,170,006.00 | 0 |
| project | `ignore_or_conflict_test_value` | 1 | 5 | 171,793.00 | 0 |
| partner | `ignore_or_conflict_test_value` | 2 | 2 | 0.00 | 1 |

Recommended review order:

1. `manual_partner_required`: tax-code conflicts, 31 mapping rows.
2. `review_non_counterparty_label`: salary, warehouse, reserve-fund, and
   similar non-counterparty labels, 8 mapping rows.
3. `choose_target_partner`: duplicate or multi-target partner candidates, 50
   mapping rows.
4. test/non-real labels: mark ignored or conflict.
5. normal business-entity, project, and partner candidates.

Split decision workbooks:

The full 927-row workbook has been split into review-focused CSV files. Each
split file keeps the same columns as the main workbook and can be validated or
applied independently with `SCBS_MAPPING_DECISION_CSV`.

| File | Suggested action | Mapping rows | Fact rows | Amount signal |
| --- | --- | ---: | ---: | ---: |
| `scbs_mapping_decision_01_manual_partner_required_v1.csv` | `manual_partner_required` | 31 | 523 | 43,331,230.24 |
| `scbs_mapping_decision_02_review_non_counterparty_label_v1.csv` | `review_non_counterparty_label` | 8 | 519 | 59,726,710.14 |
| `scbs_mapping_decision_03_choose_target_partner_v1.csv` | `choose_target_partner` | 50 | 3453 | 93,944,906.84 |
| `scbs_mapping_decision_04_ignore_or_conflict_test_value_v1.csv` | `ignore_or_conflict_test_value` | 5 | 17 | 5,969,393.00 |
| `scbs_mapping_decision_05_ignore_if_not_real_project_v1.csv` | `ignore_if_not_real_project` | 2 | 18 | 2,170,006.00 |
| `scbs_mapping_decision_06_confirm_or_ignore_business_entity_v1.csv` | `confirm_or_ignore_business_entity` | 39 | 8967 | 1,821,540,133.83 |
| `scbs_mapping_decision_09_confirm_or_ignore_project_v1.csv` | `confirm_or_ignore_project` | 41 | 7999 | 463,964,231.43 |
| `scbs_mapping_decision_10_confirm_or_ignore_partner_v1.csv` | `confirm_or_ignore_partner` | 751 | 6912 | 532,521,571.39 |

Example validation command for one split:

```bash
SCBS_MAPPING_DECISION_CSV=/mnt/artifacts/migration/scbs_mapping_decision_01_manual_partner_required_v1.csv \
odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \
  < scripts/migration/scbs_mapping_decision_validate.py
```

The priority-1 split has been validated with blank decisions and passed. The
full workbook validation artifacts remain the canonical baseline in
`artifacts/migration`.

Batch validation:

- Script: `scripts/migration/scbs_mapping_decision_batch_validate.py`
- Reads the split workbook manifest and validates every split workbook.
- Classifies each batch as:
  - `BLANK`: no decisions filled;
  - `PARTIAL`: some decisions filled, some blank;
  - `READY`: all rows decided and valid;
  - `HAS_ERRORS`: at least one invalid row or missing file.

Current batch validation result:

| Batch status | Count |
| --- | ---: |
| `BLANK` | 8 |
| `PARTIAL` | 0 |
| `READY` | 0 |
| `HAS_ERRORS` | 0 |

This is the expected pre-review baseline. A batch should not be applied until
its status is `READY`, except when the business intentionally chooses to run a
partial batch and accepts that blank rows will remain unresolved.

Readiness dashboard:

- Script: `scripts/migration/scbs_mapping_decision_readiness_report.py`
- Full refresh script:
  `scripts/migration/scbs_mapping_decision_refresh_reports.sh`
- Consolidates the current staging gate, remaining gap, action summary, batch
  status, projection simulation, and execution order.
- Current report result:
  - staged facts: 15223;
  - missing-map blocked rows: 0;
  - conflict rows: 551;
  - projection-ready rows: 0;
  - review workbook rows: 927;
  - batch status: 8 `BLANK` batches.

This report is the recommended entry point for tracking the migration decision
phase.

## Revised Business Interpretation

The SCBS slice is now treated as old-system project-level real business facts
that should be integrated into the new system's existing company context.

This means:

- `res.company` creation remains out of scope for this slice.
- `sc.business.entity` is still needed, but as a business/accounting carrier
  dimension under the existing company context, not as a new hard isolation
  boundary.
- `project.project` mapping becomes a first-class projection gate because the
  slice is project-level factual detail.
- Partner mapping remains mandatory because supplier/payment/contract/stock
  facts cannot be safely attached without a target counterparty.
- Before formal projection, a duplicate/reconciliation matrix is required
  between existing company-level facts and SCBS project-level facts.

Projection acceptance rule:

- confirmed mappings alone do not mean the fact can be posted into formal
  operational models;
- confirmed mappings mean the staged fact has enough dimensions to enter the
  duplicate/reconciliation check;
- only non-duplicated or explicitly accepted supplement facts should be
  projected into source-tagged historical/reporting layers.

Overlap check added:

- `scripts/migration/scbs_project_fact_overlap_report.py`
- Current exact overlap results:
  - supplier contracts: 0 exact legacy-contract matches;
  - supplier contracts: 4 document-number matches, amount 46,201.00;
  - payments: 0 strict project+partner+date+amount matches;
  - payments: 214 partner+amount possible matches, amount 18,179,852.98;
  - stock-in: formal inbound table currently empty;
  - fund daily: no selected formal target.
- Sample evidence:
  `artifacts/migration/scbs_project_fact_overlap_examples_v1.csv`.

Interpretation:

- The supplier-contract document-number matches are only review hints because
  they are not legacy-ID matches and include low-quality numbers such as `111`
  and `测试`.
- The payment partner+amount matches are possible same-business-fact signals,
  not confirmed duplicates. Strict project+partner+date+amount matching still
  returns 0 rows.
- This means confirmed mapping is still the next prerequisite. Formal
  projection must remain source-tagged and fact-family-specific, so old
  project-level detail does not overwrite or double-count existing company-level
  records.

This supports a staged projection strategy: mapping confirmation first,
duplicate/reconciliation second, then fact-family-specific projection.

## Stock-In Detail Readiness

Stock-in should not be projected from `T_RK_RKD` header totals alone.

The detail readiness report now exists:

- `scripts/migration/scbs_stock_in_detail_readiness_report.py`
- `artifacts/migration/scbs_stock_in_detail_readiness_report_v1.md`

Observed result:

- 703 active stock-in headers carry 90,338,220.17 header amount.
- 700 active headers have 2209 detail lines carrying 90,454,874.17 line amount.
- 2197 of 2209 detail lines have a legacy material ID and match
  `T_Base_MaterialDetail` by `CLID`.
- 12 lines do not match the legacy material catalog by ID.
- Target Odoo has 0 formal material inbound documents. Product promotion is not
  the SCBS acceptance path.

Gate:

- SCBS stock-in fact detail is technically available.
- Formal inbound projection is blocked by SCBS material catalog mapping
  readiness, not by lack of legacy detail.
- Next iteration should build a material catalog mapping layer before creating
  `sc.material.inbound` headers and lines.
- Do not promote SCBS historical materials into product templates/products for
  this slice. Construction-enterprise material management uses material catalog
  identity for cost statistics, budget comparison, and management control.

Material catalog coverage report:

- `scripts/migration/scbs_stock_in_material_catalog_coverage_report.py`
- `artifacts/migration/scbs_stock_in_material_catalog_coverage_report_v1.md`

Current SCBS stock-in material coverage:

- 1658 material text groups;
- 1641 distinct SCBS legacy material IDs;
- 0 legacy-ID matches into the target material catalog;
- 28 exact text candidates, amount 3,812,618.16;
- 58 name/spec candidates, amount 5,293,410.42;
- 1563 catalog-missing groups, amount 79,110,391.59;
- 9 groups without legacy material ID, amount 2,238,454.00.

This means the target catalog already exists, but this SCBS slice uses a
different material-ID namespace. Text matches are review candidates only.

The review workbook has been imported into `sc.legacy.scbs.material.map`:

- imported rows: 1657;
- candidate rows: 1649, amount 88,216,420.17;
- conflict rows: 8, amount 2,238,454.00;
- confirmed rows: 0;
- skipped rows: 1 empty zero-amount material group.

Refresh command:

```bash
scripts/migration/scbs_mapping_decision_refresh_reports.sh
```

The refresh script regenerates:

- decision workbook and action summary;
- split workbooks and manifest;
- partner/project/business-entity target support reports;
- full validation and batch validation;
- readiness report.
- browser-friendly review pages for batches that are hard to review as CSV.

It has been executed successfully against `sc_prod_sim`; current regenerated
state remains 8 `BLANK` batches and 0 projection-ready rows.

Partner target candidate support:

| Suggested action | Mapping rows | Candidate rows | Rows with candidate target | Fact rows | Amount signal |
| --- | ---: | ---: | ---: | ---: | ---: |
| `choose_target_partner` | 50 | 154 | 154 | 3453 | 93,944,906.84 |
| `confirm_or_ignore_partner` | 751 | 782 | 259 | 6912 | 532,521,571.39 |
| `manual_partner_required` | 31 | 35 | 17 | 523 | 43,331,230.24 |
| `review_non_counterparty_label` | 8 | 28 | 22 | 519 | 59,726,710.14 |

This report is intentionally advisory only. It lists possible `res.partner`
target IDs by current mapping target, exact tax/legacy-tax match, exact name,
and fallback name search. It does not choose targets and does not write mapping
states.

Observed review risk from the report:

- Some duplicate names have multiple active target partners.
- Some tax-code matches are suspicious because the same tax code appears on
  unrelated-looking partner names.
- Some old partner labels are not real counterparties at all, so they may need
  special migration treatment instead of a normal `res.partner` binding.

Project target candidate support:

| Suggested action | Mapping rows | Candidate rows | Rows with candidate target | Fact rows | Amount signal |
| --- | ---: | ---: | ---: | ---: | ---: |
| `confirm_or_ignore_project` | 41 | 46 | 21 | 7999 | 463,964,231.43 |
| `ignore_if_not_real_project` | 2 | 2 | 1 | 18 | 2,170,006.00 |
| `ignore_or_conflict_test_value` | 1 | 1 | 0 | 5 | 171,793.00 |

The project report lists current exact targets and fuzzy suggestions already
captured in project mapping evidence. Fuzzy suggestions remain advisory only;
`decision_target_id` must be filled explicitly before confirmation.

Business-entity consolidation support:

| Suggested action | Legacy names | Mapping rows | Fact rows | Amount signal |
| --- | ---: | ---: | ---: | ---: |
| `review_same_name_legacy_ids` | 10 | 23 | 8198 | 1,762,063,393.72 |
| `confirm_or_ignore_business_entity` | 15 | 15 | 734 | 46,269,227.96 |
| `confirm_or_ignore_platform_entity` | 1 | 1 | 35 | 13,207,512.15 |
| `ignore_or_conflict_test_value` | 2 | 2 | 10 | 5,797,600.00 |

Important business-entity finding:

- Same-name different-ID carrier records are not a minor cleanup issue. They
  cover 8198 staged facts and 1,762,063,393.72 amount/balance signal.
- Many of the large same-name groups already point to one existing
  `sc.business.entity` candidate, for example `德阳泰诚硕商贸有限公司`,
  `四川世旺鑫润商贸有限公司`, and `四川翔驰恒瑞商贸有限公司`.
- The business decision is whether those same-name old IDs should consolidate
  into one business/accounting entity or stay separate as historical carriers.

Important interpretation:

- Workbook amounts are per dimension. They must not be added across dimensions,
  because one staged fact can require decisions for business entity, project,
  and partner at the same time.
- The workbook includes blank decision columns:
  - `decision`: `confirm`, `ignore`, `conflict`, or blank/`noop`;
  - `decision_target_id`: required for `confirm`;
  - `decision_note`: copied to the mapping note when applied.
- Applying decisions is dry-run by default.
- The apply script never creates companies, projects, partners, business
  entities, or formal facts. It only binds existing target IDs and changes
  mapping states after approval.
- Non-standard legacy partner labels such as `管理人员工资`, `代付工资`,
  `工资`, `高地库房`, and `备用金` are marked as
  `review_non_counterparty_label` instead of normal partner confirmation.

Apply guardrails:

- `confirm` requires an existing target ID.
- partner `tax_code_conflict` rows still require manual target selection.
- fuzzy project rows are suggestions only until the workbook explicitly
  confirms a target project.
- blank decisions are skipped; current dry-run skipped all 927 rows and made no
  database changes.
- `map_model` is validated against `dimension` during apply, so a manually
  edited workbook cannot accidentally apply a partner decision to a project or
  business-entity mapping row.

Decision validation and projection simulation:

- Script: `scripts/migration/scbs_mapping_decision_validate.py`
- Validates decision values, mapping row identity, target existence, and target
  company compatibility.
- Requires explicit `decision_target_id` when confirming partner tax-code
  conflicts.
- Simulates the staging gate after decisions without writing any mapping row.

Current validation against the blank workbook:

| Metric | Value |
| --- | ---: |
| blank decisions | 927 |
| validation errors | 0 |
| simulated `projection_ready` rows | 0 |
| simulated `staging_ready` rows | 14672 |
| simulated `conflict` rows | 551 |

This is the expected baseline. After business fills decisions, the validation
script must pass before `scbs_mapping_decision_apply.py` is run in write mode.
