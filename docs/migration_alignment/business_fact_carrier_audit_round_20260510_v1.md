# Business Fact Carrier Audit Round 2026-05-10 v1

Status: `in_progress`

Database: `sc_acceptance_audit_20260510`

Principle: migrate objective legacy business facts first. User-facing
classification, projection, menu, and report alignment must follow the fact
carrier audit, not replace it.

## Current Round

This round continued from the company operation summary fact supplement and
moved to full legacy fact carrier closure.

Full legacy scan before this round:

| Metric | Count |
| --- | ---: |
| non-empty legacy tables | 1128 |
| candidate fact tables | 347 |
| candidate fact rows | 79525 |
| effective fact candidate tables | 150 |
| effective fact candidate rows | 19164 |
| secondary fact candidate tables | 189 |
| secondary fact candidate rows | 37364 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_current.json`

## Facts Confirmed Carried

| Source fact family | Legacy source | Runtime carrier | Evidence |
| --- | --- | --- | --- |
| 印章使用审批 | `BGGL_XZD_YZSYSPB`, `BGGL_QSJRW_GZQS` | `sc.office.admin.document` | `1565 + 13` rows in audit DB |
| 请假/休假审批 | `BGGL_HBZJ_XZD_QJXJSPB` | `sc.office.admin.document` | `347` rows in audit DB |
| 社保登记 | `BGGL_XZ_JXDJ_ZB`, `BGGL_XZ_JXDJ` | `sc.hr.payroll.document` | `2517` replayed rows, `1908` active |
| 投标报名主事实 | `P_ZTB_GCBMGL` | `sc.legacy.tender.registration.fact` | `2848` rows, `2829` active |
| 项目结算/合同残余事实 | `T_ProjectContract_In`, `XMGL_HTGL_XMJSSQ`, `T_Project_GCQZD`, `XM_SBBF`, `T_ProjectContract_Process`, `T_ProjectContract_Out_CB_BZJ` | `sc.legacy.business.fact.residual` | `74` rows, `74` active |
| 投标残余事实 | `P_ZTB_GCXXGL`, `WS_HTGL_ZBHT`, `CGPT_T_Base_ZBXX`, `CGPT_T_Base_ZBXX_CB`, `BGGL_ZTBJHT_TBBM_TBBMFSQ`, `WS_ZBJGL_ZBJ`, `WS_ZBJGL_BZJ`, `WS_BDGL_TZEGL` | `sc.legacy.business.fact.residual` | `169` rows, `162` active |
| 供应商/付款残余事实 | `T_FK_Supplier_SD`, `T_HTGL_HTBG`, `T_CollectionPlan_New`, `T_GYSHT_INFO_Ext_XAKW`, `T_CGHT_CGDD`, `T_CG_CGDD`, `T_JH_CGJH`, `T_ZJZC_DB` | `sc.legacy.business.fact.residual` | `24` rows, `22` active |
| 劳务/设备/材料残余事实 | `GLFY_*`, `LW_*`, `SGGL_FBGL_*`, `T_ZL_*`, `A_SCBS_*`, `YT_JGZS_*`, `ZYJX_*` selected candidate tables | `sc.legacy.business.fact.residual` | `5562` rows, `5558` active |
| 剩余有效事实候选 | all remaining `candidate_effective_business_fact` tables from the latest scan | `sc.legacy.business.fact.residual` | `12093` rows, `12057` active |
| 二级/人工筛查候选残余事实 | all remaining `candidate_secondary_business_fact` and `candidate_needs_manual_screen` tables from the latest scan | `sc.legacy.business.fact.residual` | `56833` rows, `56813` active |

Tender registration replay evidence:

| Metric | Value |
| --- | ---: |
| input rows | 2848 |
| active rows | 2829 |
| project linked rows | 2848 |
| guarantee amount sum | 23883974.00 |
| document fee amount sum | 0.00 |

Runtime query:

```sql
SELECT source_table,
       count(*),
       count(*) FILTER (WHERE active),
       round(sum(guarantee_amount)::numeric, 2),
       count(*) FILTER (WHERE project_id IS NOT NULL)
