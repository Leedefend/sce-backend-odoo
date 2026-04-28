# 账户收支统计三层对账矩阵 Batch-AF

## 批次定位

- Layer Target：Migration Evidence / Domain Projection Validation
- Module：`scripts/migration`, `docs/migration_alignment`
- 数据库：`sc_prod_sim`
- 目标：把 Batch-AE 定义的三层对账口径落成可重复执行脚本。

## 脚本

新增脚本：

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  make odoo.shell.exec < scripts/migration/legacy_account_income_expense_reconciliation_matrix.py
```

输出：

- `legacy_exact`：正式账户，且来源明细 `account_legacy_id` 必须与正式账户 `legacy_account_id` 精确一致。
- `new_official`：正式账户的新系统投影，包含账号/账户名兜底绑定。
- `new_continuity`：完整连续经营投影，包含 Batch-AD 补充的历史来源账户。

## 总览结果

| 口径 | 账户行 | 收入金额 | 支出金额 | 累计收款 | 累计支出 | 账户往来 | 当前账户余额 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_exact | 63 | 305,580,740.97 | 304,631,242.91 | 1,349,630,269.09 | 1,433,486,309.46 | 949,498.06 | -56,216,323.45 |
| new_official | 63 | 333,261,649.23 | 331,847,562.54 | 2,710,831,322.79 | 2,681,744,730.83 | 1,414,086.69 | 29,121,372.58 |
| new_continuity | 111 | 333,641,649.23 | 332,347,562.54 | 2,838,764,231.38 | 2,787,378,989.20 | 1,294,086.69 | 42,744,820.64 |

## 差异解释

| 差异 | 账户行 | 收入金额 | 支出金额 | 累计收款 | 累计支出 | 账户往来 | 当前账户余额 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| new_official - legacy_exact | 0 | 27,680,908.26 | 27,216,319.63 | 1,361,201,053.70 | 1,248,258,421.37 | 464,588.63 | 85,337,696.03 |
| new_continuity - new_official | 48 | 380,000.00 | 500,000.00 | 127,932,908.59 | 105,634,258.37 | -120,000.00 | 13,623,448.06 |

`new_official - legacy_exact` 代表账号/账户名兜底绑定带来的正式账户增量。它不应视为错误，而是旧单据账户 ID 漂移后的可解释补偿。

`new_continuity - new_official` 代表 Batch-AD 创建的历史来源账户带来的连续经营增量。它不属于旧过程 `C_Base_ZHSZ` 起表口径，但属于真实历史单据引用过的账户事实。

## 验收判断

账户收支统计表不再适合用“旧过程总额完全相等”作为验收标准。合理验收应为：

- `legacy_exact` 可作为旧过程可比基线。
- `new_official` 明确展示正式账户兜底绑定后的增量。
- `new_continuity` 明确展示历史来源账户补齐后的增量。
- 后续业务验收应按账户类型、账户明细、差异来源三列同时查看。

## 下一步

Batch-AG 已把三层对账矩阵进一步收敛为用户可读的账户级 Top 差异清单，并将差异原因分类为 `fallback_match` 和 `supplemental_account`。

Batch-AH 已继续把总览、账户类型、Top 差异三类结果输出为 CSV，便于业务人员用表格筛选和复核。
