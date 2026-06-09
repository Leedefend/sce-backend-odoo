# Field Operation Action Audit 2026-06-09

## Scope

在财务与资金动作覆盖后，继续验证施工生产侧正式业务入口是否具备可办理动作链路。

本轮覆盖：

- 劳务用工：提交、确认
- 劳务结算：提交、确认
- 机械使用：提交、确认
- 机械结算：提交、确认
- 分包计划、分包申请、分包登记、分包结算
- 周转材料租赁计划、租赁单、租赁结算、付款状态
- 质量问题：提交、整改、复查、关闭
- 安全问题：提交、整改、复查、关闭
- 安全方案与安全交底：提交、批准

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_field_operation_actions.sh
```

## Result

```text
FIELD_OPERATION_ACTION_AUDIT: {"audit": "field_operation_action_audit", "coverage": {"equipment": {"settlement": 3, "usage": 17505}, "labor": {"settlement": 4, "usage": 9051}, "material_rental": {"order": 248, "plan": 5, "settlement": 6}, "quality_safety": {"quality_issue": 3, "safety_disclosure": 3, "safety_issue": 3, "safety_plan": 4}, "subcontract": {"plan": 4, "register": 3, "request": 724, "settlement": 3}}, "failures": [], "status": "PASS"}
```

## Notes

- 脚本只创建专项审计数据并调用正式模型动作，不修改菜单体系，不覆盖用户确认数据。
- 审计包含关键负向校验，例如确认前必须提交、批准前必须提交等状态跳转拦截。
- 本轮与前两轮审计共同构成：核心闭环、财务动作、施工生产动作三层办理能力验收。
