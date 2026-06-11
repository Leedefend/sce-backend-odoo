# Fund Daily Handling Closure - 2026-06-12

## Boundary

资金日报属于账户资金办理和现金流核对输入，不属于公司-承包人往来责任事实，也不属于经营收付款申请。

本轮固定口径：

- `finance.fund.daily_report` 使用 `sc.fund.account.operation` 办理，用户认知保持“资金日报表”。
- 完成资金日报后，当日收入和当日支出分别进入来源级 `sc.treasury.ledger(source_kind='daily_line')`。
- 资金日报台账不挂 `payment_request_id`，不生成 `payment.ledger`。
- 资金日报不生成 `sc.interfund.movement.fact`，不参与公司-承包人责任余额。
- `finance.fund.balance_adjustment` 只表达账户状态校准，完成后不生成现金流台账和往来责任事实。
- 币种按已确认人民币基线处理，资金日报和余额调整使用公司/账户币种 `CNY`。

## Implementation

- 新增业务分类字典项：
  - `finance.fund.daily_report`
  - `finance.fund.balance_adjustment`
- `sc.treasury.ledger.source_kind` 增加 `daily_line`。
- `sc.fund.account.operation.action_done()` 对 `fund_daily_report` 按收入/支出生成幂等来源级现金流台账。
- `sc.fund.account` 增加当前账面余额、当前银行余额、余额日期、余额来源和来源单据。资金日报完成后更新账面/银行余额；余额调整完成后只更新账面余额。
- `fresh_db_fund_account_projection_write.py` 已按“最新资金日报余额优先，否则期初余额”初始化正式账户当前余额，保证新库重放路径不丢账户余额。
- `finance_business_category_runtime_audit.py` 增加两个分类的 action/domain/context 运行时验证。
- `fund_daily_handling_audit.py` 验证资金日报生成两条现金流台账、回写账户余额；余额调整不生成现金流但回写账户账面余额；两者均不泄漏到往来事实。
- `fund_account_balance_backfill_readiness_audit.py` 审计当前库历史账户余额初始化覆盖率，比较账面余额、银行余额、余额来源和余额日期。
- `fund_account_balance_backfill_write.py` 按 readiness 同一口径初始化当前库历史正式账户余额，只更新 `source_origin='legacy'` 的正式资金账户余额状态。

## Evidence

```text
DB_NAME=sc_demo make verify.fund_daily.handling.audit
FUND_DAILY_HANDLING_AUDIT: status=PASS
daily_report ledger_count=2 interfund_count=0 account_balance=1000.0 bank_balance=1000.0
balance_adjustment ledger_count=0 interfund_count=0 account_balance=520.0
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
category_count=54
covered: finance.fund.daily_report, finance.fund.balance_adjustment
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
covered: finance.fund.daily_report, finance.fund.balance_adjustment
```

```text
DB_NAME=sc_demo make verify.interfund_user_data.full_coverage.audit
INTERFUND_USER_DATA_FULL_COVERAGE_AUDIT: status=PASS
fund_daily_report source_count=7453
balance_adjustment source_count=519
interfund leak count=0
```

```text
DB_NAME=sc_demo make verify.fund_account.balance_backfill_readiness.audit
FUND_ACCOUNT_BALANCE_BACKFILL_READINESS_AUDIT: status=PASS
formal_legacy_account_count=111
latest_daily_matched_count=46
latest_daily_missing_count=65
no_daily_no_opening_count=61
current_state_mismatch_count=0
policy=latest fund daily line, then opening balance
```

```text
DB_NAME=sc_demo make backfill.fund_account.balance
FUND_ACCOUNT_BALANCE_BACKFILL_WRITE: status=PASS
updated_account_count=111
before.current_state_mismatch_count=111
after.current_state_mismatch_count=0
```

## Next

- 转账类账户余额扣加必须等待期初余额和历史账户明细基线确认后再启用，避免用不完整余额制造错误账户状态。
- 对资金日报入口补浏览器或 HTTP/API 用户可见面抽样。
- 后续资金日报汇总分析仍在报表阶段处理，但只能读取办理链路沉淀事实和历史快照，不替代资金日报登记入口。
