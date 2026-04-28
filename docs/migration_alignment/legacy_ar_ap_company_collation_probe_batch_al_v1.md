# 应收应付报表旧过程 COLLATE 探针 Batch-AL

## 批次定位

- Layer Target：Migration Evidence / Legacy SQL Reconciliation
- Module：`scripts/migration`, `docs/migration_alignment`
- 旧过程：`UP_USP_SELECT_YSYFHZB_XM_ZJ`
- 目标：不修改旧库对象，使用只读 ad-hoc SQL 给旧过程临时表字符字段补 `COLLATE DATABASE_DEFAULT`，验证旧库全局应收应付结果可导出。

## 参数

- `@XMMC`：``
- `@KSRQ`：`2000-01-01`
- `@JZRQ`：``

## 结果

- 行数：`195`
- CSV：`/home/odoo/workspace/sce-backend-odoo/artifacts/migration/legacy_ar_ap_company_collation_probe_rows_v1.csv`
- JSON：`/home/odoo/workspace/sce-backend-odoo/artifacts/migration/legacy_ar_ap_company_collation_probe_result_v1.json`

## 汇总金额

| 指标 | 金额 |
| --- | ---: |
| `income_contract_amount` | `569590088.6600` |
| `output_invoice_amount` | `496732725.6700` |
| `receipt_amount` | `490319045.6100` |
| `receivable_unpaid_amount` | `79271043.0500` |
| `invoiced_unreceived_amount` | `9626199.5100` |
| `received_uninvoiced_amount` | `3212519.4500` |
| `payable_contract_amount` | `47140260.6200` |
| `paid_amount` | `74894911.9300` |
| `input_invoice_amount` | `73605618.7100` |
| `payable_unpaid_amount` | `943424.8700` |
| `paid_uninvoiced_amount` | `2232718.0900` |
| `output_tax_amount` | `36882083.9800` |
| `input_tax_amount` | `2731649.3100` |
| `deduction_tax_amount` | `1380400.1000` |
| `actual_available_balance` | `5214866.8510` |
| `self_funding_income_amount` | `1222938.1100` |
| `self_funding_refund_amount` | `1197292.9700` |
| `self_funding_unreturned_amount` | `25645.1400` |
| `output_surcharge_amount` | `4425850.4284` |
| `input_surcharge_amount` | `327797.9364` |
| `deduction_surcharge_amount` | `57147.7460` |

## 判断

排序规则冲突来自旧过程临时表字符字段使用 tempdb 默认排序规则。给 `#TEMP_RESULT_ZJ` / `#TEMP_RESULT_ZZJG` 的项目、单位字符字段补 `COLLATE DATABASE_DEFAULT` 后，旧过程逻辑可在恢复容器中只读执行。

本批只解决旧过程执行入口，不判定新旧数值一致。下一步应读取本 CSV，与 `sc.ar.ap.company.summary` 按 `legacy_project_id` 做字段级差异矩阵。
