# User Confirmed Settlement Usability 2026-06-10

## Scope

专项补齐直管验收结算数据进入正式 `sc.settlement.order` 后的办理可用性字段。

覆盖：

- 材料结算单
- 机械结算单
- 劳务结算
- 分包结算单
- 工程结算单

## Backfill

```text
USER_CONFIRMED_SETTLEMENT_USABILITY_BACKFILL: {"copied_fields": 337, "missing_fact_count": 0, "missing_fact_sample": [], "operation": "user_confirmed_settlement_usability_backfill", "settlement_count": 2593, "status": "PASS", "updated": 337, "updated_by_label": {"分包结算单": 12, "劳务结算": 85, "机械结算单": 62, "材料结算单": 178}}
```

前置回填已补齐 2593 条结算单的业务分类和验收可见字段。

## Audit

```text
USER_CONFIRMED_SETTLEMENT_USABILITY_AUDIT: {"audit": "user_confirmed_settlement_usability_audit", "by_label": {"分包结算单": 88, "劳务结算": 576, "工程结算单": 37, "机械结算单": 669, "材料结算单": 1223}, "failures": [], "settlement_count": 2593, "status": "PASS"}
```

## Release Gate

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS db=sc_demo started_at=2026-06-10T00:00:44+08:00 finished_at=2026-06-10T00:03:04+08:00
```

关键数据对齐结果：

- 用户确认正式菜单：`62`
- 检查记录：`256844`
- 检查字段：`861`
- 不一致字段：`0`
- 只读来源字段未承接：`0`

## Policy

- 不改用户已确认菜单体系。
- 不覆盖用户已验收列表值。
- 回填只针对直管验收结算单缺失的正式承接字段。
