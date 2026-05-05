# SCBS Project Fact Integration Iteration Status

Date: 2026-05-05

## Business Premise

The data already present in the new system is treated as company-level data
that users have already entered.

The SCBS slice is treated as old-system project-level real business facts. The
integration target is therefore fact consolidation under the existing company
context, not creating a separate company dataset by name.

Project operation strategy is now an explicit second-level global isolation
dimension after company isolation:

- confirmed SCBS project-level business facts are treated as `公司直营`, even
  when legacy department/company names contain `联营`;
- existing new-system projects only keep their prior `联营项目` classification
  when they do not carry confirmed SCBS project facts;
- this classification is stored on `project.project.operation_strategy` and
  propagated to formal projection targets through project-related stored fields.

## Current Progress

| Area | Status | Evidence |
| --- | --- | --- |
| legacy backup restore | done | `LegacyScbs20260417` restored from `DB_BAK_SCBS.zip` |
| fact staging | done | 15,223 staged facts, 2,020,311,261.45 amount/balance signal |
| missing mapping blockers | done | 0 blocked rows after dimension backfill |
| business entity/project/partner candidate maps | done | candidate models, views, access rules, and import scripts exist |
| decision workbook | refreshed | 0 active review rows; inactive residuals retained for audit |
| formal data side effects | controlled | SCBS formal rows are source-tagged and projected only after explicit policy gates; no `res.company` rows created by SCBS staging |
| existing-formal overlap report | done | `artifacts/migration/scbs_project_fact_overlap_report_v1.md` |
| stock-in detail readiness | done | `artifacts/migration/scbs_stock_in_detail_readiness_report_v1.md` |
| SCBS material mapping review model | done | `sc.legacy.scbs.material.map` loaded with 1657 review rows |
| material catalog bootstrap | done | 1455 SCBS material catalogs created, 108 linked by business key, 86 existing links confirmed |
| business entity bootstrap | done | 27 business entities created, 12 existing targets confirmed, 39/41 entity maps confirmed |
| low-risk project/partner confirmation | done | 1 exact project map and 229 single-target exact partner maps confirmed |
| strong project candidate confirmation | done | 2 single strong project candidates confirmed; 1 multi-strong candidate intentionally skipped |
| project fact bootstrap | done | user confirmed SCBS project names as business facts; 38 target projects created and mapped |
| partner fact bootstrap | done | 629 SCBS historical partners created and mapped without merging into existing partner master |
| residual fact exclusion | done | 33 non-business/test residual staging facts archived from active projection pool |
| operation-strategy policy refresh | done | 62 SCBS fact-bearing projects are now `公司直营`; 3 existing mapped projects corrected from prior `联营项目` default |
| payment/contract formal projection | done | 7,774 positive payment facts written to `sc.payment.execution`; 218 negative payment facts written to `sc.legacy.payment.adjustment.fact`; 1,124 no-project payment/contract facts written to `sc.legacy.enterprise.business.fact`; 1,576 supplier-contract facts written to `sc.general.contract`; all SCBS formal rows are `公司直营` |
| stock-in formal projection | done | 697 material inbound headers and 2,173 lines written; 88,601,224.17 line amount; all SCBS inbound rows are `公司直营` and use material catalog identity |
| fund-daily enterprise projection | done | 3,798 enterprise fund daily documents written by business entity; project binding is 0 |
| unified residual register | done | 36 residual/audit rows remain after enterprise no-project carrier write |
| closure reconciliation | pass | source facts, formal writes, and residual register reconcile; duplicate/source/strategy/material guards all pass |
| release acceptance | pass | strict simulation acceptance and empty-database acceptance both pass |
| formal projection dry-run plan | done | 15,190 active facts planned; remaining operational gaps are explicit residuals |

## Open Gaps

