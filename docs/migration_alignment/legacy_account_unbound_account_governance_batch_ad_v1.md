# 账户收支未绑定账户治理 Batch-AD

## 批次定位

- Layer Target：Domain Carrier / Migration Data Quality
- Module：`scripts/migration`, `docs/migration_alignment`
- 数据库：`sc_prod_sim`
- 目标：消除 `sc.legacy.account.transaction.line` 中账户来源明细未绑定账户的问题，保证账户收支统计表按账户维度连续展示。

## 问题事实

Batch-AC 后，账户收支来源表共有 39,707 行，其中 548 行没有绑定 `sc.legacy.account.master`，金额合计 143,598,208.98。

排查发现，主要缺口不是旧账户主表 `C_Base_ZHSZ` 中的 inactive 账户，而是历史单据上出现过、但不在 `C_Base_ZHSZ` 中的账户锚点。例如：

- `66a280576a644dbea099608859a0efd9`
- `5d20e4228c524b35a83677ca7336e968`
- `26a417f9e8374a02af255798811a20a8`
- `1a532e1fb7a14566a187ad65fb0cbdb1`
- `2001209078094d2494a30e889216c411`

这些账户真实参与了历史收支单据。如果不承载，账户收支统计表会漏计历史业务金额。

## 处理策略

`fresh_db_legacy_account_transaction_replay_write.py` 在写入账户收支来源明细前，新增补账户规则：

- 先读取全部待回放明细中的 `account_legacy_id/account_name/project_legacy_id`。
- 若 `account_legacy_id` 不存在于 `sc.legacy.account.master`，创建一条 `source_table='legacy_account_transaction_source'` 的历史来源账户。
- 账户名称优先取 `/` 左侧文本；账号优先取 `/` 右侧文本，纯数字文本也作为账号保留。
- 补账户后再解析并回填明细 `account_id`。

该规则只补历史真实单据引用过的账户，不修改 `C_Base_ZHSZ` 主数据回放口径。

## 验证结果

模拟生产库回放结果：

- 补充历史来源账户：48 个。
- 已有明细回填账户：906 条。
- 来源明细未绑定账户：0 条。
- `sc.account.income.expense.summary` 行数：120。
- 累计收款合计：5,677,528,462.76。
- 累计支出合计：5,574,757,978.40。

补充账户绑定来源分布：

| 来源 | 行数 | 金额 |
| --- | ---: | ---: |
| `C_JFHKLR` | 191 | 100,440,982.00 |
| `T_FK_Supplier` | 221 | 66,369,861.45 |
| `ZJGL_BZJGL_Pay_FBZJTH` | 111 | 20,454,123.33 |
| `ZJGL_BZJGL_Branch_SBZJTH` | 101 | 20,125,345.73 |
| `ZJGL_BZJGL_Pay_FBZJ` | 73 | 12,158,728.91 |
| `C_JFHKLR_TH_ZCDF_CB` | 54 | 4,665,815.57 |
| `ZJGL_BZJGL_Branch_SBZJDJ` | 36 | 3,319,787.09 |
| `ZJGL_ZJSZ_DKGL_DKDJ` | 11 | 3,075,000.00 |
| 其他来源 | 108 | 3,837,522.88 |

## 下一步

账户收支统计表下一阶段应进入旧报表样本对账：

- 选取旧系统常用的开始日期、结束日期、账户类型、项目过滤条件。
- 分别输出旧过程结果和新系统 `sc.account.income.expense.summary` 结果。
- 对账户类型汇总行、账户明细行、累计收款、累计支出、账户往来、当前账户余额做差异解释。
