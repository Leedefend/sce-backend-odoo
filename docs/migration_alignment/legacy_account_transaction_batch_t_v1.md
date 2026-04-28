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

## 尚未覆盖

旧过程中的 `LJSK/LJZC` 仍包含多来源：

- `C_JFHKLR`
- `BGGL_JHK_HKDJ`
- `ZJGL_ZCDFSZ_FXJK_*`
- `ZJGL_BZJGL_*`
- `T_FK_Supplier`
- `C_CWSFK_GSCWSR`
- `C_CWSFK_GSCWZC`
- `T_KK_SJTHB`

下一轮应继续按同一载体补累计收款、累计支出来源。