FROM sc_legacy_tender_registration_fact
GROUP BY source_table;
```

Result:

| source_table | rows | active rows | guarantee amount | project linked |
| --- | ---: | ---: | ---: | ---: |
| `P_ZTB_GCBMGL` | 2848 | 2829 | 23883974.00 | 2848 |

Project settlement residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 6 |
| input rows | 74 |
| active rows | 74 |
| write mismatch count | 0 |

Runtime query:

```sql
SELECT source_table,
       count(*) AS rows,
       count(*) FILTER (WHERE active) AS active_rows,
       round(sum(amount_total)::numeric, 2) AS amount_total,
       count(*) FILTER (WHERE project_legacy_id IS NOT NULL AND project_legacy_id <> '') AS with_project
FROM sc_legacy_business_fact_residual
WHERE family = 'project_settlement'
GROUP BY source_table
ORDER BY source_table;
```

Result:

| source_table | rows | active rows | amount total | with project |
| --- | ---: | ---: | ---: | ---: |
| `T_ProjectContract_In` | 4 | 4 | 0.00 | 4 |
| `T_ProjectContract_Out_CB_BZJ` | 5 | 5 | 3053466.63 | 0 |
| `T_ProjectContract_Process` | 1 | 1 | 0.00 | 1 |
| `T_Project_GCQZD` | 6 | 6 | 0.00 | 6 |
| `XMGL_HTGL_XMJSSQ` | 55 | 55 | 46796778.03 | 55 |
| `XM_SBBF` | 3 | 3 | 0.00 | 3 |

The project settlement facts are carried as original residual facts first.
Dedicated contract/settlement projection should be a later step after field
semantics are reviewed per table.

Tender residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 8 |
| input rows | 169 |
| active rows | 162 |
| write mismatch count | 0 |

Runtime query:

```sql
SELECT family,
       source_table,
       count(*) AS rows,
       count(*) FILTER (WHERE active) AS active_rows,
       round(sum(amount_total)::numeric, 2) AS amount_total
FROM sc_legacy_business_fact_residual
WHERE source_table IN (
  'P_ZTB_GCXXGL',
  'WS_HTGL_ZBHT',
  'CGPT_T_Base_ZBXX',
  'CGPT_T_Base_ZBXX_CB',
  'BGGL_ZTBJHT_TBBM_TBBMFSQ',
  'WS_ZBJGL_ZBJ',
  'WS_ZBJGL_BZJ',
  'WS_BDGL_TZEGL'
)
GROUP BY family, source_table
ORDER BY family, source_table;
```

Result:

| family | source_table | rows | active rows | amount total |
| --- | --- | ---: | ---: | ---: |
| bid_tender | `CGPT_T_Base_ZBXX` | 6 | 6 | 0.00 |
| bid_tender | `CGPT_T_Base_ZBXX_CB` | 9 | 9 | 447490.40 |
| bid_tender | `P_ZTB_GCXXGL` | 20 | 20 | 840000.00 |
| bid_tender | `WS_BDGL_TZEGL` | 3 | 3 | 0.00 |
| bid_tender | `WS_HTGL_ZBHT` | 2 | 2 | 3232344.10 |
| bid_tender | `WS_ZBJGL_BZJ` | 3 | 3 | 0.00 |
| bid_tender | `WS_ZBJGL_ZBJ` | 4 | 4 | 0.00 |
| office_admin | `BGGL_ZTBJHT_TBBM_TBBMFSQ` | 122 | 115 | 45001.25 |

These facts are carried as residual originals first. Later tender-domain
projection should decide which rows become tender projects, tender contracts,
guarantee facts, or registration-fee facts.

Supplier/payment residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 8 |
| input rows | 24 |
| active rows | 22 |
| write mismatch count | 0 |

Runtime query:

```sql
SELECT source_table,
       count(*) AS rows,
       count(*) FILTER (WHERE active) AS active_rows,
       round(sum(amount_total)::numeric, 2) AS amount_total,
       count(*) FILTER (WHERE project_legacy_id IS NOT NULL AND project_legacy_id <> '') AS with_project,
       count(*) FILTER (WHERE partner_legacy_id IS NOT NULL AND partner_legacy_id <> '') AS with_partner
