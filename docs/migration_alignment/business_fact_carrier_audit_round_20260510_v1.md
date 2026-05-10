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

## Remaining Priority

The next carrier work should continue from high-signal remaining candidates,
with priority on objective amount/project/partner facts:

| Priority | Family | Examples |
| --- | --- | --- |
| 1 | supplier/payment residual | `T_FK_Supplier_SD`, `T_HTGL_HTBG`, `T_CollectionPlan_New` |
| 2 | labor/equipment/material residual | `GLFY_*`, `LW_*`, `T_ZL_*`, `A_SCBS_*` |
| 3 | tender specialization | tender residual rows already carried; next step is specialized projection into tender/guarantee surfaces |
| 4 | project settlement specialization | project residual rows already carried; next step is specialized projection into contract/settlement surfaces |

Do not force old records into new customer/supplier classifications during this
phase. Each source table should be either carried into a neutral or specialized
runtime fact carrier, or explicitly excluded with evidence.
