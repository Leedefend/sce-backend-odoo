# SCBS Partial Business Data Current State

Date: 2026-05-05
Branch: `business-data-maintenance`

## Source Package

- Source archive: `/home/odoo/workspace/DB_BAK_SCBS.zip`
- Valid backup restored: `DB_BAK_SCBS/DB_Build_SC_BSSM_20260417053343.bak`
- Restored database: `LegacyScbs20260417`
- SQL Server backup metadata:
  - database name: `DB_Build_SC_BSSM`
  - server name: `db-103`
  - backup start: `2026-04-17 05:33:44`
  - backup finish: `2026-04-17 05:33:57`
  - compatibility level: `100`
  - collation: `Chinese_PRC_CI_AS`
- Invalid backup in archive:
  - `DB_BAK_SCBS/DB_Build_SC_BS_LY_V2_20260417050930 - ... .bak`
  - ZIP CRC is valid, but the extracted `.bak` content is all zero bytes, so it is not usable for restore.

## Restored Data Scope

The backup is a partial business-fact dataset, not a full historical replacement.

High-volume active facts observed:

| Legacy table | Domain | Active rows | Amount / balance signal |
| --- | --- | ---: | ---: |
| `T_Base_CooperatCompany` | partners / counterparties | 1906 | n/a |
| `T_FK_Supplier` | supplier payments | 9130 | 364,696,413.39 |
| `T_GYSHT_INFO` | supplier contracts | 1592 | 274,514,199.25 |
| `T_RK_RKD` | stock-in headers | 703 | 90,338,220.17 |
| `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | fund daily balances | 3798 | 1,290,762,428.64 |
| `BASE_SYSTEM_PROJECT` | legacy project/business-unit dimension | 21 active of 25 | n/a |

## New System Baseline

Current simulated production Odoo state:

- `res.company`: 1 company, `四川保盛建设集团有限公司`
- `project.project`: 785 projects
  - many projects have `company_id = False`
  - a small number, including demo data, have `company_id = 四川保盛建设集团有限公司`
- `construction.contract`: 6934 contracts
  - visible sample contracts have `company_id = 四川保盛建设集团有限公司`
- `res.partner`: 7288 total partners, 7284 active and 4 inactive
  - mostly shared partners with `company_id = False`
- `res.users`: 113 users
  - users belong to the single current company through `company_id/company_ids`

This means the target system currently has a single legal company record, but business models already carry company isolation fields. Importing legacy facts with a wrong or premature `company_id` can either hide records from users or leak records across company boundaries after multi-company is enabled.

## Legacy Company And Project Signals

The legacy schema does not expose one clean company field across all facts. It has at least two different axes:

1. Business-unit / carrier axis:
   - Usually represented by `XMID/XMMC`, `f_XMID/XMMC`, or `ProjectName`.
   - Many values are company-like names, for example:
     - `四川世旺鑫润商贸有限公司`
     - `四川翔驰恒瑞商贸有限公司`
     - `四川晟博通达商贸有限公司`
     - `德阳泰诚硕商贸有限公司`
     - `四川鑫垚建筑劳务有限公司`
     - `公司综合平台`

2. Real construction project axis:
   - Often represented by `GCMC`.
   - Values are project names, for example:
     - `旌阳区供水项目——柏隆净水厂`
     - `高新产业园配套项目（包2）`
     - `三星堆环线基础设施改造`
     - `2023年高标准农田改造提升-东美村`

`BASE_SYSTEM_PROJECT` is overloaded. Its active rows are mostly business carriers or company-like units, not normal construction projects. Distribution:

| `COMPANYID` | `COMPANYNAME` | `NATURE` | Rows | Active rows |
| --- | --- | --- | ---: | ---: |
| `2cb50a4e35174bdd98436251f688e88a` | `公司直属` | `自营` | 24 | 20 |
| `1` | `四川保盛建设集团有限公司` | empty | 1 | 1 |

Because of this, legacy `XMID` must not be blindly mapped to `project.project`.

## Field Coverage By Core Fact Table

| Source | Active rows | Carrier fields covered | Real project fields covered | Department/company fields covered |
| --- | ---: | ---: | ---: | ---: |
| `T_Base_CooperatCompany` | 1906 | `XMID/XMMC`: 1906 | n/a | n/a |
| `T_FK_Supplier` | 9130 | `f_XMID/XMMC`: 3130 | `GCMC`: 6516 | `f_BMID/f_BM`: 7026 |
| `T_GYSHT_INFO` | 1592 | `XMID/ProjectName`: 1346 | `GCMC`: 1151 | `JBBMID/JBBM`: 0 in active rows |
| `T_RK_RKD` | 703 | `XMID/f_ProjectName`: 703 | `GCMC`: 355 | `SSGSID/SSGSMC`: 0 in active rows |
| `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | 3798 | `XMID/XMMC`: 3798 | n/a | n/a |