FROM sc_legacy_business_fact_residual
WHERE source_table IN (
  'T_FK_Supplier_SD',
  'T_HTGL_HTBG',
  'T_CollectionPlan_New',
  'T_GYSHT_INFO_Ext_XAKW',
  'T_CGHT_CGDD',
  'T_CG_CGDD',
  'T_JH_CGJH',
  'T_ZJZC_DB'
)
GROUP BY source_table
ORDER BY source_table;
```

Result:

| source_table | rows | active rows | amount total | with project | with partner |
| --- | ---: | ---: | ---: | ---: | ---: |
| `T_CG_CGDD` | 3 | 3 | 0.00 | 3 | 0 |
| `T_CGHT_CGDD` | 4 | 4 | 0.00 | 4 | 0 |
| `T_CollectionPlan_New` | 1 | 0 | 0.00 | 1 | 0 |
| `T_FK_Supplier_SD` | 7 | 7 | 0.00 | 7 | 0 |
| `T_GYSHT_INFO_Ext_XAKW` | 1 | 1 | 0.00 | 0 | 0 |
| `T_HTGL_HTBG` | 5 | 5 | 0.00 | 5 | 0 |
| `T_JH_CGJH` | 2 | 1 | 0.00 | 2 | 0 |
| `T_ZJZC_DB` | 1 | 1 | 0.00 | 1 | 1 |

These rows are original residual carrier facts. Several tables contain supplier
or payment semantics in non-standard field names, so dedicated projection must
review each table before assigning customer/supplier or payable labels.

Labor/equipment/material residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 74 |
| input rows | 5562 |
| active rows | 5558 |
| write mismatch count | 0 |

Runtime family summary:

```sql
SELECT family,
       count(DISTINCT source_table) AS tables,
       count(*) AS rows,
       count(*) FILTER (WHERE active) AS active_rows,
       round(sum(amount_total)::numeric, 2) AS amount_total
