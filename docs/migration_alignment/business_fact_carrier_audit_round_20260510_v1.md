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

## Remaining Priority

The next carrier work should continue from high-signal remaining candidates,
with priority on objective amount/project/partner facts:

| Priority | Family | Examples |
| --- | --- | --- |
| 1 | project settlement | `T_ProjectContract_In`, `XMGL_HTGL_XMJSSQ`, `T_Project_GCQZD`, `XM_SBBF` |
| 2 | bid/tender residual | `WS_HTGL_ZBHT`, `P_ZTB_GCXXGL`, `CGPT_T_Base_ZBXX*`, `BGGL_ZTBJHT_TBBM_TBBMFSQ` |
| 3 | supplier/payment residual | `T_FK_Supplier_SD`, `T_HTGL_HTBG`, `T_CollectionPlan_New` |
| 4 | labor/equipment/material residual | `GLFY_*`, `LW_*`, `T_ZL_*`, `A_SCBS_*` |

Do not force old records into new customer/supplier classifications during this
phase. Each source table should be either carried into a neutral or specialized
runtime fact carrier, or explicitly excluded with evidence.