## Current Isolation Risk

Risk level: high if data is imported directly into live business models without a mapping layer.

Observed reasons:

- The old `project` dimension contains business carriers, branch-like units, deleted test rows, and the company platform row.
- Several fact rows contain both a company-like carrier and a construction project name on the same record.
- Some facts contain department-like fields such as `f_BMID/f_BM`, but those values are not reliable company IDs.
- The new Odoo system currently has only one `res.company`, while the legacy facts imply multiple internal carriers or operating entities.
- Existing Odoo access and API contracts already propagate `company_id` and `allowed_company_ids`; therefore a later multi-company enablement would make incorrect imports visible as permission bugs or data leakage.

## Integration Position

The safe integration path is staging-first:

1. Import raw legacy facts into staging/read-only legacy models or staging tables.
2. Preserve all raw legacy keys:
   - `legacy_xmid`
   - `legacy_xmmc`
   - `legacy_gcmc`
   - `legacy_company_id`
   - `legacy_company_name`
   - `legacy_dept_id`
   - `legacy_dept_name`
   - source table and source primary key
3. Build an explicit mapping table before writing target `company_id`, `project_id`, or business document links.
4. Classify each legacy key as one of:
   - legal company
   - internal business carrier / operating unit
   - real construction project
   - department
   - counterparty
   - unknown / needs manual decision
5. Only map `company_id` after the user accepts the company isolation mapping.

## Immediate Next Iteration List

Status: implemented through staging and reconciliation for the restored slice.

1. Generate a distinct legacy-dimension matrix:
   - group by `XMID/XMMC`, `GCMC`, `f_BMID/f_BM`, `SSGSID/SSGSMC`
   - include row counts, amount totals, min/max dates, source tables
2. Compare matrix names against current Odoo:
   - `res.company`
   - `project.project`
   - `res.partner`
   - users and allowed companies
3. Mark each dimension value as:
   - exact match
   - likely match
   - new company candidate
   - project candidate
   - partner candidate
   - unknown
4. Design the staging import model and ACL:
   - readable by migration/admin users only
   - no normal business workflow writes during staging
5. After mapping approval, implement a dry-run importer:
   - no destructive updates
   - duplicate detection by source table and legacy primary key
   - report unresolved mappings before any live write

## Current Conclusion

The data is restorable and analyzable. It is not ready for direct merge into live business tables.

The blocking issue is not restore quality; it is semantic mapping and company isolation. The legacy data uses `XMID/XMMC` as a business carrier dimension and `GCMC` as a real project dimension, while the new system currently has one company and many project records. The legacy-dimension matrix, mapping support models, staging fact model, candidate imports, and reconciliation reports now exist. The remaining gate is business acceptance of the mapping rows before formal projection.

## Deeper Analysis 2026-05-05

### Carrier Dimension

The first carrier matrix shows a small number of high-weight operating carriers across multiple source tables. These are not one-off text labels; they recur across partner, payment, supplier contract, stock, and fund balance facts.

