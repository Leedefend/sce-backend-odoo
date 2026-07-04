# User Visible Business Fact Alignment Probe v1

Status: PASS
Database: sc_acceptance_audit_20260510

## Deterministic Lanes

| lane | status | payload identities | target identities | missing | permission gap |
| --- | --- | ---: | ---: | ---: | ---: |
| 项目主数据 | PASS | 818 | 891 | 0 | 0 |
| 往来单位主数据 | PASS | 6541 | 7170 | 0 | 0 |
| 合同台账事实 | PASS | 6793 | 6929 | 0 | 0 |
| 付款申请事实 | PASS | 24747 | 30784 | 0 | 0 |
| 收款事实 | PASS | 5355 | 30784 | 0 | 0 |
| 付款明细事实 | PASS | 31883 | 31883 | 0 | 0 |
| 发票登记明细事实 | PASS | 25393 | 25393 | 0 | 0 |
| 资金日报明细事实 | PASS | 7754 | 7754 | 0 | 0 |

## User Priority Plan

```json
{
  "expected_rows": 55,
  "group_counts": {
    "人事行政": 7,
    "付款": 2,
    "分析大屏": 2,
    "办公资料": 1,
    "发票税务": 6,
    "合同": 1,
    "基础资料": 2,
    "成本报表": 7,
    "扣款": 3,
    "投标": 2,
    "收支": 2,
    "收款": 1,
    "组织人员": 2,
    "证照资料": 2,
    "财税报表": 2,
    "费用报销": 1,
    "资金保证金": 4,
    "资金借还": 2,
    "资金日报": 1,
    "资金账户": 1,
    "项目资金": 4
  },
  "row_count": 55,
  "verified_count": 55
}
```

## Boundary

The probe checks old-system fact identities carried into the new database. It does not require old data to satisfy new customer/supplier or projection-only semantics when no deterministic legacy source key exists.