FROM sc_legacy_business_fact_residual
WHERE family IN ('labor_subcontract','lease_equipment','material_stock','a')
GROUP BY family
ORDER BY family;
```

Result:

| family | tables | rows | active rows | heuristic amount total |
| --- | ---: | ---: | ---: | ---: |
| `a` | 9 | 104 | 104 | 525411.60 |
| `labor_subcontract` | 42 | 5147 | 5143 | 5933441.37 |
| `lease_equipment` | 15 | 237 | 237 | 21300339480.32 |
| `material_stock` | 8 | 74 | 74 | 593906.27 |

`amount_total` in residual carrier rows is a heuristic extraction from legacy
amount-like fields. It is useful for prioritization and audit spotting, but
dedicated domain projection must review field semantics before these numbers
are used as business report figures.

Remaining effective-fact residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 102 |
| input rows | 12093 |
| active rows | 12057 |
| write mismatch count | 0 |

Runtime residual carrier total:

| Metric | Value |
| --- | ---: |
| source table count | 192 |
| rows | 17841 |
| active rows | 17792 |

Top carried residual families after this batch:

| family | tables | rows | active rows |
| --- | ---: | ---: | ---: |
| `labor_subcontract` | 42 | 5147 | 5143 |
| `base` | 2 | 4919 | 4919 |
| `t` | 25 | 2615 | 2613 |
| `office_admin` | 11 | 1968 | 1937 |
| `zlgl` | 1 | 1817 | 1817 |
| `lease_equipment` | 15 | 237 | 237 |
| `dataspider` | 1 | 219 | 219 |
| `sggl` | 15 | 185 | 185 |
| `d` | 3 | 170 | 159 |

Secondary/manual-screen residual replay evidence:

| Metric | Value |
| --- | ---: |
| source table count | 150 |
| input rows | 56833 |
| active rows | 56813 |
| write mismatch count | 0 |

Runtime residual carrier total after this batch:

| Metric | Value |
| --- | ---: |
| source table count | 342 |
| rows | 74674 |
| active rows | 74605 |

Top carried residual families after this batch:

| family | tables | rows | active rows |
| --- | ---: | ---: | ---: |
| `pm` | 5 | 21773 | 21773 |
| `t` | 63 | 19166 | 19159 |
| `cgpt` | 7 | 9519 | 9519 |
| `office_admin` | 38 | 5779 | 5736 |
| `labor_subcontract` | 42 | 5147 | 5143 |
| `base` | 3 | 5044 | 5044 |
| `zlgl` | 3 | 1994 | 1994 |
| `sgbw` | 1 | 1439 | 1439 |
| `sggl` | 32 | 1172 | 1172 |
| `a` | 10 | 820 | 820 |

## Scan Baseline Correction

The full legacy scan had already listed `P_ZTB_GCBMGL` as known covered, but
the audit DB had `0` rows in `sc.legacy.tender.registration.fact` before this
round. That was a baseline-vs-runtime mismatch. The runtime carrier is now
actually populated.

The scan baseline was also updated for facts already proven in runtime:

- `BGGL_XZD_YZSYSPB`
- `BGGL_QSJRW_GZQS`
- `BGGL_HBZJ_XZD_QJXJSPB`
- `BGGL_XZ_JXDJ_ZB`
- `BGGL_XZ_JXDJ`

Full legacy scan after this correction:

| Metric | Before | After |
| --- | ---: | ---: |
| candidate fact tables | 347 | 342 |
| candidate fact rows | 79525 | 74674 |
| effective fact candidate tables | 150 | 147 |
| effective fact candidate rows | 19164 | 17199 |
| secondary fact candidate tables | 189 | 187 |
| secondary fact candidate rows | 37364 | 34478 |
| known replayed/assetized tables | 151 | 156 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_tender.json`

Full legacy scan after tender residual carrier:

| Metric | Before tender residual | After tender residual |
| --- | ---: | ---: |
| candidate fact tables | 342 | 334 |
| candidate fact rows | 74674 | 74505 |
| effective fact candidate tables | 147 | 139 |
| effective fact candidate rows | 17199 | 17030 |
| known replayed/assetized tables | 156 | 164 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_tender_residual.json`

Full legacy scan after supplier/payment residual carrier:

| Metric | Before supplier/payment residual | After supplier/payment residual |
| --- | ---: | ---: |
| candidate fact tables | 334 | 326 |
| candidate fact rows | 74505 | 74481 |
| effective fact candidate tables | 139 | 131 |
| effective fact candidate rows | 17030 | 17006 |
| known replayed/assetized tables | 164 | 172 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_supplier_payment_residual.json`

Full legacy scan after labor/equipment/material residual carrier:

| Metric | Before labor/equipment/material residual | After labor/equipment/material residual |
| --- | ---: | ---: |
| candidate fact tables | 326 | 253 |
| candidate fact rows | 74481 | 68931 |
| effective fact candidate tables | 131 | 102 |
| effective fact candidate rows | 17006 | 12093 |
| secondary fact candidate tables | 187 | 143 |
| secondary fact candidate rows | 34478 | 33841 |
| known replayed/assetized tables | 172 | 245 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_labor_equipment_material_residual.json`

Full legacy scan after remaining effective residual carrier:

| Metric | Before remaining effective residual | After remaining effective residual |
| --- | ---: | ---: |
| candidate fact tables | 253 | 150 |
| candidate fact rows | 68931 | 56833 |
| effective fact candidate tables | 102 | 0 |
| effective fact candidate rows | 12093 | 0 |
| secondary fact candidate tables | 143 | 142 |
| secondary fact candidate rows | 33841 | 33836 |
| known replayed/assetized tables | 245 | 348 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_effective_residual.json`

