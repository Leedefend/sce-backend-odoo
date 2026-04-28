# 账户收支统计表对账预检 Batch-AE

## 批次定位

- Layer Target：Domain Projection / Migration Evidence
- Module：`docs/migration_alignment`
- 旧过程：`Report_SP_USP_Select_ZHSZTJB_GS_Tree`
- 目标：确认旧过程与新系统账户收支统计表对账时的边界和差异来源。

## 旧过程执行限制

在当前 `legacy-mssql-restore` 容器中直接执行旧过程失败：

```text
Cannot resolve the collation conflict between "SQL_Latin1_General_CP1_CI_AS" and "Chinese_PRC_CI_AS" in the equal to operation.
```

原因是旧过程内创建 `#xmids_temp` 临时表，临时表继承 tempdb 排序规则，而旧库业务表使用中文排序规则。该问题属于旧库恢复环境限制，不是新系统实现错误。

后续对账应采用两种方式之一：

- 使用等价 SQL 手工复刻旧过程来源口径，并显式处理排序规则。
- 在旧库恢复容器中修正 tempdb/临时表排序规则后再执行旧过程。

## 新旧口径差异

新系统当前口径比旧过程更完整，不能直接用总额机械一致作为验收标准。

主要差异：

- 旧过程只从 `C_Base_ZHSZ` 有效账户起算；Batch-AD 新系统补了 48 个历史来源账户，用于承载真实历史单据引用但不在 `C_Base_ZHSZ` 的账户。
- 旧过程按账户 ID 精确关联；新系统回放会按账户 ID、账号、账户名兜底匹配，避免旧单据账户 ID 漂移导致漏计。
- 旧过程 `Report_SP_USP_Select_ZHSZTJB_GS_Tree` 中 `T_KK_SJDJB_CB` 扣款实缴登记分支被注释；新系统依据资金明细过程和扣款汇总过程承载了该真实支出来源。

## 模拟生产现状

新系统账户收支统计当前总览：

| 范围 | 行数 | 收入金额 | 支出金额 | 累计收款 | 累计支出 | 账户往来 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 全部账户 | 120 | 667,283,298.46 | 664,695,125.08 | 5,677,528,462.76 | 5,574,757,978.40 | 2,588,173.38 |
| `C_Base_ZHSZ` 正式账户 | 63 | 333,261,649.23 | 331,847,562.54 | 2,710,831,322.79 | 2,681,744,730.83 | 1,414,086.69 |
| 历史来源账户 | 48 | 380,000.00 | 500,000.00 | 127,932,908.59 | 105,634,258.37 | -120,000.00 |

## 后续对账策略

下一轮不应只比较旧过程总额，而应拆三层：

- `legacy_exact`：只按旧过程账户 ID 精确关联，复刻旧过程可比口径。
- `new_official`：新系统正式账户口径，包含账号/账户名兜底绑定。
- `new_continuity`：新系统连续经营口径，包含历史来源账户。

验收时需要分别解释：

- 旧过程恢复环境是否可直接执行。
- 旧过程精确口径与 `legacy_exact` 是否一致。
- `new_official` 相对 `legacy_exact` 多出的金额是否来自账号/账户名兜底。
- `new_continuity` 相对 `new_official` 多出的金额是否来自 Batch-AD 历史来源账户。

Batch-AF 已将上述三层口径落成脚本：

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  make odoo.shell.exec < scripts/migration/legacy_account_income_expense_reconciliation_matrix.py
```
