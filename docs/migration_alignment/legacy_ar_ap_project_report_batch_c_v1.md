# 应收应付报表（项目）承载方案 Batch-C

## 批次边界

- Layer Target：业务事实分析层
- Module：`docs/migration_alignment`
- Reason：旧库 P0 高频报表“应收应付报表（项目）”点击量最高，旧实现依赖多类事实，必须先拆清字段、依赖表和新系统覆盖率，再进入聚合模型实现。

## 不做

- 不新增 Odoo 模型。
- 不新增菜单。
- 不实现报表 SQL view。
- 不修改前端。
- 不修改 `smart_core`、启动链或公共 intent。

## 旧库入口与使用证据

- 报表：应收应付报表（项目）
- 旧配置：`a547011c5d9541b286e45d2cbe2123a1`
- 旧过程：`UP_USP_SELECT_YSYFHZB_XM`
- 参数：`@XMID` 项目，`@DWMC` 往来单位名称
- 使用：8243 次点击，18 个用户，最近使用到 2026-04-10

## 旧过程输出字段

| 字段 | 业务含义 | 旧库口径 |
| --- | --- | --- |
| `XMIDS` | 项目编号 | 参数 `@XMID` |
| `XMMC` | 项目名称 | `BASE_SYSTEM_PROJECT.XMMC` |
| `DWMC` | 往来单位 | `View_Select_Dept_All_NEW.DWMC` |
| `HTJE` | 收入合同金额 | `T_ProjectContract_Out.GCYSZJ` |
| `YKP` | 已开票 | `C_JXXP_XXKPDJ.SKZJE` |
| `YSK` | 已收款 | `C_JFHKLR.f_JE`，正常类型收款 |
| `WSK` | 未收款 | 收入合同金额 - 已收款 |
| `YKPWSK` | 已开票未收款 | max(已开票 - 已收款, 0) |
| `YSKWKP` | 已收款未开票 | max(已收款 - 已开票, 0) |
| `HTJE_YF` | 应付合同金额 | `T_GYSHT_INFO.ZJE` |
| `JJFS_YF` | 计价方式 | `T_GYSHT_INFO.JJFSTEXT` 去重拼接 |
| `YFK_YF` | 已付款 | `T_FK_Supplier.f_FKJE` |
| `YKP_YF` | 已收供应商发票 | `C_JXXP_ZYFPJJD_CB.HJJE` |
| `WFK_YF` | 未付款 | max(已收供应商发票 - 已付款, 0) |
| `WKP_YF` | 未开票/付款超票 | max(已付款 - 已收供应商发票, 0) |
| `KPDJSE` | 销项税额 | `C_JXXP_XXKPDJ.ZSE` |
| `JXSBSE` | 进项上报税额 | `C_JXXP_ZYFPJJD_CB.JXSE` |
| `DKZE` | 抵扣税额 | `C_JXXP_DKDJ_CB.DKSE` |
| `SF` | 税负/抵扣比例 | 抵扣税额 / 销项税额 |
| `SJKYYE` | 实际可用余额 | `View_Select_XMCKXX_BS.SJKYYE` |
| `ZCSRJE` | 自筹收入金额 | `C_JFHKLR.f_JE`，自筹垫付/其他类型收款 |
| `ZCTHJE` | 自筹退回金额 | `C_JFHKLR_TH_ZCDF_CB.BCTK` |
| `ZCWTJE` | 自筹未退金额 | 自筹收入 - 自筹退回 |
| `KPDJFJS` | 销项附加税 | `C_JXXP_XXKPDJ_CB.D_SCBSJS_FJS` |
| `JXSBFJS` | 进项附加税 | `C_JXXP_ZYFPJJD_CB.D_SCBSJS_FJS` |
| `DKDJFJS` | 抵扣附加税 | `C_JXXP_DKDJ_CB.D_SCBSJS_DKFJS` |

## 旧库依赖数据量