Full legacy scan after secondary/manual-screen residual carrier:

| Metric | Before secondary/manual residual | After secondary/manual residual |
| --- | ---: | ---: |
| candidate fact tables | 150 | 0 |
| candidate fact rows | 56833 | 0 |
| effective fact candidate tables | 0 | 0 |
| effective fact candidate rows | 0 | 0 |
| secondary fact candidate tables | 142 | 0 |
| secondary fact candidate rows | 33836 | 0 |
| manual-screen candidate tables | 8 | 0 |
| manual-screen candidate rows | 22997 | 0 |
| known replayed/assetized tables | 348 | 498 |

Artifact:

`artifacts/migration/business_fact_upgrade/current_audit/legacy_db_full_business_fact_loss_scan_20260510_after_secondary_manual_residual.json`

Under the current full-scan rules, no legacy table remains classified as a
candidate business fact without a runtime carrier. This means the current
objective fact-carrier pass is closed at original-data level. It does not mean
every residual row has already been semantically projected into a dedicated
new-system business model.

## Semantic Projection Batch A

After carrier closure, the first semantic projection batch focused on a source
pair with strong business certainty:

| Legacy source | Target model | Result |
| --- | --- | --- |
| `A_SCBS_CLRKD` + `A_SCBS_CLRKD_CB` | `sc.material.inbound` + `sc.material.inbound.line` | `33` received inbound documents, `44` lines, `539339.12` amount |

Projection policy:

- use the legacy header table for document number, inbound date, project,
  supplier, creator, and header evidence;
- use the already carried `A_SCBS_CLRKD_CB` residual rows for material name,
  spec, unit, quantity, and line amount;
- compute target unit price as `legacy line amount / quantity`, so formal
  totals follow source facts instead of recalculating from rounded legacy unit
  price;
- block rows without a project anchor instead of assigning a default project.

Runtime verification:

```sql
SELECT count(*) AS headers,
       round(sum(amount_total)::numeric, 2) AS amount
FROM sc_material_inbound
WHERE legacy_fact_model = 'legacy.main.A_SCBS_CLRKD';

SELECT count(*) AS lines,
       round(sum(amount)::numeric, 2) AS amount
FROM sc_material_inbound_line l
JOIN sc_material_inbound h ON h.id = l.inbound_id
WHERE h.legacy_fact_model = 'legacy.main.A_SCBS_CLRKD';
```

Result:

| Target | Rows | Amount |
| --- | ---: | ---: |
| `sc.material.inbound` | 33 | 539339.12 |
| `sc.material.inbound.line` | 44 | 539339.12 |

Projection residuals:

| Legacy document | Project legacy id | Amount | Reason |
| --- | --- | ---: | --- |
| `CLRKD-20220301-001` | `7a7f8b5476a34a74ad907808839a9c89` | 27092.80 | `missing_project_anchor` |
| `CLRKD-20220226-001` | `7a7f8b5476a34a74ad907808839a9c89` | 360.00 | `missing_project_anchor` |

Artifacts:

- `artifacts/migration/legacy_a_scbs_material_inbound_headers_v1.csv`
- `artifacts/migration/legacy_a_scbs_material_inbound_projection_plan_v1.csv`
- `artifacts/migration/legacy_a_scbs_material_inbound_projection_residual_v1.csv`
- `artifacts/migration/legacy_a_scbs_material_inbound_projection_result_v1.json`

## Semantic Projection Batch B

The next projection batch covered the matching material outbound source pair:

| Legacy source | Target model | Result |
| --- | --- | --- |
| `A_SCBS_CLCKD` + `A_SCBS_CLCKD_CB` | `sc.material.outbound` + `sc.material.outbound.line` | `1` issued outbound document, `1` line, `1` quantity |