| Gap | Why It Matters | Current Finding | Next Action |
| --- | --- | --- | --- |
| non-real/test residual mappings | residual dirty labels should not become normal business dimensions | 33 staging rows archived inactive; active decision workbook is empty | keep inactive for audit, do not project |
| partner identity conflicts | wrong partner merge changes supplier/payment facts | partner target candidate report now has 0 rows; partner facts are preserved as independent SCBS historical partners | no further partner merge required for current fact projection |
| project non-real/test residues | project-level facts are now created as target projects except non-real/test residues | normal project facts are fully mapped; non-real/test residual facts archived inactive | no active project mapping blocker |
| payment duplicate policy | company-level existing payments may overlap project-level old payments | strict exact overlap is 0; broad partner+amount possible overlap is 214 rows / 18,179,852.98 | project as source-tagged SCBS project-level supplement; do not merge into existing `payment.request` |
| formal target project requirement | current project document models require `project_id`, but some SCBS facts have no source project clue | after direct-project recovery: payment 1,115 rows / 39,138,881.03 and supplier contract 9 rows / 623,832.00 have no project clue; they are now written to company-scoped `sc.legacy.enterprise.business.fact`; stock-in 0 projectless active rows | do not create project documents from these rows; retain enterprise carrier unless source-chain evidence later identifies a real project |
| project bucket entity coverage | project buckets should not be created without confirmed entity evidence | projectless payment and supplier-contract rows have no business entity and no project clue; they are now company-scoped enterprise facts | do not create bucket projects for these rows |
| SCBS direct project clue recovery | direct-operation facts should not stay in an unassigned-project bucket | 21 provisional bucket projects were matched to SCBS `BASE_SYSTEM_PROJECT` direct projects by `legacy_xmid/legacy_xmmc`; 2,269 rows / 217,682,489.35 recovered | bucket labels removed; projects normalized as `legacy_scbs_direct_project` and `公司直营` |
| enterprise no-project facts | no-project rows must be accepted without fabricating projects | payment 1,115 rows / 39,138,881.03 and supplier contract 9 rows / 623,832.00 still have no `XMID/XMMC/GCMC`; they are written to `sc.legacy.enterprise.business.fact` with company isolation and `公司直营` strategy | keep as historical enterprise facts; do not create project documents from `bm/zmbtext` alone |
| residual business-scope classification | no-project rows must be explainable without fabricating projects | residual scope report is PASS: payment has 1,111 rows / 38,167,981.03 with legacy department/business-bucket only, 4 rows / 970,900.00 with counterparty/remark only; supplier contracts have 9 rows / 623,832.00 with business-entity/department text only | classification explains why enterprise carrier is correct and project creation is unsafe |
| negative payment facts | payment target model enforces non-negative amounts | 218 confirmed-project payment rows / -63,703,002.32 have been written to `sc.legacy.payment.adjustment.fact`: 67 refund/return rows / -4,797,262.89; 44 account/internal adjustment rows / -27,710,200.00; 107 rows / -31,195,539.43 retained with explicit unknown-text classification | keep them out of positive payment execution; use the historical adjustment carrier for audit and future business review |
| supplier contract document-number review | low-quality document numbers can collide | legacy source-key duplicate is 0; document reference match is 1 | use `legacy_source_model + legacy_record_id` as identity; keep document number as source reference only |
| material residual conflicts | stock-in lines need material identity for cost statistics, budget comparison, and management control | 8 missing-ID material text groups accepted as business facts; 6 material catalogs created and 2 existing catalogs linked; SCBS material map is now 1,657 confirmed / 0 conflict | no product-library promotion; material catalog remains source of truth |
| stock-in line quality residuals | target inbound line requires positive quantity and line detail | zero-quantity/zero-amount placeholder lines were skipped; remaining stock-in residual is only 3 zero-amount headers without legacy lines | keep zero-amount no-line headers as audit residual; do not create empty formal inbound docs |
| fund daily enterprise document | fund daily is not a project document | 3,798 rows written to enterprise fund daily with `business_entity_id`; `project_id` is empty for all SCBS rows | treat as formal enterprise business document, not residual |
| unified residual audit | rows outside operational write must be explainable at上线 | 36 rows are registered in `artifacts/migration/scbs_unified_residual_register_v1.csv` and summarized in `artifacts/migration/scbs_unified_residual_register_v1.md` | use this as上线差异说明; do not treat registered residuals as missing operational writes |

## Projection Readiness By Fact Family

