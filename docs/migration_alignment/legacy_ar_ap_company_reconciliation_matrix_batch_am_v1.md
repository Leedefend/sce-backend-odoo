# 应收应付报表新旧差异矩阵 Batch-AM

## 批次定位

- Layer Target：Migration Evidence / Reconciliation Matrix
- Module：`scripts/migration`, `docs/migration_alignment`
- 目标：按 `legacy_project_id` 对齐旧库 `UP_USP_SELECT_YSYFHZB_XM_ZJ` 只读 COLLATE 导出基线与新系统 `sc.ar.ap.company.summary`。

## 输入基线

- 旧库来源：`UP_USP_SELECT_YSYFHZB_XM_ZJ`
- 旧库执行方式：`scripts/migration/legacy_ar_ap_company_collation_probe.py`
- 旧库导出：`legacy_ar_ap_company_collation_probe_rows_v1.csv`
- 新系统来源：`sc.ar.ap.company.summary`
- 对齐键：`project.legacy_project_id`

## 行覆盖

| 指标 | 数量 |
| --- | ---: |
| 旧库行数 | `195` |
| 新系统行数 | `765` |
| 匹配项目 | `195` |
| 仅旧库 | `0` |
| 仅新系统 | `570` |

结论：旧库 195 行均能在新系统中找到对应项目，但新系统额外覆盖 570 个项目。当前差异主要不是主键丢失，而是旧过程最终输出范围比新系统报表窄。

## 汇总差异

| 字段 | 旧库 | 新系统 | 差异 |
| --- | ---: | ---: | ---: |
| `income_contract_amount` | `569590088.66` | `3142399070.99` | `2572808982.33` |
| `output_invoice_amount` | `496732725.67` | `47602317362.22` | `47105584636.55` |
| `receipt_amount` | `490319045.61` | `480379794.04` | `-9939251.57` |
| `receivable_unpaid_amount` | `79271043.05` | `2662019276.95` | `2582748233.90` |
| `invoiced_unreceived_amount` | `6403680.06` | `47121937568.18` | `47115533888.12` |
| `received_uninvoiced_amount` | `0.00` | `0.00` | `0.00` |
| `payable_contract_amount` | `47140260.62` | `2402850045.36` | `2355709784.74` |
| `paid_amount` | `74894911.93` | `2147431936.05` | `2072537024.12` |
| `input_invoice_amount` | `73605618.71` | `2642686493.21` | `2569080874.50` |
| `payable_unpaid_amount` | `-27754651.31` | `255418109.31` | `283172760.62` |
| `paid_uninvoiced_amount` | `1289293.22` | `0.00` | `-1289293.22` |
| `output_tax_amount` | `42796083.30` | `4074448722.58` | `4031652639.28` |
| `input_tax_amount` | `6959747.43` | `241175377.57` | `234215630.14` |
| `deduction_tax_amount` | `35836335.87` | `3833273345.01` | `3797437009.14` |
| `actual_available_balance` | `5214866.85` | `-2586337.86` | `-7801204.71` |
| `self_funding_income_amount` | `539095.14` | `0.00` | `-539095.14` |
| `self_funding_refund_amount` | `0.00` | `0.00` | `0.00` |
| `self_funding_unreturned_amount` | `539095.14` | `0.00` | `-539095.14` |
| `output_surcharge_amount` | `385164.75` | `38657783.48` | `38272618.73` |
| `input_surcharge_amount` | `62637.74` | `1275135.86` | `1212498.12` |
| `deduction_surcharge_amount` | `322527.01` | `37382647.62` | `37060120.61` |

## Top 差异项目

| 项目 | 原因 | 影响分 |
| --- | --- | ---: |
| 鸿图府项目第一期建筑安装工程 | `matched` | `60619310923.56` |
| 易静工程（德阳二重工程项目） | `matched` | `15206076127.21` |
| 誉城国际一期二批次 | `matched` | `7640299428.93` |
| 向东工程 | `new_only` | `5335842909.70` |

## 口径判断

1. 新系统项目覆盖更宽。`sc.ar.ap.company.summary` 当前按新系统项目应收应付事实全量汇总，只要项目存在任一事实字段即可进入报表。
2. 旧库过程输出更窄。旧过程包含合同登记日期、项目名称等参数入口，且最终输出经过旧 SQL 内部条件收敛，因此默认空条件结果只有 195 个项目。
3. 旧库不存在 `legacy_only`，说明本轮不是迁移项目主键断链问题；主要矛盾是“旧常用报表口径”与“新系统全量经营事实口径”的范围差异。
4. 当前不能直接把新系统报表判定为错误。若业务希望复刻旧常用报表，应新增“旧口径筛选/报表视图”；若业务希望升级为全量经营台账，则需要把 570 个 `new_only` 项目分类解释。

## 后续任务

- 对 570 个 `new_only` 项目按事实来源分类：收入合同、销项发票、收款、支出合同、付款、进项发票。
- 对 Top matched 项目做字段级来源追踪，优先解释销项发票、进项发票、收付款三类大额差异。
- 明确产品口径：保留 `sc.ar.ap.company.summary` 作为全量经营事实报表，同时按需增加“旧库常用口径”筛选入口。