| Legacy carrier | Legacy ID | Source count | Rows | Payment amount | Contract amount | Stock amount | Fund balance |
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
| `公司综合平台` | `fb0c4133-f011-44a4-a285-59cfd30aec27` | 4 | 1048 | 0.00 | 1,719,361.15 | 0.00 | 11,488,151.00 |

There are also same-name different-ID carrier records in supplier contracts, for example `德阳泰诚硕商贸有限公司`, `德阳市博众建材销售有限公司`, `四川翔驰恒瑞商贸有限公司`, and `四川世旺鑫润商贸有限公司`. This means:

- ID-only mapping will miss same-name historical or duplicated IDs.
- Name-only mapping can merge records that may be separate legal entities or historical carriers.
- The mapping table must support many legacy IDs to one accepted target, but only after review.

### Real Project Dimension

Top `GCMC` values behave like real construction projects because they aggregate payments, supplier contracts, and stock-in facts.

| Legacy `GCMC` | Source count | Rows | Total amount | Date range |
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

Exact matching to current `project.project` is weak. In the first exact check, only `2023年高标准农田改造提升-东美村` matched exactly. Fuzzy checks found likely matches such as:

- legacy `旌阳区供水项目——柏隆净水厂` -> Odoo `德阳市旌阳区供水建设项目（柏隆净水厂）`
- legacy `二重厂西路等4条道路工程` -> Odoo `二重厂西路（华山路-衡山路）等4条路砂石工程专业分包` or a longer municipal-road project name
- legacy `齐家堰流域（高槐村-桂花村）河段水生态修复项目` -> Odoo `齐家堰水生态保护修复项目`

These must be reviewed; fuzzy matching is useful for suggestions only.

### Partner Dimension

The carrier names mostly already exist in `res.partner`, but duplicates exist in the target:

- `四川鑫垚建筑劳务有限公司`: 3 active target partners
- `德阳森元路面工程有限公司`: 2 active target partners
- `德阳泰诚硕商贸有限公司`: 2 active target partners
- other carrier names have one target partner match

The legacy partner table also contains duplicates by `DWMC`, often across multiple carriers, and many rows do not have a tax code. Therefore partner mapping needs a survivorship rule:

- prefer tax code when available and reliable
- otherwise use normalized name plus manual review
- preserve source partner ID even when merged into one target partner
- do not create additional duplicate partners until the duplicate policy is accepted

### Contract And Payment Linkage

Payment and contract facts are not naturally closed by contract ID in this slice.

| Check | Rows | Amount |
| --- | ---: | ---: |
| active payments | 9130 | 364,696,413.39 |
| active payments with `f_HTID` | 0 | n/a |
| active payments with supplier ID | 9130 | 364,696,413.39 |
| active payments whose supplier ID matches legacy partner | 9126 | 363,725,513.39 |
| active supplier contracts | 1592 | 274,514,199.25 |
| active contracts with supplier ID | 1592 | 274,514,199.25 |
| active contracts whose supplier ID matches legacy partner | 1201 | 205,705,124.92 |
| active contracts with `XMID` | 1346 | 239,701,183.10 |

Implication: supplier payment import cannot assume a direct legacy contract foreign key. If the business expects payment-to-contract reconciliation, we need the real old-system business rule, for example by supplier, project, carrier, date, bill number, invoice number, payment application number, or another workflow table.

## Business Questions Needed Before Final Design

The next analysis can continue technically, but these business facts will decide the final target design:

1. Are the high-weight carriers such as `四川世旺鑫润商贸有限公司`, `四川晟博通达商贸有限公司`, and `德阳泰诚硕商贸有限公司` legal companies, internal accounting subjects, affiliated carriers, or just project/accounting labels?
2. Should these carriers become real `res.company` records in the new system, or should they be modeled as business units / analytic dimensions under the single company `四川保盛建设集团有限公司`?
3. In the old system, when a record has both `XMID/XMMC` and `GCMC`, which one controls company isolation and which one controls project ledger reporting?
4. How does old-system supplier payment reconcile to supplier contract when `T_FK_Supplier.f_HTID` is empty in this slice?
5. Should the migration preserve the old duplicated partner rows as separate records, or merge them by tax code / normalized name?