| 旧表 | 行数 | 作用 |
| --- | ---: | --- |
| `BASE_SYSTEM_PROJECT` | 755 | 项目 |
| `T_ProjectContract_Out` | 1694 | 收入合同 |
| `T_ProjectContract_Out_CB` | 3308 | 收入合同明细 |
| `T_GYSHT_INFO` | 5535 | 供应商/应付合同 |
| `C_JFHKLR` | 7412 | 收款 |
| `C_JFHKLR_CB` | 4491 | 收款明细 |
| `C_JFHKLR_TH_ZCDF` | 834 | 自筹退回 |
| `C_JFHKLR_TH_ZCDF_CB` | 1606 | 自筹退回明细 |
| `C_JXXP_XXKPDJ` | 3157 | 销项开票 |
| `C_JXXP_XXKPDJ_CB` | 4660 | 销项开票明细 |
| `C_JXXP_ZYFPJJD` | 16616 | 进项发票 |
| `C_JXXP_ZYFPJJD_CB` | 25393 | 进项发票明细 |
| `C_JXXP_DKDJ_New` | 605 | 抵扣登记 |
| `C_JXXP_DKDJ_CB` | 4990 | 抵扣明细 |
| `T_FK_Supplier` | 13629 | 供应商付款 |

## 新系统覆盖率

| 新模型 | 总量 | 项目覆盖 | 往来单位覆盖 | 判断 |
| --- | ---: | ---: | ---: | --- |
| `construction.contract` | 6889 | 6889 | 6889 | 可承载收入/支出合同，历史合同编号 6793 条 |
| `sc.receipt.income` | 9543 | 9543 | 5779 | 可承载收款，但需要单位文本兜底 |
| `sc.payment.execution` | 1192 | 1192 | 642 | 仅承载付款残余/实付残余，不足以覆盖旧 `T_FK_Supplier` 全量 |
| `payment.ledger` | 12194 | 通过付款申请 | 通过付款申请 | 可作为资金台账参考，不等同旧供应商付款口径 |
| `sc.invoice.registration` | 27947 | 27947 | 21402 | 可承载发票登记；销项和预缴没有 `partner_id` |
| `sc.legacy.invoice.tax.fact` | 5920 | 5920 | 文本字段 | 可补税额事实，但不是完整发票登记 |
| `sc.legacy.receipt.income.fact` | 7220 | 已迁移 | 文本字段 | 可作为收款旧事实对账参考 |
| `sc.legacy.payment.residual.fact` | 1683 | 已迁移 | 文本字段 | 只能补付款残余，不能替代供应商付款全量 |

## 关键缺口

1. 往来单位键不能只用 `partner_id`  
   旧报表按 `View_Select_Dept_All_NEW.DWMC` 聚合。新系统部分历史事实没有 `partner_id`，特别是销项发票和预缴发票，必须使用 `partner_id + legacy_partner_name / legacy_counterparty_text / partner_name_text` 组合键。

2. 旧供应商付款 `T_FK_Supplier` 未被现有 `sc.payment.execution` 全量覆盖  
   旧表有 13629 行，新系统 `sc.payment.execution` 只有 1192 行。下一批如果直接实现 `YFK_YF`，必须找已有 `payment.request/payment.ledger` 与旧供应商付款的映射，或补 `legacy supplier payment fact`。

3. 自筹退回口径尚无明确新模型  
   `ZCTHJE/ZCWTJE` 依赖 `C_JFHKLR_TH_ZCDF*`，当前未发现对应专用事实模型。需要先补事实或在报表中标注为缺口字段。

4. 实际可用余额依赖旧视图 `View_Select_XMCKXX_BS`  
   新系统没有同名资金可用余额视图。该字段应放入资金账户/项目资金汇总后再接入，不应在应收应付报表中临时硬算。

## 下一批实现建议

Batch-D 不宜一次实现完整 27 字段。建议先实现 `sc.ar.ap.project.summary` 的第一阶段可用报表：

- 维度：项目、往来单位显示名、方向
- 第一阶段字段：
  - 收入合同金额 `HTJE`
  - 已开票 `YKP`
  - 已收款 `YSK`
  - 未收款 `WSK`
  - 已开票未收款 `YKPWSK`
  - 已收款未开票 `YSKWKP`
  - 应付合同金额 `HTJE_YF`
  - 已收供应商发票 `YKP_YF`
  - 销项税额 `KPDJSE`
  - 进项税额 `JXSBSE`

暂缓字段：

- 已付款 `YFK_YF`
- 未付款 `WFK_YF`
- 付款超票 `WKP_YF`
- 抵扣税额 `DKZE`
- 自筹退回相关字段
- 实际可用余额

暂缓原因：这些字段现有事实覆盖不完整，直接上线会给用户错误数字。