Projection policy:

- use the legacy header table for document number, outbound date, project,
  receiver, purpose, creator, and header evidence;
- use the already carried `A_SCBS_CLCKD_CB` residual row for material name,
  spec, quantity, and line amount evidence;
- write to the formal outbound quantity workflow and keep legacy amount in
  line notes because `sc.material.outbound` does not currently carry amount
  fields;
- block rows without a project anchor. This batch had no projection residuals.

Runtime verification:

```sql
SELECT count(*) AS headers
FROM sc_material_outbound
WHERE legacy_fact_model = 'legacy.main.A_SCBS_CLCKD';

SELECT count(*) AS lines,
       sum(l.qty) AS qty
FROM sc_material_outbound_line l
JOIN sc_material_outbound h ON h.id = l.outbound_id
WHERE h.legacy_fact_model = 'legacy.main.A_SCBS_CLCKD';
```

Result:

| Target | Rows | Quantity |
| --- | ---: | ---: |
| `sc.material.outbound` | 1 | |
| `sc.material.outbound.line` | 1 | 1 |

Projected document:

| Document | Project | Receiver | Purpose | Material | Spec | Qty | Legacy amount | State |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| `CLCKD-20220225-002` | `测试001` | `得个` | `随便` | `天猫` | `20型` | 1 | 300.00 | `issued` |

Artifacts:

- `artifacts/migration/legacy_a_scbs_material_outbound_projection_plan_v1.csv`
- `artifacts/migration/legacy_a_scbs_material_outbound_projection_residual_v1.csv`
- `artifacts/migration/legacy_a_scbs_material_outbound_projection_result_v1.json`

## Semantic Projection Batch C

The next projection batch covered legacy equipment usage facts:

| Legacy source | Target model | Result |
| --- | --- | --- |
| `A_SCBS_JXD` + `A_SCBS_JXD_CB` | `sc.equipment.usage` | `37` confirmed usage records, `515.8366` usage hours |

Projection policy:

- use the legacy header table for document number, usage date, project,
  construction location, operator, creator, and header evidence;
- use `A_SCBS_JXD_CB` lines for equipment name, usage quantity/hour signal,
  unit, unit price, and amount evidence;
- write formal equipment usage records with `usage_qty = 1` and
  `usage_hours = legacy SL`, preserving original unit, unit price, amount, and
  line remark in `note`;
- keep legacy amount as evidence because `sc.equipment.usage` is an operational
  usage model and does not carry settlement amount fields;
- block rows without a project anchor.

Runtime verification:

```sql
SELECT count(*) AS rows,
       round(sum(usage_hours)::numeric, 4) AS usage_hours
FROM sc_equipment_usage
WHERE legacy_fact_model = 'legacy.main.A_SCBS_JXD_CB';
```

Result:

| Target | Rows | Usage hours | Legacy amount evidence |
| --- | ---: | ---: | ---: |
| `sc.equipment.usage` | 37 | 515.8366 | 64360.80 |

Projection residuals:

| Legacy document | Equipment | Qty | Unit | Amount | Reason |
| --- | --- | ---: | --- | ---: | --- |
| `JXD-20220303-002` | `装载机` | 8 | `10型` | 4000.00 | `missing_project_anchor` |
| `JXD-20220301-001` | `装机` | 10 | `50` | 2000.00 | `missing_project_anchor` |
| `JXD-20220228-001` | `挖机` | 10 | `60` | 1500.00 | `missing_project_anchor` |

Artifacts:

- `artifacts/migration/legacy_a_scbs_equipment_usage_projection_plan_v1.csv`
- `artifacts/migration/legacy_a_scbs_equipment_usage_projection_residual_v1.csv`
- `artifacts/migration/legacy_a_scbs_equipment_usage_projection_result_v1.json`

## Semantic Projection Batch D

The next projection batch covered legacy labor wage settlement facts:

