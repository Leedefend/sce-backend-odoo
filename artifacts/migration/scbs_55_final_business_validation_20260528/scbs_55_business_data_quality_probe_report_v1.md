# SCBS 55 Business Data Quality Probe v1

Status: PASS_WITH_SCHEMA_RECHECK
Database: sc_demo
Generated At: 2026-05-28T08:21:30.277772+00:00

| seq | entry | old active | delivered active | user excluded | unexplained gap | status | note |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 5 | 请假/休假审批单 | 339 | 339 | 0 | 0 | PASS |  |
| 6 | 印章使用审批表 | 1565 | 1565 | 0 | 0 | PASS |  |
| 9 | 社保人员登记 | 156 | 156 | 0 | 0 | PASS |  |
| 13 | 奖金 | 0 | 0 | 0 | 0 | PASS |  |
| 35 | 到款确认表-旧单据事实 | 2595 | 2595 | 0 | 0 | PASS | 旧库 ZJGL_SZQR_DKQRB 单据级事实；用户可见金额已按 KPSKQK_BQS。 |
| 35 | 到款确认表-用户收入入口 | 2556 | 2556 | 0 | 0 | PASS | 单据级投影；旧明细级 active 必须为 0，active 单据不得重复。 |
| 41 | 预缴税款 | 5395 | 5390 | 5 | 0 | PASS | 2026-05-27 用户确认旧项目缺失的 5 条不交付；用户树视图已移除旧系统不可见空列。 |
| 44 | 外经证登记 | 317 | 317 | 0 | 0 | PASS | 附件 fallback 已改为 legacy-file 链接，不再裸露 hash 作为附件名。 |
| 46 | 库存统计表（新）-材料库存事实 | 16389 | 16389 | 0 | 0 | PASS | 旧库材料出入库事实层已落地；用户报表使用汇总视图过滤无材料和 inactive 项目。 |
| 46 | 库存统计表（新）-用户汇总入口 | 14 | 14 | 0 | 0 | PASS_WITH_SCHEMA_RECHECK | 数量和脏数据过滤已闭合；旧 LowCode/Report 利润字段已承载，仍需复核日期和项目过滤口径。 |

## Metrics

```json
[
  {
    "delivered_active": 339,
    "delivered_rows": 347,
    "entry": "请假/休假审批单",
    "metrics": {},
    "note": "",
    "old_active": 339,
    "old_rows": 347,
    "seq": 5,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 1565,
    "delivered_rows": 1565,
    "entry": "印章使用审批表",
    "metrics": {},
    "note": "",
    "old_active": 1565,
    "old_rows": 1565,
    "seq": 6,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 156,
    "delivered_rows": 167,
    "entry": "社保人员登记",
    "metrics": {},
    "note": "",
    "old_active": 156,
    "old_rows": 167,
    "seq": 9,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 0,
    "delivered_rows": 0,
    "entry": "奖金",
    "metrics": {},
    "note": "",
    "old_active": 0,
    "old_rows": 0,
    "seq": 13,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 2595,
    "delivered_rows": 2595,
    "entry": "到款确认表-旧单据事实",
    "metrics": {},
    "note": "旧库 ZJGL_SZQR_DKQRB 单据级事实；用户可见金额已按 KPSKQK_BQS。",
    "old_active": 2595,
    "old_rows": 2655,
    "seq": 35,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 2556,
    "delivered_rows": 2556,
    "entry": "到款确认表-用户收入入口",
    "metrics": {
      "duplicate_active_documents": 0,
      "line_grain_active": 0
    },
    "note": "单据级投影；旧明细级 active 必须为 0，active 单据不得重复。",
    "old_active": 2556,
    "old_rows": 2556,
    "seq": 35,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 5390,
    "delivered_rows": 7215,
    "entry": "预缴税款",
    "metrics": {
      "active_attachment": 5390,
      "active_no_cert": 736,
      "active_no_tax_type": 34,
      "active_zero_amount": 43
    },
    "note": "2026-05-27 用户确认旧项目缺失的 5 条不交付；用户树视图已移除旧系统不可见空列。",
    "old_active": 5395,
    "old_rows": 5455,
    "seq": 41,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 5
  },
  {
    "delivered_active": 317,
    "delivered_rows": 318,
    "entry": "外经证登记",
    "metrics": {},
    "note": "附件 fallback 已改为 legacy-file 链接，不再裸露 hash 作为附件名。",
    "old_active": 317,
    "old_rows": 318,
    "seq": 44,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 16389,
    "delivered_rows": 20922,
    "entry": "库存统计表（新）-材料库存事实",
    "metrics": {},
    "note": "旧库材料出入库事实层已落地；用户报表使用汇总视图过滤无材料和 inactive 项目。",
    "old_active": 16389,
    "old_rows": 20922,
    "seq": 46,
    "status": "PASS",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  },
  {
    "delivered_active": 14,
    "delivered_rows": 14,
    "entry": "库存统计表（新）-用户汇总入口",
    "metrics": {
      "no_material_rows": 0,
      "no_project_name_rows": 0,
      "price_diff_sum": 0.0,
      "profit_amount": 0.0,
      "stock_amount": 78749.28,
      "test_project_rows": 0
    },
    "note": "数量和脏数据过滤已闭合；旧 LowCode/Report 利润字段已承载，仍需复核日期和项目过滤口径。",
    "old_active": 14,
    "old_rows": 14,
    "seq": 46,
    "status": "PASS_WITH_SCHEMA_RECHECK",
    "unexplained_gap": 0,
    "user_confirmed_excluded": 0
  }
]
```
