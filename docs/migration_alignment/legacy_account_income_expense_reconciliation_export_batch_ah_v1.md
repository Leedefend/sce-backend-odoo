# 账户收支统计三层对账导出 Batch-AH

## 批次定位

- Layer Target：Migration Evidence / Report Export
- Module：`scripts/migration`, `docs/migration_alignment`
- 数据库：`sc_prod_sim`
- 目标：把账户收支统计三层对账结果输出为可下载、可筛选的 CSV 证据，支撑业务验收。

## 执行命令

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  make odoo.shell.exec < scripts/migration/legacy_account_income_expense_reconciliation_matrix.py
```

## 导出物

脚本现在输出五类证据：

- JSON：`legacy_account_income_expense_reconciliation_matrix_v1.json`
- Markdown：`legacy_account_income_expense_reconciliation_matrix_v1.md`
- 总览 CSV：`legacy_account_income_expense_reconciliation_totals_v1.csv`
- 账户类型 CSV：`legacy_account_income_expense_reconciliation_account_type_v1.csv`
- Top 差异 CSV：`legacy_account_income_expense_reconciliation_top_diff_v1.csv`

默认目录为 `artifacts/migration`。如果 Odoo 容器内该目录不可写，脚本会把导出物写入容器内 `/tmp`，并在 JSON/stdout 的 `artifacts.*_fallback` 字段记录真实位置。

## CSV 口径

### 总览 CSV

`legacy_account_income_expense_reconciliation_totals_v1.csv` 用于对比三层总额和两类差异：

- `legacy_exact`
- `new_official`
- `new_continuity`
- `new_official_minus_legacy_exact`
- `new_continuity_minus_new_official`

### 账户类型 CSV

`legacy_account_income_expense_reconciliation_account_type_v1.csv` 用于按账户类型筛选：

- 保证金账户
- 其他资金账户
- 历史来源账户
- 未分类账户

### Top 差异 CSV

`legacy_account_income_expense_reconciliation_top_diff_v1.csv` 用于业务解释差异来源：

- `fallback_match`：正式账户由账号/账户名兜底绑定形成的增量。
- `supplemental_account`：真实历史单据引用过、但不在正式账户主数据中的历史来源账户。

## 验收判断

本批不改变业务数据、不改变模型、不改变前端契约，只把既有三层对账矩阵转成可筛选导出物。

业务验收时应先看总览 CSV 确认三层口径，再看账户类型 CSV 判断差异集中在哪类账户，最后用 Top 差异 CSV 对金额影响最大的账户逐项确认。

## 后续方向

- 如要面向最终用户下载，需要给 `MIGRATION_ARTIFACT_ROOT` 配置容器可写且宿主机可取的挂载目录。
- 如要进入新系统页面，需要把三类 CSV 的字段契约化为报表接口，避免前端直接解析迁移脚本输出。