| Legacy source | Target model | Result |
| --- | --- | --- |
| `A_SCBS_RYGZD` + `A_SCBS_RYGZD_CB` | `sc.labor.settlement` + `sc.labor.settlement.line` | `2` confirmed settlement documents, `5` lines, `63950.00` amount |

Projection policy:

- use the legacy header table for document number, settlement date, project,
  labor contractor, creator, and header evidence;
- use `A_SCBS_RYGZD_CB` lines for work content, quantity, unit, unit price,
  amount, and remarks;
- compute target unit price as `legacy line amount / quantity`, so formal
  totals follow source facts;
- require both a project anchor and a labor contractor anchor because
  `sc.labor.settlement` requires both fields. Rows missing either anchor remain
  residual facts instead of being assigned a default contractor or default
  project.

Runtime verification:

```sql
SELECT count(*) AS headers,
       round(sum(amount_total)::numeric, 2) AS amount
FROM sc_labor_settlement
WHERE legacy_fact_model = 'legacy.main.A_SCBS_RYGZD';

SELECT count(*) AS lines,
       round(sum(l.amount_total)::numeric, 2) AS amount
FROM sc_labor_settlement_line l
JOIN sc_labor_settlement h ON h.id = l.settlement_id
WHERE h.legacy_fact_model = 'legacy.main.A_SCBS_RYGZD';
```

Result:

| Target | Rows | Amount |
| --- | ---: | ---: |
| `sc.labor.settlement` | 2 | 63950.00 |
| `sc.labor.settlement.line` | 5 | 63950.00 |

Projected documents:

| Document | Project | Contractor | Amount | State |
| --- | --- | --- | ---: | --- |
| `RYGZD-20220303-001` | `德阳市旌阳区天山路（黄河路-凯江路）改造项目` | `李合贵` | 21120.00 | `confirmed` |
| `RYGZD-20220304-001` | `德阳市旌阳区天山路（黄河路-凯江路）改造项目` | `朱龙钊` | 42830.00 | `confirmed` |

Projection residuals:

| Reason | Documents | Lines | Amount |
| --- | ---: | ---: | ---: |
| `missing_project_anchor` | 3 | 6 | 14400.00 |
| `missing_labor_contractor` | 3 | 3 | 4080.00 |

Artifacts:

- `artifacts/migration/legacy_a_scbs_labor_settlement_projection_plan_v1.csv`
- `artifacts/migration/legacy_a_scbs_labor_settlement_projection_residual_v1.csv`
- `artifacts/migration/legacy_a_scbs_labor_settlement_projection_result_v1.json`

## Semantic Projection Batch E

This batch covered the remaining A_SCBS progress diary and screened the A_SCBS
expense claim source:

| Legacy source | Target model | Result |
| --- | --- | --- |
| `A_SCBS_JDRB` | `sc.construction.diary` | `1` legacy-confirmed daily report |
| `A_SCBS_FYD` + `A_SCBS_FYD_CB` | `sc.expense.claim` | blocked, `1` document / `360.00` amount lacks a project anchor |

Construction diary projection policy:

- use the legacy progress daily table for document number, date, project,
  construction unit/location, handler, progress description, creator, and
  attachment reference;
- write the target as `source_origin = legacy` and
  `state = legacy_confirmed`;
- block rows without a project anchor. This batch had no construction-diary
  residuals.

Runtime verification:

```sql
SELECT count(*) AS rows
FROM sc_construction_diary
WHERE legacy_source_model = 'legacy.main.A_SCBS_JDRB';
```

Result:

| Document | Project | Type | Construction unit | Handler | Description | State |
| --- | --- | --- | --- | --- | --- | --- |
| `JDRB-20220225-001` | `测试001` | `日报表` | `堡坎` | `思敏路` | `堡坎施工到350米` | `legacy_confirmed` |

Expense screening conclusion:

| Legacy document | Source | Target candidate | Amount | Blocking reason |
| --- | --- | --- | ---: | --- |
| `FYD-20220226-001` | `A_SCBS_FYD` + `A_SCBS_FYD_CB` | `sc.expense.claim` | 360.00 | `missing_project_anchor` |

