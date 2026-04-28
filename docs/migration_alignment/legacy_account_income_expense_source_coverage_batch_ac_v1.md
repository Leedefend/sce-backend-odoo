# 账户收支统计表来源覆盖审计 Batch-AC

## 批次定位

- Layer Target：Domain Projection / Migration Evidence
- Module：`docs/migration_alignment`, `addons/smart_construction_core`
- 旧过程：`Report_SP_USP_Select_ZHSZTJB_GS_Tree`
- 目标：确认旧过程 `LJSK/LJZC` 的有效账户金额来源是否仍有未承载缺口。

## 审计结论

旧过程账户维度的有效账户金额来源已经进入 `sc.legacy.account.transaction.line`，或者在当前旧库中无有效账户金额行。

剩余风险不再是“未识别来源表”，而是：

- 历史账户未绑定新账户主数据。
- 旧过程样本区间、项目过滤、账户类型过滤与新系统展示筛选的逐项对账。
- 旧过程里部分 0 行分支后续如果旧库补数据，需要按已确认映射规则接入。

## 有效来源矩阵

| 来源 | 方向 | 当前旧库有效账户行 | 金额 | 新系统承载 |
| --- | --- | ---: | ---: | --- |
| `C_JFHKLR` | 累计收款 | 5348 | 2,439,165,450.40 | 已接入 |
| `BGGL_JHK_HKDJ_CB` | 累计收款 | 0 | 0.00 | 分支确认，当前无有效行 |
| `ZJGL_ZCDFSZ_FXJK_HK` | 累计收款 | 84 | 55,223,063.02 | 已接入 |
| `ZJGL_BZJGL_Pay_FBZJTH` | 累计收款 | 1851 | 209,336,943.57 | 已接入 |
| `T_FK_Supplier` 付款退回 | 累计收款 | 0 | 0.00 | 分支确认，当前无有效行 |
| `C_ZFSQGL_FKZH_CB` 付款退回多账户 | 累计收款 | 0 | 0.00 | 分支确认，当前无有效行 |
| `ZJGL_BZJGL_Branch_SBZJDJ` | 累计收款 | 1540 | 108,563,008.28 | 已接入 |
| `C_CWSFK_GSCWSR` | 累计收款 | 2118 | 19,785,988.01 | 已接入 |
| `ZJGL_BZJGL_Pay_FBZJTH_CB` | 累计收款 | 0 | 0.00 | 分支确认，当前无有效行 |
| `ZJGL_ZJSZ_DKGL_DKDJ` | 累计收款 | 150 | 52,926,662.18 | 已接入 |
| `T_KK_SJTHB_CB` | 累计收款 | 61 | 4,842,508.14 | 已接入 |
| `T_FK_Supplier` 正常付款 | 累计支出 | 13282 | 2,103,459,198.35 | 已接入 |
| `C_ZFSQGL_FKZH_CB` 正常付款多账户 | 累计支出 | 0 | 0.00 | 分支确认，当前无有效行 |
| `BGGL_JHK_JKSQ` | 累计支出 | 0 | 0.00 | 分支确认，当前无有效行 |
| `ZJGL_ZCDFSZ_FXJK_JK` | 累计支出 | 95 | 96,586,522.16 | 已接入 |
| `C_JFHKLR_TH` | 累计支出 | 0 | 0.00 | 分支确认，当前无有效行 |
| `C_JFHKLR_TH_ZCDF_CB` | 累计支出 | 1509 | 128,341,610.12 | 已接入 |
| `ZJGL_BZJGL_Pay_FBZJ` | 累计支出 | 2903 | 215,611,737.26 | 已接入 |
| `ZJGL_BZJGL_Branch_SBZJTH` | 累计支出 | 884 | 108,850,591.28 | 已接入 |
| `ZJGL_ZJSZ_DKGL_HKDJ` | 累计支出 | 98 | 31,859,781.01 | 已接入 |
| `C_CWSFK_GSCWZC` | 累计支出 | 2530 | 57,049,072.70 | 已接入 |
| `T_KK_SJDJB_CB` | 累计支出 | 6394 | 88,141,282.74 | 已接入 |

## 投标退款判断

本轮排查了名称上可能对应“投标退款”的候选表和过程引用，包括 `C_FKGL_YJTH`、`D_FJLX_ZJ_FKGL_YJTH`、`T_ZJZCTHD_ZB`、`T_ZJZCTHD_CB`、`ZJSZ_SKJH_XMBYJTH` 等。当前旧库这些候选表为 0 行，且不在账户收支统计旧过程的有效金额子查询中。

因此，不能把“投标退款”作为当前账户收支统计表的未承载事实缺口继续追写。后续如业务确认存在另一张旧报表或另一个低代码过程引用该能力，应另开报表来源审计批次。

## 下一步

账户收支统计表后续工作应从“继续找来源表”转为：

- 对 548 条未绑定账户来源逐项补账户主数据或确认历史无效账户。
- 按旧报表常用查询条件抽样，对 `Report_SP_USP_Select_ZHSZTJB_GS_Tree` 与新系统 `sc.account.income.expense.summary` 做区间、项目、账户类型对账。
- 对 0 行分支保留映射规则，但不把它们标记为当前数据缺口。