| Fact Family | Current Decision |
| --- | --- |
| business entity dimension | business-fact accepted for active facts; 39 confirmed, 2 inactive residual conflicts retained |
| project dimension | business-fact accepted for active facts; 41 confirmed, 2 inactive residual conflicts, 1 inactive ignored retained |
| partner dimension | business-fact accepted; 858 confirmed, 121 candidate with no fact rows, 1 conflict with no current projection impact |
| supplier contracts | formal write done: 1,576 project-confirmed rows / 272,941,574.25 plus 9 enterprise no-project facts / 623,832.00 |
| supplier payments | formal write done: 7,774 positive payment executions / 383,815,778.68 plus 218 historical payment adjustment facts / -63,703,002.32 plus 1,115 enterprise no-project facts / 39,138,881.03 |
| stock-in | formal write done for project-confirmed operational headers: 697 headers / 2,173 lines / 88,601,224.17; 3 zero-amount no-line headers remain residual |
| fund daily | formal write done as enterprise business documents: 3,798 rows / 1,290,762,428.64 account balance; project binding 0 |

## Material Management Policy Alignment

Construction-enterprise material management is different from production
enterprise product management.

For this SCBS slice, the target is not to build or promote a product library.
Material facts are needed for:

- cost-side statistics;
- budget and plan comparison;
- project management control.

Therefore the business control dimension is `sc.material.catalog`, not
`product.product`.

Current coverage report:

- `artifacts/migration/scbs_stock_in_material_catalog_coverage_report_v1.md`
- `artifacts/migration/scbs_stock_in_material_mapping_workbook_v1.md`
- 1658 stock-in material text groups;
- 1641 distinct legacy material IDs;
- 1463 catalog-ready groups by legacy ID after bootstrap;
- 128 exact text candidates, amount 5,452,447.77;
- 58 name/spec candidates, amount 5,293,410.42;
- 9 missing legacy material ID groups, amount 2,238,454.00;
- 9 rows without legacy material ID, amount 2,238,454.00.

Material review batches:

| Batch | Rows | Amount | Meaning |
| --- | ---: | ---: | --- |
| `01_manual_material_identity_required` | 9 | 2,238,454.00 | no SCBS material ID; needs manual material identity |
| `02_confirm_exact_text_catalog_or_create_new` | 28 | 3,812,618.16 | exact text candidates; confirm or create new |
| `03_review_name_spec_catalog_or_create_new` | 58 | 5,293,410.42 | name/spec candidates; unit differs or ambiguous |
| `04_create_or_map_material_catalog_high_amount` | 158 | 60,110,682.76 | no candidate and high amount; prioritize creation/mapping |
| `05_create_or_map_material_catalog_remaining` | 1405 | 18,999,708.83 | remaining no-candidate rows |

Operational implication:

- Do not run historical material promotion into `product.template` /
  `product.product` for SCBS stock-in acceptance.
- If an existing formal line model still requires `product_id`, the existing
  system-default material may only be used as a technical placeholder.
- The source of truth for SCBS material identity must remain
  `material_catalog_id` plus source table/header/line IDs.
- This is now aligned with the broader construction material deproductization
  policy in
  `docs/migration_alignment/construction_material_deproductization_audit_v1.md`.
- Material plan has been refactored as the first business flow:
  `material_catalog_id` is the visible material identity, and `product_id` is a
  hidden technical placeholder only.
- Material purchase request and material RFQ line entry have also been shifted
  to visible `material_catalog_id`, with `product_id` kept hidden as technical
  placeholder. Plan-to-RFQ material catalog propagation has been smoke-tested.
- Material acceptance, inbound, and outbound line entry now use visible
  `material_catalog_id`; `product_id` remains hidden technical placeholder.
  Acceptance-to-inbound material catalog propagation has been smoke-tested, and
  inbound material summaries now prefer material catalog names.
- Material settlement line entry/report has also shifted to material catalog
  identity; "按材料" grouping now groups by `material_catalog_id` instead of
  product.
- Turnover material rental plan/order/settlement lines now use visible
  `material_catalog_id` and preserve material name/spec/unit as business fact
  text; rental no longer exposes product as the material identity.

System import status:

- Model: `sc.legacy.scbs.material.map`
- Import result:
  `artifacts/migration/scbs_stock_in_material_map_import_result_v1.json`
- Bootstrap result:
  `artifacts/migration/scbs_material_catalog_bootstrap_result_v1.json`
- Rollback target list for bootstrap-created catalogs:
  `artifacts/migration/scbs_material_catalog_bootstrap_rollback_targets_v1.csv`
- Preview:
  `artifacts/migration/scbs_stock_in_material_map_import_preview_v1.csv`
- Imported rows: 1657
- Confirmed rows: 1649
- Conflict rows: 8, amount 2,238,454.00
- Created target material catalogs: 1455
- Linked existing target catalogs by business key: 108
- Confirmed existing target links: 86
- Skipped rows: 1 empty zero-amount material group