## Staging Acceptance Progress 2026-05-05

The restored slice has now been loaded into the new system only as staging
facts. No formal business document, project, company, or partner was created by
the fact load.

Business premise clarified:

- The data already present in the new system is understood as company-level
  facts that have already entered the system.
- This SCBS slice represents real old-system project-level business facts.
- The target is not to create a separate company dataset. The target is to
  integrate project-level factual detail under the existing company/accounting
  context, while preserving the old source identity.
- Therefore the main risk is no longer only company isolation. The main
  projection risk is double counting or misalignment between existing
  company-level facts and the project-level facts being introduced.

Implemented staging scope:

| Source table | Fact family | Rows | Amount / balance signal |
| --- | --- | ---: | ---: |
| `T_FK_Supplier` | payment | 9130 | 364,696,413.39 |
| `T_GYSHT_INFO` | supplier contract | 1592 | 274,514,199.25 |
| `T_RK_RKD` | stock in | 703 | 90,338,220.17 |
| `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | fund daily | 3798 | 1,290,762,428.64 |
| total | staging facts | 15223 | 2,020,311,261.45 |

Mapping coverage after partner and dimension candidate backfills:

| Metric | Rows |
| --- | ---: |
| staged facts with business entity map | 8977 |
| staged facts with project map | 8022 |
| staged facts with partner map | 11409 |
| blocked by missing mapping | 0 |
| staging-ready only | 14672 |
| blocked by mapping conflict | 551 |
| projection-ready | 0 |

Remaining gap:

- Missing-map technical blockage is closed.
- 551 rows, amount 51,298,836.24, remain in conflict review.
- Projection-ready remains 0 because no mapping row has been business-confirmed
  yet.
- The current conflict queue is mostly partner tax-code conflicts, explicit
  non-project labels, and test or malformed legacy dimension values.
- The broader approval workbook contains 927 mapping rows that are attached to
  staged facts: 41 business-entity mappings, 44 project mappings, and 842
  partner mappings. These rows include both direct conflicts and ordinary
  candidates that must be confirmed before formal projection.
- Some legacy partner labels are not real counterparties, for example
  `管理人员工资`, `代付工资`, `工资`, `高地库房`, and `备用金`; they are now
  flagged as `review_non_counterparty_label` for business treatment instead of
  automatic partner confirmation.
- Partner target candidates have been exported for the partner decision queue.
  The report shows 50 multi-target partner mappings, 31 tax-code conflict
  mappings, and 8 non-counterparty label mappings that need explicit business
  selection or treatment before projection.
- Project target candidates have been exported for 44 project mapping rows.
  Forty-one normal project candidates include 46 target candidate rows, but
  only 21 currently have a target suggestion, so many project decisions still
  require manual business matching.
- Business-entity consolidation has been exported for 41 business-entity
  mapping rows. The largest issue is same-name different-ID carriers: 10 legacy
  names, 23 mapping rows, 8198 staged facts, and 1,762,063,393.72 amount/balance
  signal. These must be accepted as one business/accounting entity or preserved
  as separate historical carriers by business decision.
- A consolidated readiness report now tracks the decision phase:
  `artifacts/migration/scbs_mapping_decision_readiness_report_v1.md`. Current
  status is 15223 staged facts, 0 missing-map blocked rows, 551 conflict rows,
  0 projection-ready rows, 927 review rows, and 8 blank decision batches.

Projection implication:

- Confirming mappings is safe as an identity-alignment step.
- Project-level facts should not be written into the same formal measures that
  already carry company-level totals until a duplicate/reconciliation check is
  performed.
- The first formal projection should be designed as source-tagged project-level
  historical facts or reporting projection records:
  - source domain `SCBS`;
  - source table and legacy record ID;
  - existing company context;
  - confirmed business entity, project, and partner dimensions;
  - explicit import batch;
  - no overwrite of existing company-level records.
- Any report that combines old company-level data and SCBS project-level data
  must define whether SCBS is a drill-down detail, a supplement, or an
  additional independent fact source.

## Overlap Check Against Existing Formal Data

Implemented a first project-level fact overlap report:

- Script: `scripts/migration/scbs_project_fact_overlap_report.py`
- Result JSON:
  `artifacts/migration/scbs_project_fact_overlap_report_result_v1.json`
- Summary CSV:
  `artifacts/migration/scbs_project_fact_overlap_summary_v1.csv`
- Examples CSV:
  `artifacts/migration/scbs_project_fact_overlap_examples_v1.csv`
- Markdown report:
  `artifacts/migration/scbs_project_fact_overlap_report_v1.md`

Current overlap findings:

| Fact family | Source | Staged rows | Amount | Existing overlap signal | Interpretation |
| --- | --- | ---: | ---: | --- | --- |
| supplier contract | `T_GYSHT_INFO` | 1592 | 274,514,199.25 | 0 exact `legacy_contract_id` matches | old SCBS contract IDs are not already present as formal contract legacy IDs |
| supplier contract | `T_GYSHT_INFO` | 1592 | 274,514,199.25 | 4 document-number matches, 46,201.00 | small document-number overlap requires review |
| payment | `T_FK_Supplier` | 9130 | 364,696,413.39 | 0 exact project+partner+date+amount matches | no strict duplicate against payment requests using current mapped target suggestions |
| payment | `T_FK_Supplier` | 9130 | 364,696,413.39 | 214 partner+amount matches, 18,179,852.98 | possible company-level/summary overlap; needs business duplicate rule |
| stock in | `T_RK_RKD` | 703 | 90,338,220.17 | formal material inbound table has 0 rows | low formal duplicate risk after mapping confirmation |
| fund daily | `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | 3798 | 1,290,762,428.64 | no selected formal target | keep as reporting snapshot until semantics are defined |

