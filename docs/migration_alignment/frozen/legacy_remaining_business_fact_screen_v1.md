# Legacy Remaining Business Fact Screen v1

Status: `PASS`

This is a read-only screen after the current migration asset bus.

## Result

- raw workflow rows: `163245`
- covered rows: `118236`
- remaining rows: `45009`
- DB writes: `0`
- Odoo shell: `false`

## Remaining Families

| Family | Rows |
|---|---:|
| unknown_or_unmapped_family | 28784 |
| payment_request_residual | 5948 |
| document_admin_residual | 3754 |
| attendance_hr_residual | 2709 |
| supplier_or_purchase_residual | 2607 |
| tender_registration_residual | 1168 |
| fund_daily_or_loan_residual | 39 |

## Covered By Lane

| Lane | Rows |
|---|---:|
| outflow_request | 45693 |
| legacy_expense_deposit | 20216 |
| supplier_contract | 13281 |
| legacy_receipt_income | 10375 |
| receipt | 8556 |
| legacy_invoice_tax | 6389 |
| actual_outflow | 6088 |
| contract | 6084 |
| legacy_fund_daily_snapshot | 993 |
| legacy_financing_loan | 561 |

## Top Remaining Source Tables

| Source table | Rows |
|---|---:|
| C_JXXP_ZYFPJJD | 19707 |
| C_ZFSQGL | 4779 |
| C_JFHKLR_TH_ZCDF | 2550 |
| T_KK_SJTHB | 2387 |
| T_Base_CooperatCompany | 2055 |
| BGGL_XZD_YZSYSPB | 1584 |
| BGGL_TZXX_WJPYCJ | 1476 |
| P_ZTB_GCBMGL | 1114 |
| BGGL_KQTJ_YTWC | 1109 |
| CWGL_FYBX | 934 |
| BGGL_HBZJ_XZD_QJXJSPB | 909 |
| C_ZJGL_GCKZF | 858 |
| SGZL_RZRJ | 694 |
| BGGL_XZ_JXDJ_ZB | 691 |
| T_GYSHT_INFO | 460 |
| C_JXXP_XXKPDJ | 350 |
| ZJGL_BZJGL_Pay_FBZJ | 341 |
| T_FK_Supplier | 311 |
| ZJGL_WJZ_WJZDJB | 310 |
| ZJGL_BZJGL_Branch_SBZJTH | 245 |
| BGGL_XZ_GZ | 233 |
| C_JXXP_DKDJ_New | 213 |
| BGGL_TZXX_HY | 205 |
| T_ProjectContract_Out | 156 |
| C_JFHKLR | 136 |
| ZJGL_SZQR_DKQRB | 134 |
| GLFY_XMFYBXD | 134 |
| BGGL_XZ_BZ | 117 |
| BGGL_KQTJ_WDK_New | 97 |
| T_CGHT_INFO | 92 |

## Top Remaining Template Business Names

| Template business | Rows |
|---|---:|
| 进项上报 | 19707 |
| 支付申请 | 4779 |
| 自筹垫付退回 | 2550 |
| 项目扣款实缴退回 | 2387 |
| 一般供应商 | 2055 |
| 印章使用审批表 | 1584 |
| 文件批阅承办笺（新） | 1357 |
| 投标报名管理 | 1114 |
| 报销申请 | 934 |
| 请假/休假审批表 | 909 |
| 工程款支付审批 | 858 |
| 资料图片管理 | 694 |
| 绩效登记单 | 691 |
| 外出申请 | 645 |
| 外出申请（新） | 464 |
| 销项开票登记 | 350 |
| 付保证金 | 341 |
| 供货商材料合同（专票） | 323 |
| 往来单位付款 | 311 |
| 外经证登记 | 310 |
| 收保证金退回 | 245 |
| 抵扣登记 | 213 |
| 会议 | 205 |
| 工资登记 | 158 |
| 供货商材料合同 | 137 |
| 到款确认表 | 134 |
| 项目费用报销单 | 134 |
| 外部合同管理(新) | 133 |
| 工程款收入 | 125 |
| 文件批阅承办笺 | 119 |

## Next lane recommendation

- lane: `payment_request_residual`
- remaining rows: `5948`
- top source table: `C_ZFSQGL`
- top source table rows: `4779`
- reason: largest remaining classified business family after current asset bus coverage

## Boundary

This report is a prioritization map. It does not prove each remaining row is loadable.
The next lane still needs direct source-table completeness screening before model or XML work.
