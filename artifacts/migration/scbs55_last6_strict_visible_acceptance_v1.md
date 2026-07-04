# SCBS55 Last 6 Strict Visible Acceptance v1

- status: PASS
- frontend_url: http://1.95.85.92:18081
- db_name: sc_demo
- login: wutao
- checked_count: 6
- failure_count: 0

| key | name | action | expected | new count | headers | identities | status |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| self_guarantee | 自筹保证金 | 868 | 1580 | 1580 | PASS | PASS | PASS |
| self_guarantee_refund | 自筹保证金退回 | 869 | 823 | 823 | PASS | PASS | PASS |
| self_funding_income | 自筹垫付收入 | 901 | 2141 | 2141 | PASS | PASS | PASS |
| self_funding_refund | 自筹垫付退回 | 902 | 827 | 827 | PASS | PASS | PASS |
| engineering_progress_receipt | 工程进度收款 | 899 | 3259 | 3259 | PASS | PASS | PASS |
| supplier_contract | 供货合同 | 900 | 5565 | 5565 | PASS | PASS | PASS |

## Failures

```json
[]
```
