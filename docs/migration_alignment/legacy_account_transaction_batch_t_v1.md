# 账户收支来源明细 Batch-T

## 批次定位

- Layer Target：Domain Carrier / Domain Projection
- Module：`addons/smart_construction_core`, `scripts/migration`
- 旧过程：`Report_SP_USP_Select_ZHSZTJB_GS_Tree`
- 本批来源：`C_FKGL_ZHJZJWL`

## 旧过程口径

旧过程中的 `ZCJE` 和 `SRJE` 来自账户间资金往来表：

- `ZCZH_Id = 账户ID` 时计入 `ZCJE`，语义为账户往来支出。
- `SKZH_Id = 账户ID` 时计入 `SRJE`，语义为账户往来收入。
- 仅统计 `DJZT='2'`、未删除、发生日期在查询区间内的记录。

## 新系统承载

新增模型 `sc.legacy.account.transaction.line`，作为账户收支统计表的来源明细载体。

本批把 `C_FKGL_ZHJZJWL` 拆成两类明细：

- 支出方向：`source_key = <Id>:expense`，账户为 `ZCZH_Id`。
- 收入方向：`source_key = <Id>:income`，账户为 `SKZH_Id`。

该模型保留来源表、历史记录ID、项目、账户、对方账户、方向、统计口径、金额和单据状态。

## 对汇总表的影响

`sc.account.income.expense.summary` 已调整为：

- `收入金额` 读取 `metric_bucket='account_transfer' and direction='income'`。
- `支出金额` 读取 `metric_bucket='account_transfer' and direction='expense'`。
- `账户往来` = `收入金额 - 支出金额`。
- `累计收款/累计支出` 优先读取后续累计收支来源；当前缺失时继续回退到资金日报可用口径。

## 可重建能力

新增 Make target：

- `fresh_db.legacy_account_transaction.replay.adapter`
- `fresh_db.legacy_account_transaction.replay.write`

并已接入 `history_continuity_oneclick.sh`，完整部署重放时会在账户主数据之后写入账户收支来源明细。

## Batch-U 补充

Batch-U 在同一载体继续接入公司财务收支：

- `C_CWSFK_GSCWSR`：公司财务收入，写入 `direction='income'`、`metric_bucket='cumulative'`，对应旧过程 `LJSK` 的公司财务收入部分。
- `C_CWSFK_GSCWZC`：公司财务支出，写入 `direction='expense'`、`metric_bucket='cumulative'`，对应旧过程 `LJZC` 的公司财务支出部分。

`sc.account.income.expense.summary` 已经按 `metric_bucket='cumulative'` 优先读取累计收款和累计支出，因此本批无需调整报表结构。

Batch-V 在同一载体继续接入收款登记：

- `C_JFHKLR`：收款登记，写入 `direction='income'`、`metric_bucket='cumulative'`，对应旧过程 `LJSK` 的收款登记部分。
- 发生日期使用 `f_RQ`，账户使用 `SKZHID/SKZH`，金额使用 `f_JE`。
- 项目优先使用 `XMID/XMMC`，缺失时回退到来源项目和特殊项目字段。

Batch-W 在同一载体继续接入收入退回：

- `C_JFHKLR_TH`：普通收入退回，写入 `direction='expense'`、`metric_bucket='cumulative'`，对应旧过程 `LJZC` 的收入退回部分；当前旧库未发现符合已审核、未删除、有退回账户且金额非零的有效行。
- `C_JFHKLR_TH_ZCDF_CB`：自筹收入退回明细，关联 `C_JFHKLR_TH_ZCDF` 表头，写入 `direction='expense'`、`metric_bucket='cumulative'`；金额使用 `BCTK`，账户使用 `THZHID/THZH`，日期优先 `THSJ`，再回退 `JNSJ/DJRQ`。
- 模拟生产库本批新增 `C_JFHKLR_TH_ZCDF_CB` 1509 行，金额 128,341,610.12；其中 1501 行已绑定账户，8 行未绑定账户，未绑定金额 70,118.23。

Batch-X 在同一载体继续接入供应商付款：

- `T_FK_Supplier`：正常付款写入 `direction='expense'`、`metric_bucket='cumulative'`，对应旧过程 `LJZC` 的供应商付款部分；当前模拟生产库新增 13282 行，金额 2,103,459,198.35。
- `T_FK_Supplier`：付款退回分支保留为 `direction='income'`、`metric_bucket='cumulative'`，对应旧过程 `LJSK` 的付款退回部分；当前旧库 `SFZFTK='是'` 且有效付款账户的记录为 0。
- 账户名称输出为 `FKZHMC/FKZH`，让回放脚本在旧账户 ID 未进入账户主数据时，能按账号兜底匹配有效账户。
- 账号兜底后，`T_FK_Supplier` 已绑定 13125 行，未绑定 157 行，未绑定金额 36,913,102.92。

Batch-Y 在同一载体继续接入借还款：

- `ZJGL_ZCDFSZ_FXJK_HK`：风险借款还款，写入 `direction='income'`、`metric_bucket='cumulative'`，对应旧过程 `LJSK` 的风险借款还款部分；模拟生产库新增 84 行，金额 55,223,063.02。
- `ZJGL_ZCDFSZ_FXJK_JK`：风险借款申请，写入 `direction='expense'`、`metric_bucket='cumulative'`，对应旧过程 `LJZC` 的风险借款部分；模拟生产库新增 95 行，金额 96,586,522.16。
- `BGGL_JHK_HKDJ` 与 `BGGL_JHK_JKSQ` 的员工借还款分支已保留，但当前旧库已审核有效记录的账户字段为空，因此本批未产生有效行。
- 本批新增 179 行全部绑定到账户主数据，未新增未绑定来源。

Batch-Z 在同一载体继续接入保证金：

- `ZJGL_BZJGL_Pay_FBZJ`：付保证金，写入 `direction='expense'`、`metric_bucket='cumulative'`；模拟生产库新增 2903 行，金额 215,611,737.26。
- `ZJGL_BZJGL_Pay_FBZJTH`：退付保证金，写入 `direction='income'`、`metric_bucket='cumulative'`；模拟生产库新增 1851 行，金额 209,336,943.57。
- `ZJGL_BZJGL_Branch_SBZJDJ`：收保证金，写入 `direction='income'`、`metric_bucket='cumulative'`；模拟生产库新增 1540 行，金额 108,563,008.28。
- `ZJGL_BZJGL_Branch_SBZJTH`：退收保证金，写入 `direction='expense'`、`metric_bucket='cumulative'`；模拟生产库新增 884 行，金额 108,850,591.28。
- 退付保证金账户名称补 `Y_ZFZHao/Y_ZFZH` 兜底后，重放修正 511 条账户绑定；本批保证金最终未绑定 262 条，未绑定金额 48,318,603.97。

Batch-AA 在同一载体继续接入贷款：

- `ZJGL_ZJSZ_DKGL_DKDJ`：贷款登记，写入 `direction='income'`、`metric_bucket='cumulative'`；模拟生产库新增 150 行，金额 52,926,662.18。
- `ZJGL_ZJSZ_DKGL_HKDJ`：贷款还款，写入 `direction='expense'`、`metric_bucket='cumulative'`；模拟生产库新增 98 行，金额 31,859,781.01。
- 本批贷款来源未绑定 13 条，金额 1,225,000.00，主要为利龙旧账户和虚拟账户。

## 尚未覆盖

旧过程中的 `LJSK/LJZC` 仍包含多来源：

- `T_KK_SJTHB`

下一轮应继续按同一载体补累计收款、累计支出来源。