Sample-level reading:

- The 4 supplier-contract document-number matches are not exact legacy-ID
  duplicates. The sample includes low-quality document numbers such as `111`
  and `测试`, so they are review hints only.
- The 214 payment partner+amount matches are deliberately broad. They can match
  several formal payment requests for the same partner and amount. Because
  strict project+partner+date+amount matches are 0, these rows should be
  treated as possible company-level/project-level relationship candidates, not
  as confirmed duplicates.
- The sample evidence is stored in
  `artifacts/migration/scbs_project_fact_overlap_examples_v1.csv`.

Practical conclusion:

- It is reasonable to continue mapping confirmation.
- Formal projection should still be gated by fact family:
  - supplier contracts: block exact legacy ID duplicates, review the 4 document
    matches;
  - payments: do not project until partner/project mappings are confirmed and
    the 214 partner+amount possible overlaps are assessed;
  - stock-in: can likely proceed after mapping confirmation because formal
    inbound is empty, but only after material master mapping exists;
  - fund daily: reporting snapshot only, not formal accounting/posting.
- The integration policy should preserve project-level SCBS facts with source
  identity, and then make reports decide whether they are drill-down details or
  additional facts relative to existing company-level records.

## Stock-In Detail Projection Readiness

Implemented a stock-in detail readiness report:

- Script: `scripts/migration/scbs_stock_in_detail_readiness_report.py`
- Markdown report:
  `artifacts/migration/scbs_stock_in_detail_readiness_report_v1.md`
- Summary CSV:
  `artifacts/migration/scbs_stock_in_detail_readiness_summary_v1.csv`
- Mismatch examples:
  `artifacts/migration/scbs_stock_in_detail_mismatch_examples_v1.csv`
