# SCBS Negative Payment Semantics Report

Status: `PASS`

## Summary

| Classification | Rows | Amount | Abs Amount |
| --- | ---: | ---: | ---: |
| negative_without_text_semantics | 107 | -31195539.43 | 31195539.43 |
| account_or_internal_adjustment | 44 | -27710200.00 | 27710200.00 |
| refund_or_return | 67 | -4797262.89 | 4797262.89 |

## Judgment

- These rows have confirmed project anchors, but their amounts are negative.
- They must not be written into `sc.payment.execution`, which represents positive payment execution.
- Rows with refund/return or adjustment wording need a future refund/reversal/adjustment carrier before formal write.
- Rows without text semantics remain historical negative payment residuals until source-chain semantics are confirmed.
