# 应收应付报表（项目）字段全口径可用矩阵 Batch-K

## 1. 批次定位

- Layer Target：业务事实分析层 / Domain Projection Audit
- Module：`docs/migration_alignment`
- Reason：旧库 P0 报表“应收应付报表（项目）”已连续补齐多类事实，需要对旧过程 `UP_USP_SELECT_YSYFHZB_XM` 的 27 个输出字段做全口径审计，确认字段是否已经可用、是否存在运行库覆盖缺口，以及下一步应修复什么。

## 2. 总体结论

旧报表 27 个输出字段中：

- 已承载并可用于业务查看：`25` 个
- 已承载并经口径修正：`1` 个，`SF` 抵扣比例
- 已承载并经覆盖修正：`1` 个，`SJKYYE` 实际可用余额
- 未承载字段：`0` 个

因此，当前系统已经具备旧报表主体业务事实承载能力。Batch-L 已修复项目级资金余额在报表行上的覆盖问题；Batch-M 已确认并修正抵扣比例为旧库一致的项目级口径。

## 3. 字段矩阵

| 旧字段 | 业务含义 | 新系统字段/承载 | 状态 | 说明 |
| --- | --- | --- | --- | --- |
| `XMIDS` | 项目编号 | `project_id` / `project_name` | 已承载 | 旧参数字段，新系统以项目记录和项目名称承载。 |
| `XMMC` | 项目名称 | `project_name` | 已承载 | 来自 `project.project`。 |
| `DWMC` | 往来单位 | `partner_name` | 已承载 | 优先新 `res.partner`，无法匹配时使用历史名称兜底。 |
| `HTJE` | 收入合同金额 | `income_contract_amount` | 已承载 | 来源 `construction.contract(type='out')`。 |
| `YKP` | 已开票 | `output_invoice_amount` | 已承载 | 来源销项发票登记。 |
| `YSK` | 已收款 | `receipt_amount` | 已承载 | 来源收款事实。 |
| `WSK` | 未收款 | `receivable_unpaid_amount` | 已承载 | 收入合同金额 - 已收款。 |
| `YKPWSK` | 已开票未收款 | `invoiced_unreceived_amount` | 已承载 | `max(已开票 - 已收款, 0)`。 |
| `YSKWKP` | 已收款未开票 | `received_uninvoiced_amount` | 已承载 | `max(已收款 - 已开票, 0)`。 |
| `HTJE_YF` | 应付合同金额 | `payable_contract_amount` | 已承载 | 来源 `construction.contract(type='in')`。 |
| `JJFS_YF` | 计价方式 | `payable_pricing_method_text` | 已承载 | 来源 `sc.legacy.supplier.contract.pricing.fact`。 |
| `YFK_YF` | 已付款 | `paid_amount` | 已承载 | 来源 `sc.treasury.ledger(direction='out', state='posted')`。 |
| `YKP_YF` | 已收供应商发票 | `input_invoice_amount` | 已承载 | 来源进项发票登记。 |
| `WFK_YF` | 未付款 | `payable_unpaid_amount` | 已承载 | `max(已收供应商发票 - 已付款, 0)`。 |
| `WKP_YF` | 未开票/付款超票 | `paid_uninvoiced_amount` | 已承载 | `max(已付款 - 已收供应商发票, 0)`。 |
| `KPDJSE` | 销项税额 | `output_tax_amount` | 已承载 | 来源销项发票登记。 |
| `JXSBSE` | 进项上报税额 | `input_tax_amount` | 已承载 | 来源进项发票登记。 |
| `DKZE` | 抵扣税额 | `deduction_tax_amount` | 已承载 | 来源 `sc.legacy.tax.deduction.fact`。 |
| `SF` | 税负/抵扣比例 | `tax_deduction_rate` | 已承载 | Batch-M 已按旧库最终 SELECT 修正为项目级抵扣比例，并在项目行上重复展示。 |
| `SJKYYE` | 实际可用余额 | `actual_available_balance` | 已承载 | Batch-L 已补齐仅有项目余额、没有往来单位事实的项目级余额行。 |
| `ZCSRJE` | 自筹收入金额 | `self_funding_income_amount` | 已承载 | 来源 `sc.legacy.self.funding.fact`。 |
| `ZCTHJE` | 自筹退回金额 | `self_funding_refund_amount` | 已承载 | 来源 `sc.legacy.self.funding.fact`。 |
| `ZCWTJE` | 自筹未退金额 | `self_funding_unreturned_amount` | 已承载 | 自筹收入 - 自筹退回。 |
| `KPDJFJS` | 销项附加税 | `output_surcharge_amount` | 已承载 | 来源 `sc.legacy.invoice.surcharge.fact(direction='output')`。 |
| `JXSBFJS` | 进项附加税 | `input_surcharge_amount` | 已承载 | 来源 `sc.legacy.invoice.surcharge.fact(direction='input')`。 |
| `DKDJFJS` | 抵扣附加税 | `deduction_surcharge_amount` | 已承载 | 来源 `sc.legacy.tax.deduction.fact`。 |