- Top materials:
  `artifacts/migration/scbs_stock_in_top_materials_v1.csv`

Current finding:

| Check | Result |
| --- | ---: |
| active stock-in headers | 703 |
| active headers with lines | 700 |
| active stock-in lines | 2209 |
| active line amount | 90,454,874.17 |
| lines with legacy material ID | 2197 |
| lines matching legacy material catalog by `CLID` | 2197 |
| lines without catalog ID match | 12 |
| distinct legacy material IDs | 1641 |
| distinct line material names | 870 |
| target `product.template` rows | 1 |
| target formal material inbound rows | 0 |

Projection implication:

- SCBS stock-in has usable line-level detail; the old slice is not limited to
  header totals.
- Formal `sc.material.inbound` projection is still blocked because SCBS
  material catalog mapping is not accepted.
- The next safe step is material catalog mapping from `T_Base_MaterialDetail`
  plus line fields `CLID/CLMC/GGXH/DW`. This is a construction-enterprise
  material management control dimension, not a production product-library
  promotion.
- Six active headers have zero header amount but non-zero line amount. These
  should be flagged for review and should not force line facts to zero.

### Material Catalog Coverage Alignment

The current business policy is:

- Use `sc.material.catalog` for material identity, cost statistics, budget/plan
  comparison, and management control.
- Do not promote SCBS historical materials into `product.template` /
  `product.product` as part of this acceptance path.
- If an existing operational line model requires `product_id`, the system
  default material is only a technical placeholder; `material_catalog_id` stays
  the business source of truth.

Coverage report:

- Script: `scripts/migration/scbs_stock_in_material_catalog_coverage_report.py`
- Markdown report:
  `artifacts/migration/scbs_stock_in_material_catalog_coverage_report_v1.md`
- CSV:
  `artifacts/migration/scbs_stock_in_material_catalog_coverage_v1.csv`
- Mapping workbook:
  `artifacts/migration/scbs_stock_in_material_mapping_workbook_v1.md`

Current result:

| Coverage state | Material groups | Amount |
| --- | ---: | ---: |
| exact text catalog candidates | 28 | 3,812,618.16 |
| name/spec catalog candidates | 58 | 5,293,410.42 |
| catalog missing | 1563 | 79,110,391.59 |
| missing legacy material ID | 9 | 2,238,454.00 |

The target system already has 2,279,734 `sc.material.catalog` rows, but the SCBS
`CLID` values do not match target `legacy_material_id` values. This indicates a
different legacy material-ID namespace for this slice. Text candidates are
review suggestions only; they should not be treated as automatic merges.

The material mapping workbook splits the 1658 review rows into five batches:

| Batch | Rows | Amount |
| --- | ---: | ---: |
| manual material identity required | 9 | 2,238,454.00 |
| confirm exact text catalog or create new | 28 | 3,812,618.16 |
| review name/spec catalog or create new | 58 | 5,293,410.42 |
| create/map material catalog high amount | 158 | 60,110,682.76 |
| create/map material catalog remaining | 1405 | 18,999,708.83 |

The review rows have also been imported into the system review model:

- Model: `sc.legacy.scbs.material.map`
- Result JSON:
  `artifacts/migration/scbs_stock_in_material_map_import_result_v1.json`
- Current database state:
  - 1657 imported rows;
  - 1649 candidate rows, amount 88,216,420.17;
  - 8 conflict rows, amount 2,238,454.00;
  - 0 confirmed rows;
  - 1 empty zero-amount material group skipped.

Formal table counts stayed unchanged through staging and backfill:

| Model | All | Active | Inactive |
| --- | ---: | ---: | ---: |
| `res.company` | 1 | 1 | 0 |
| `project.project` | 785 | 785 | 0 |
| `res.partner` | 7288 | 7284 | 4 |
| `construction.contract` | 6934 | 6934 | 0 |
