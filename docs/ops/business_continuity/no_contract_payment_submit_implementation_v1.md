# No-Contract Payment Submit Implementation v1

## 目的

承接旧业务事实中的企业日常支出场景：付款申请在未选择结算单时，可以不强制选择合同继续提交。

## 规则边界

- 未选择合同、未选择结算单：允许按原有附件、资金、项目生命周期、数据校验、审批链继续提交。
- 已选择合同：继续校验合同未作废。
- 已选择结算单：仍必须选择关联合同，避免结算付款绕过合同一致性。
- 不改变付款金额、结算额度、资金基线、tier validation、审计、凭证、ACL、会计和前端逻辑。

## 修改点

- `payment.request.action_submit` 复用 `_check_contract_submit_gate()` 处理合同/结算提交门槛。
- `payment.request.available_actions` 调用同一门槛，避免前端按钮可用性与真实提交动作分裂。

## 验证

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-NO-CONTRACT-PAYMENT-SUBMIT-IMPLEMENT.yaml`
- `python3 -m py_compile addons/smart_construction_core/models/core/payment_request.py addons/smart_construction_core/handlers/payment_request_available_actions.py`
- `DB_NAME=sc_demo make odoo.shell.exec` rollback-only no-contract submit check: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` rollback-only selected-contract submit check: PASS
- `DB_NAME=sc_demo make odoo.shell.exec` selected-settlement consistency check: PASS
- `DB_NAME=sc_demo make verify.imported_business_continuity.v1`: PASS

## 回滚

```bash
git restore addons/smart_construction_core/models/core/payment_request.py \
  addons/smart_construction_core/handlers/payment_request_available_actions.py \
  docs/ops/business_continuity/no_contract_payment_submit_implementation_v1.md \
  agent_ops/tasks/ITER-2026-04-18-NO-CONTRACT-PAYMENT-SUBMIT-IMPLEMENT.yaml
```