## 4. 模拟生产运行库覆盖

运行库：`sc_prod_sim`

- 报表行数：`11696`
- 覆盖项目：`814`
- 覆盖往来单位键：`7202`
- Batch-L 新增项目级余额行：`56`

主要字段覆盖：

| 字段 | 非零/非空行 | 金额/说明 |
| --- | ---: | ---: |
| 收入合同金额 | 744 | `3142399070.99` |
| 已开票 | 671 | `47602317362.22` |
| 已收款 | 814 | `480379794.04` |
| 未收款 | 1555 | `2662019276.95` |
| 已开票未收款 | 664 | `47472912552.33` |
| 已收款未开票 | 775 | `350974984.15` |
| 应付合同金额 | 3881 | `2402859650.36` |
| 计价方式 | 3412 | 非空文本行 |
| 已付款 | 5950 | `2147431936.05` |
| 已收供应商发票 | 7206 | `2642686733.21` |
| 未付款 | 2481 | `623636160.51` |
| 付款超票 | 634 | `128381363.35` |
| 销项税额 | 734 | `177414371.67` |
| 进项税额 | 3780 | `114112494.93` |
| 抵扣税额 | 1864 | `56009185.14` |
| 抵扣比例 | 7471 | Batch-M 修正后，315 个项目具备非零项目级抵扣比例 |
| 自筹收入金额 | 569 | `219525590.83` |
| 自筹退回金额 | 370 | `143229174.39` |
| 自筹未退金额 | 415 | `76296416.44` |
| 销项附加税 | 730 | `20595859.4964` |
| 进项附加税 | 3594 | `13328329.2112` |
| 抵扣附加税 | 592 | `1759613.9436` |

项目资金余额单独说明：

- `sc.legacy.project.fund.balance.fact` 有效项目余额事实：`755` 行
- 已匹配新项目：`755` 行
- 项目余额事实金额合计：`-2586337.8610`
- Batch-K 审计时，报表中有实际可用余额的项目为 `512` 个；Batch-L 修复后，资金余额事实涉及的 `755` 个项目均已进入报表
- 报表行级 `actual_available_balance` 不允许直接合计，因为同一项目余额会随往来单位行重复展示

## 5. 当前缺口

### 已修复：实际可用余额报表行覆盖缺口

`SJKYYE` 是项目级余额。Batch-K 审计时，投影只把它挂到已有项目+往来单位行上。如果某项目只有资金余额事实、没有合同/收款/付款/发票/自筹等往来单位事实，该项目不会出现在 `sc.ar.ap.project.summary`。

Batch-L 已把 `project_fund_balance` 纳入报表 key 集合，为只有余额事实的项目生成“项目级余额”行，保证 755 个资金余额项目均可被用户看到。

### 已修复：抵扣比例口径

Batch-K 审计时，`SF` 按报表行计算：

```text
抵扣比例 = 抵扣税额 / 销项税额
```

但运行库只有 2 行同时有销项税额与抵扣税额。原因是销项税通常在客户往来单位行，抵扣税通常在供应商往来单位行。Batch-M 已回查旧过程最终 SELECT，确认 `SF` 是项目级汇总比例，并已修正。

## 6. 下一轮执行建议

1. 重跑模拟生产覆盖矩阵，确认旧报表 27 字段达到“可办理后可查看、可解释、可重建”的状态。
2. 复核 Batch-L 新增的“项目级余额”行在原生列表与自定义前端中的显示效果。
3. 复核比例字段在透视、导出和用户说明中的表现，避免用户误把项目级比例按行求和。