## Current User Data Import Gate

After business entity bootstrap, project fact bootstrap, partner fact bootstrap, and material bootstrap:

- staged facts: 15,223 rows, amount/balance signal 2,020,311,261.45;
- active projection pool: 15,190 rows, amount signal 2,012,171,862.45;
- inactive audit residuals: 33 rows, amount signal 8,139,399.00;
- blocked rows: 0;
- projection-ready rows: 15,190;
- staging-ready rows: 0;
- conflict rows: 0.

Projection-ready rows are not equal to full formal import readiness:

| Fact Family | Gate | Rows | Amount | Meaning |
| --- | --- | ---: | ---: | --- |
| fund daily | projection_ready | 3,798 | 1,290,762,428.64 | enterprise fund daily can attach to confirmed business entity |
| payment | projection_ready | 9,107 | 359,251,657.39 | dimension mapping ready; duplicate policy still required before formal payment write |
| supplier_contract | projection_ready | 1,585 | 273,565,406.25 | dimension mapping ready; document-number review still required before formal contract write |
| stock_in | projection_ready | 700 | 88,592,370.17 | dimension mapping ready; header-line mismatch review remains for formal stock projection policy |

Formal projection execution state after policy refinements:

| Fact Family | Target | Written Rows | Written Amount | Residual Rows | Residual Amount | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| fund_daily | sc.legacy.fund.daily.snapshot.fact | 3,798 | 1,290,762,428.64 | 0 | 0.00 | enterprise business documents written without project binding; summary view is grouped by business entity/date and excludes project-source rows |
| payment | sc.payment.execution + sc.legacy.payment.adjustment.fact + sc.legacy.enterprise.business.fact | 9,107 | 359,251,657.39 | 0 | 0.00 | positive project-confirmed rows written to payment execution; negative project-confirmed rows written to historical payment adjustment facts; no-project rows written to enterprise facts |
| supplier_contract | sc.general.contract + sc.legacy.enterprise.business.fact | 1,585 | 273,565,406.25 | 0 | 0.00 | project-confirmed rows written to general contracts; no-project rows written to enterprise facts |
| stock_in | sc.material.inbound | 697 headers / 2,173 lines | 88,601,224.17 | 3 zero-amount headers | 0.00 | operational headers written; no-line zero headers remain audit residual |

Unified residual register:

| Category | Rows | Amount | Handling |
| --- | ---: | ---: | --- |
| payment_no_project | 0 | 0.00 | written to `sc.legacy.enterprise.business.fact`; no longer residual |
| payment_negative_project_confirmed | 0 | 0.00 | written to `sc.legacy.payment.adjustment.fact`; no longer residual |
| supplier_contract_no_project | 0 | 0.00 | written to `sc.legacy.enterprise.business.fact`; no longer residual |
| stock_in_zero_amount_no_line | 3 | 0.00 | zero-amount no-line headers; do not create empty inbound docs |
| inactive_non_business_or_dirty_residual | 33 | 8,139,399.00 | archived from projection pool; not business write |

Closure reconciliation:

| Fact Family | Source Rows | Source Amount | Formal Rows | Formal Amount | Residual Rows | Residual Amount | Delta | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| payment | 9,107 | 359,251,657.39 | 9,107 | 359,251,657.39 | 0 | 0.00 | -0.00 | PASS_STRICT_AMOUNT_CLOSED |
| supplier_contract | 1,585 | 273,565,406.25 | 1,585 | 273,565,406.25 | 0 | 0.00 | 0.00 | PASS_STRICT_AMOUNT_CLOSED |
| stock_in | 700 | 88,592,370.17 | 697 | 88,601,224.17 | 3 | 0.00 | -8,854.00 | PASS_WITH_HEADER_LINE_POLICY_DELTA |
| fund_daily | 3,798 | 1,290,762,428.64 | 3,798 | 1,290,762,428.64 | 0 | 0.00 | 0.00 | PASS_ENTERPRISE_DOCUMENT_CLOSED |
| inactive_residual | 33 | 8,139,399.00 | 0 | 0.00 | 33 | 8,139,399.00 | 0.00 | PASS_ARCHIVED_RESIDUAL_REGISTERED |

Closure guard checks:

- SCBS formal non-direct rows: payment=0, payment_adjustment=0, enterprise_fact=0, contract=0, stock_in=0;
- SCBS material mappings not confirmed: 0;
- SCBS enterprise fund daily project-bound rows: 0;
- SCBS enterprise fund daily missing business entity rows: 0;
- enterprise fund daily summary rows: 3,750; summarized source row count: 3,798; summary project-bound rows: 0;
- source duplicate checks: payment=0, payment_adjustment=0, enterprise_fact=0, contract=0, stock_in=0, fund_daily=0;
- stock-in delta is expected: formal amount follows legacy line facts while
  source staging amount is the header signal.

Release acceptance:

| Mode | Database | Status | Meaning |
| --- | --- | --- | --- |
| strict | `sc_prod_sim` | PASS | loaded SCBS simulation data is fully reconciled and guard-checked |
| empty | `sc_empty_scbs_accept_20260505_1033` | PASS | fresh install has SCBS carrier models but no imported SCBS data pollution |

Strict release acceptance checks include:

- payment, contract, stock-in, and fund-daily source counts and amounts;
- formal write totals by target carrier;
- operation strategy non-direct guards;
- fund daily no-project and all-entity guards;
- material mapping confirmation guard;
- source duplicate guards for payment, payment adjustment, enterprise fact,
  contract, stock-in, and fund daily;
- residual policy guards for 3 zero-amount no-line stock headers and 33
  inactive non-business/dirty rows.

Empty-database acceptance checks include:

- `sc.legacy.scbs.fact.staging` model installed;
- `sc.legacy.payment.adjustment.fact` model installed;
- `sc.legacy.enterprise.business.fact` model installed;
- `sc.legacy.fund.daily.snapshot.fact` model installed;
- `sc.material.catalog` model installed;
- SCBS staging rows = 0;
- SCBS payment adjustment rows = 0;
- SCBS enterprise fact rows = 0;
- SCBS fund daily rows = 0.

Residual business-scope classification:

| Fact Family | Classification | Rows | Amount | Meaning |
| --- | --- | ---: | ---: | --- |
| payment | legacy_department_or_business_bucket_only | 1,111 | 38,167,981.03 | legacy `bm` has department/business bucket text, but explicit project fields are empty |
| payment | counterparty_or_remark_only | 4 | 970,900.00 | only counterparty or remark evidence exists |
| supplier_contract | legacy_business_entity_or_department_only | 9 | 623,832.00 | business entity/department text exists, but no project anchor |

This supports the current policy: do not force residual rows into project
documents from legacy department/business-bucket labels alone.

Negative payment semantics:

| Classification | Rows | Amount | Meaning |
| --- | ---: | ---: | --- |
| refund_or_return | 67 | -4,797,262.89 | text indicates refund, return, repayment, or tax refund |
| account_or_internal_adjustment | 44 | -27,710,200.00 | text indicates account transfer, adjustment, write-off, or deposit adjustment |
| negative_without_text_semantics | 107 | -31,195,539.43 | no reliable text semantics found in current source fields |

These rows have project anchors but cannot be written to positive payment
execution. They have been written to `sc.legacy.payment.adjustment.fact` as
historical refund/adjustment facts, preserving the source amount and
classification for future review.

Projection plan artifacts:

- `artifacts/migration/scbs_formal_projection_plan_v1.csv`
- `artifacts/migration/scbs_formal_projection_plan_v1.md`
- `artifacts/migration/scbs_formal_projection_plan_result_v1.json`
- `artifacts/migration/scbs_formal_projection_policy_preflight_v1.csv`
- `artifacts/migration/scbs_formal_projection_policy_preflight_v1.md`
- `artifacts/migration/scbs_formal_projection_policy_preflight_result_v1.json`
- `artifacts/migration/scbs_formal_projection_stock_in_mismatch_examples_v1.csv`
- `artifacts/migration/scbs_formal_projection_stock_in_missing_line_examples_v1.csv`
- `artifacts/migration/scbs_project_bucket_policy_report_v1.md`
- `artifacts/migration/scbs_project_bucket_policy_summary_v1.csv`
- `artifacts/migration/scbs_project_bucket_policy_by_entity_v1.csv`
- `artifacts/migration/scbs_project_bucket_policy_top_partners_v1.csv`
- `artifacts/migration/scbs_project_bucket_bootstrap_plan_v1.csv`
- `artifacts/migration/scbs_project_bucket_bootstrap_result_v1.json`
- `artifacts/migration/scbs_project_operation_strategy_backfill_plan_v1.csv`
- `artifacts/migration/scbs_project_operation_strategy_backfill_result_v1.json`
- `artifacts/migration/scbs_operation_strategy_policy_refresh_plan_v1.csv`
- `artifacts/migration/scbs_operation_strategy_policy_refresh_result_v1.json`
- `artifacts/migration/scbs_payment_contract_projection_plan_v1.csv`
- `artifacts/migration/scbs_payment_contract_projection_residual_v1.csv`
- `artifacts/migration/scbs_payment_contract_projection_result_v1.json`
- `artifacts/migration/scbs_stock_in_legacy_lines_v1.csv`
- `artifacts/migration/scbs_stock_in_line_export_result_v1.json`
- `artifacts/migration/scbs_stock_in_projection_plan_v1.csv`
- `artifacts/migration/scbs_stock_in_projection_residual_v1.csv`
- `artifacts/migration/scbs_stock_in_projection_result_v1.json`
- `artifacts/migration/scbs_fund_daily_source_v1.csv`
- `artifacts/migration/scbs_fund_daily_source_export_result_v1.json`
- `artifacts/migration/scbs_fund_daily_enterprise_projection_plan_v1.csv`
- `artifacts/migration/scbs_fund_daily_enterprise_projection_residual_v1.csv`
- `artifacts/migration/scbs_fund_daily_enterprise_projection_result_v1.json`
- `artifacts/migration/scbs_residual_business_scope_report_v1.md`
- `artifacts/migration/scbs_residual_business_scope_summary_v1.csv`
- `artifacts/migration/scbs_residual_business_scope_bucket_v1.csv`
- `artifacts/migration/scbs_negative_payment_semantics_report_v1.md`
- `artifacts/migration/scbs_negative_payment_semantics_summary_v1.csv`
- `artifacts/migration/scbs_negative_payment_semantics_detail_v1.csv`
- `artifacts/migration/scbs_negative_payment_adjustment_projection_plan_v1.csv`
- `artifacts/migration/scbs_negative_payment_adjustment_projection_result_v1.json`
- `artifacts/migration/scbs_enterprise_no_project_fact_projection_plan_v1.csv`
- `artifacts/migration/scbs_enterprise_no_project_fact_projection_result_v1.json`
- `artifacts/migration/scbs_unified_residual_register_v1.csv`
- `artifacts/migration/scbs_unified_residual_summary_v1.csv`
- `artifacts/migration/scbs_unified_residual_register_v1.md`
- `artifacts/migration/scbs_unified_residual_register_result_v1.json`
- `artifacts/migration/scbs_migration_closure_reconciliation_v1.csv`
- `artifacts/migration/scbs_migration_closure_reconciliation_v1.md`
- `artifacts/migration/scbs_migration_closure_reconciliation_result_v1.json`
- `artifacts/migration/scbs_release_acceptance_strict_v1.md`
- `artifacts/migration/scbs_release_acceptance_strict_result_v1.json`
- `artifacts/migration/scbs_release_acceptance_empty_v1.md`
- `artifacts/migration/scbs_release_acceptance_empty_result_v1.json`
- `artifacts/migration/scbs_direct_project_normalize_plan_v1.csv`
- `artifacts/migration/scbs_direct_project_normalize_result_v1.json`
- `artifacts/migration/scbs_direct_project_normalize_rollback_v1.csv`
- `artifacts/migration/scbs_residual_project_clue_summary_v1.csv`
- `artifacts/migration/scbs_residual_project_clue_grouping_v1.csv`
- `artifacts/migration/scbs_residual_project_clue_payment_examples_v1.csv`
- `artifacts/migration/scbs_residual_project_clue_contract_examples_v1.csv`

Project-bucket policy report (superseded by direct-project recovery for
stock-in and by no-project residual policy for payment/contract):

| Fact Family | Projectless Rows | Projectless Amount | Entity Coverage |
| --- | ---: | ---: | --- |
| payment | 2,608 | 110,459,119.00 | 1,493 rows have entity; 1,115 rows lack entity |
| supplier_contract | 440 | 96,955,707.99 | 431 rows have entity; 9 rows lack entity |
| stock_in | 345 | 50,030,375.39 | 345 rows have entity |

Recommended project-bucket policy:

