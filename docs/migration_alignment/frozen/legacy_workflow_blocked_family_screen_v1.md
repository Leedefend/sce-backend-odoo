# Legacy Workflow Blocked Family Screen v1

Status: `PASS`

This is a read-only screen for the blocked legacy approval audit rows.
It does not generate XML assets and does not weaken target-anchor requirements.

## Result

- raw rows: `163245`
- blocked rows: `83543`
- DB writes: `0`
- Odoo shell: `false`

## Top blocked business families

| Family | Rows |
|---|---:|
| expense_or_deposit_family | 26780 |
| invoice_tax_family | 25669 |
| unknown_or_unmapped_family | 11210 |
| receipt_or_income_residual | 10647 |
| payment_request_residual | 5090 |
| supplier_contract_residual | 2515 |
| document_approval_family | 1476 |
| contract_residual | 156 |

## Top Template Business Names

| Template business | Rows |
|---|---:|
| 进项上报 | 21692 |
| 到款确认表 | 6782 |
| 报销申请 | 5261 |
| 公司财务支出 | 4871 |
| 支付申请 | 4779 |
| 付保证金 | 4315 |
| 销项开票登记 | 3977 |
| 公司财务收入 | 3722 |
| 自筹垫付退回 | 2550 |
| 收保证金退回 | 2499 |
| 项目扣款实缴退回 | 2387 |
| 一般供应商 | 2055 |
| 付保证金退回 | 2033 |
| 印章使用审批表 | 1584 |
| 收保证金登记 | 1568 |
| 文件批阅承办笺（新） | 1357 |
| 付保证金退回(新) | 1296 |
| 投标报名管理 | 1114 |
| 资金日报表 | 993 |
| 请假/休假审批表 | 909 |
| 工程款支付审批 | 858 |
| 资料图片管理 | 694 |
| 绩效登记单 | 691 |
| 外出申请 | 645 |
| 销项票申请 | 520 |
| 外出申请（新） | 464 |
| 预缴税款 | 349 |
| 供货商材料合同（专票） | 323 |
| 贷款登记 | 320 |
| 往来单位付款 | 311 |

## Top Templates

| Template | Rows |
|---|---:|
| 进项上报-文楠 | 17490 |
| 审批流程 | 13183 |
| 报销申请 | 4427 |
| 到款确认表-文楠审核 | 4421 |
| 公司财务支出 | 4327 |
| 公司财务收入 | 3722 |
| 销项开票登记 | 3407 |
| 进项上报-卢燕 | 2259 |
| 政务中心保证金退回 | 2033 |
| 联营保证金退回 | 1871 |
| 付保证金流程 | 1851 |
| 缴纳政务中心保证金 | 1810 |
| 进项上报 | 1708 |
| 自筹垫付退回 | 1606 |
| 项目扣款实缴退回 | 1349 |
| 到款确认表-卢燕审核 | 1254 |
| 支付申请-尹佳梅、卢燕审核 | 1204 |
| 支付申请-文楠审核 | 1135 |
| 到款确认表-尹佳梅审核 | 1052 |
| 工程部--印章使用审批流程 | 1021 |
| 请假/休假流程 | 909 |
| 工程款支付审批 | 858 |
| 支付申请 | 791 |
| 公司存档资料管理 | 694 |
| 外出申请 | 644 |
| 收联营保证金 | 552 |
| 销项票申请 | 520 |
| 支付申请-尹佳梅审核 | 519 |
| 付项目保证金流程 | 503 |
| 已审批流程-财务支出 | 467 |

## Setup Business Tables

| Setup table | Rows |
|---|---:|
| C_JXXP_ZYFPJJD | 21692 |
| ZJGL_SZQR_DKQRB | 6782 |
| CWGL_FYBX | 5261 |
| C_CWSFK_GSCWZC | 4871 |
| C_ZFSQGL | 4779 |
| ZJGL_BZJGL_Pay_FBZJ | 4315 |
| C_JXXP_XXKPDJ | 3977 |
| C_CWSFK_GSCWSR | 3722 |
| ZJGL_BZJGL_Pay_FBZJTH | 3329 |
| C_JFHKLR_TH_ZCDF | 2550 |
| ZJGL_BZJGL_Branch_SBZJTH | 2499 |
| T_KK_SJTHB | 2387 |
| T_Base_CooperatCompany | 2055 |
| BGGL_XZD_YZSYSPB | 1584 |
| ZJGL_BZJGL_Branch_SBZJDJ | 1568 |
| BGGL_TZXX_WJPYCJ | 1476 |
| P_ZTB_GCBMGL | 1114 |
| BGGL_KQTJ_YTWC | 1109 |
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | 993 |
| BGGL_HBZJ_XZD_QJXJSPB | 909 |
| C_ZJGL_GCKZF | 858 |
| SGZL_RZRJ | 694 |
| BGGL_XZ_JXDJ_ZB | 691 |
| C_JXXP_KJFPSQ | 520 |
| T_GYSHT_INFO | 460 |
| C_JXXP_YJSKDJ | 349 |
| ZJGL_ZJSZ_DKGL_DKDJ | 320 |
| T_FK_Supplier | 311 |
| ZJGL_WJZ_WJZDJB | 310 |
| ZJGL_ZCDFSZ_FXJK_JK | 280 |

## Next lane recommendation

- family: `expense_or_deposit_family`
- blocked rows: `26780`
- lane: `expense_deposit_fact_lane`
- reason: blocked rows point to reimbursement, financial expense, guarantee, or deposit facts not yet covered by current payment/request assets

## Boundary

Rows remain blocked until their target business records are assetized and loadable.
Do not import these approval rows into `sc.legacy.workflow.audit` without a concrete target external id.
