# Business Flow Closure Audit 2026-06-09

## Scope

专项验证用户确认数据进入正式业务模型后，系统是否具备可继续办理的核心闭环能力。

本轮覆盖两条链路：

- 合同、结算、付款、付款台账、合同联营/对账汇总
- 材料采购申请、材料验收、材料入库、材料出库、材料询比价、材料结算

## Command

```bash
DB_NAME=sc_demo scripts/ops/validate_business_flow_closure.sh
```

## Result

```text
BUSINESS_FLOW_CLOSURE_AUDIT: {"audit": "business_flow_closure_audit", "failures": [], "flows": {"contract_payment": {"contract": 11772, "ledger": 12201, "payment": 35825, "recon_summary": 1, "settlement": 2768}, "material_stock_settlement": {"acceptance": 3, "inbound": 13642, "outbound": 6, "request": 3, "rfq": 129, "settlement": 3}}, "status": "PASS"}
```

## Notes

- 开发库先执行了 `smart_construction_core` 模块升级，修复代码字段已存在但 `sc_demo` 表结构未更新的问题。
- 验收脚本只创建专项审计数据并调用正式模型动作，不修改菜单体系和用户已确认的可见数据。
- 脚本包含错误路径校验，例如未提交直接完成结算/付款、未提交直接入库/结算等状态跳转会被正式模型拦截。