- Do not merge no-project facts into existing real projects without source evidence.
- Current execution does not create remaining bucket projects.
- Rows with no project source evidence remain residual/reporting-only until
  entity and project evidence is found.

Dry-run bucket bootstrap:

- candidate bucket projects: 21;
- rows that would be linked after bucket creation: 2,269;
- entity-less projectless rows that remain excluded from bucket creation:
  1,124 rows / 39,762,713.03;
- bucket bootstrap was applied only as an intermediate staging fix, then
  normalized after source evidence was recovered.

Direct project normalization:

- 21 provisional bucket projects were matched to SCBS `BASE_SYSTEM_PROJECT`
  rows by `legacy_xmid`;
- original source evidence: `PROJECT_ENV=正式项目`, `NATURE=自营`,
  `COMPANYNAME=公司直属`;
- normalized rows: 2,269 facts / 217,682,489.35;
- remaining provisional bucket projects: 0.

Residual project clue mining before enterprise carrier write:

- no-project payment facts: 1,115 rows / 39,138,881.03;
- no-project supplier-contract facts: 9 rows / 623,832.00;
- rows with strong project clue (`XMID/XMMC/GCMC` or equivalent): 0;
- payment department/cost-center clue: 1,104 rows / 38,115,934.03 have
  `f_BM=四川保盛联营项目`;
- these facts must not be forced into the direct-project set and are now
  written to `sc.legacy.enterprise.business.fact`.

Operation-strategy backfill:

- confirmed SCBS fact-bearing projects after policy refresh: 62 `公司直营`;
- prior-default existing mapped projects corrected from `联营项目` to `公司直营`:
  3;
- confirmed SCBS project facts now under `公司直营`: 10,268 rows /
  681,646,720.78;
- SCBS formal payment rows now under `公司直营`: 9,107 rows /
  359,251,657.39, including 7,774 positive payment executions, 218
  historical payment adjustment facts, and 1,115 enterprise no-project facts;
- SCBS formal supplier-contract rows now under `公司直营`: 1,585 rows /
  273,565,406.25, including 1,576 project contracts and 9 enterprise
  no-project facts.
- SCBS formal material inbound rows now under `公司直营`: 697 headers /
  2,173 lines / 88,601,224.17.

Excluded audit residuals:

| Gate Before Exclusion | Rows | Amount | Meaning |
| --- | ---: | ---: | --- |
| conflict/staging_ready | 33 | 8,139,399.00 | test values, non-real project labels, and no-real-dimension residuals retained inactive |

Current dimension state:

| Dimension | Confirmed | Candidate | Conflict | Ignored | Target Link State |
| --- | ---: | ---: | ---: | ---: | --- |
| business entity | 39 | 0 | 2 | 0 | 27 new entities created, 12 existing targets confirmed |
| project | 41 | 0 | 2 | 1 | 38 SCBS business-fact projects created; 1 exact target and 2 strong single candidates confirmed |
| partner | 858 | 121 | 1 | 0 | 629 SCBS historical partners created; 229 single-target exact-name mappings confirmed |
| material catalog | 1657 | 0 | 0 | 0 | 1455 catalogs created by initial bootstrap; missing-ID groups later accepted as business facts with 6 new catalogs and 2 existing links |

Refreshed residual decision workload after business-fact bootstrap:

- Active decision workbook rows: 0
- Active split decision batches: 0
- Archived residual plan:
  `artifacts/migration/scbs_residual_fact_exclusion_plan_v1.csv`
- Archived residual result:
  `artifacts/migration/scbs_residual_fact_exclusion_result_v1.json`

Project remaining focus file:

- `artifacts/migration/scbs_project_remaining_decision_focus_v1.csv`
- superseded by project fact bootstrap because the user confirmed SCBS project
  names as project-level business facts;
- bootstrap result:
  `artifacts/migration/scbs_project_fact_bootstrap_result_v1.json`;
- rollback target list:
  `artifacts/migration/scbs_project_fact_bootstrap_rollback_targets_v1.csv`.

## Safe Integration Rule

No SCBS project-level fact should overwrite existing company-level records.

Formal projection must be source-tagged with:

- source domain `SCBS`;
- source table;
- legacy header ID and, where applicable, legacy line ID;
- import batch;
- confirmed business entity, project, partner, and material-catalog mappings.

Reports that combine existing company-level data and SCBS project-level data
must explicitly classify SCBS as drill-down detail, supplement, or independent
fact source.