The expense row remains carried in `sc.legacy.business.fact.residual`. It
should not be projected to `sc.expense.claim` until the old project
`7a7f8b5476a34a74ad907808839a9c89` is anchored to a target project.

Artifacts:

- `artifacts/migration/legacy_a_scbs_construction_diary_projection_plan_v1.csv`
- `artifacts/migration/legacy_a_scbs_construction_diary_projection_residual_v1.csv`
- `artifacts/migration/legacy_a_scbs_construction_diary_projection_result_v1.json`

## Semantic Projection Batch F

This batch covered legacy machine-shift facts from the equipment lease family.
The old detail table had already been carried as residual facts, but its header
table had not been present in `sc.legacy.equipment.lease.fact`. The batch first
loaded the objective `T_ZL_MachineShift` headers, then projected deterministically
matched documents into equipment settlements.

| Legacy source | Carry target | Business target | Result |
| --- | --- | --- | --- |
| `T_ZL_MachineShift` | `sc.legacy.equipment.lease.fact` | header anchor for projection | `54` headers carried, `53` active |
| `T_ZL_MachineShift` + `T_ZL_MachineShift_CB` | existing residual details | `sc.equipment.settlement` | `36` settlements / `38` lines / `29722.40` amount |

Projection policy:

- use `T_ZL_MachineShift` as the settlement header source and
  `T_ZL_MachineShift_CB` as settlement lines;
- require a target project anchor and a non-empty supplier name before writing
  `sc.equipment.settlement`;
- create or mark the supplier partner as supplier only when the old supplier
  name is explicit;
- calculate each line price from the legacy fact amount divided by legacy
  work quantity (`JE / GZSJ`) so the target total equals the old fact amount;
- keep raw line evidence in notes, including old equipment code, specification,
  work content, source unit price, source amount, work time, and remark.

Runtime verification:

| Target | Rows | Amount |
| --- | ---: | ---: |
| `sc.legacy.equipment.lease.fact` (`T_ZL_MachineShift`) | 54 headers | n/a |
| `sc.equipment.settlement` | 36 | 29722.40 |
| `sc.equipment.settlement.line` | 38 | 29722.40 |

Projection residuals:

| Reason | Headers | Amount |
| --- | ---: | ---: |
| `missing_project_anchor` | 15 | 5021.50 |
| `missing_equipment_name` | 2 | 5640.00 |
| `inactive_legacy_header` | 1 | 0.00 |

These residuals remain carried as objective facts. They should not be forced
into equipment settlement until the old project anchors or source line names
are resolved.

Artifacts:

- `artifacts/migration/legacy_t_zl_machine_shift_headers_v1.csv`
- `artifacts/migration/legacy_t_zl_machine_shift_header_adapter_result_v1.json`
- `artifacts/migration/legacy_t_zl_machine_shift_settlement_projection_plan_v1.csv`
- `artifacts/migration/legacy_t_zl_machine_shift_settlement_projection_residual_v1.csv`
- `artifacts/migration/legacy_t_zl_machine_shift_settlement_projection_result_v1.json`

## Remaining Priority

The next work should move from raw fact carrying to semantic projection and
user-facing continuation. Priority should stay evidence-based:

| Priority | Family | Examples |
| --- | --- | --- |
| 1 | labor/equipment/material specialization | residual rows already carried; next step is semantic projection |
| 2 | supplier/payment specialization | supplier/payment residual rows already carried; next step is semantic projection |
| 3 | tender/project settlement specialization | tender and project residual rows already carried; next step is specialized projection |
| 4 | secondary/manual-screen review | residual originals already carried; next step is decide whether they need dedicated models, reports, or documented exclusion from user-visible workflows |

Do not force old records into new customer/supplier classifications during this
phase. Each source table should be either carried into a neutral or specialized
runtime fact carrier, or explicitly excluded with evidence.
