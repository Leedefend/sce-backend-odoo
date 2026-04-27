# Business Expense/Settlement OCA Unification Batch - 2026-04-27

## Scope

- Layer Target: `Business approval OCA execution unification`
- Module: `smart_construction_core`
- Reason: `审批配置只决定是否需要审核，审核执行统一交给 OCA tier.validation；启用审批进入统一审批，取消审批则直接进入业务批准态。`

## Changes

- `sc.expense.claim` 接入 `mail.thread`、`mail.activity.mixin`、`tier.validation`，提交后按配置进入 OCA 审批或直达 `approved`。
- `sc.settlement.order` 接入 `tier.validation`，提交后按配置进入 OCA 审批或直达 `approve`。
- 新增费用/保证金、结算单 OCA 审批通过/驳回 server action。
- 审批规则同步支持 `sc.expense.claim`、`sc.settlement.order`，模块升级时把这两类规则 runtime 收口为 `tier_validation` 并生成 active tier definition。
- `business_oca_runtime_smoke.py` 扩展覆盖付款申请、物资计划、费用/保证金、结算单四类业务的通过/驳回链路。

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/core/expense_claim.py addons/smart_construction_core/models/core/settlement_order.py addons/smart_construction_core/models/support/approval_policy.py scripts/verify/business_oca_runtime_smoke.py scripts/verify/business_document_state_policy_switch_smoke.py`
- `python3 xml.etree.ElementTree parse` for new/changed XML files.
- `git diff --check`
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_construction_core`
- `ENV=test ENV_FILE=.env.prod.sim ... make verify.business.oca_runtime_smoke`
- `ENV=test ENV_FILE=.env.prod.sim ... make verify.business.document_state_policy_switch`
- `APPROVAL_POLICY_RUNTIME`: expense, settlement, payment request, material plan all `runtime=tier_validation`, `tier_defs=1`, `active=1`.

## Result

- PASS.
- 费用/保证金：启用审批时 `submit -> OCA -> approved`，驳回回到 `draft` 并保留驳回原因；取消审批时提交直达 `approved`。
- 结算单：启用审批时 `submit -> OCA -> approve`，驳回回到 `draft` 并保留驳回原因；取消审批时提交直达 `approve`。
- 当前模拟生产库中费用/结算 submitter 与 reviewer 均选到 `chenshuai`，说明真实可用用户能力组还需要后续按职责分离补齐，但执行链路已统一。

## Rollback

- 回退本批 commit。
- 重新执行 `make mod.upgrade MODULE=smart_construction_core`。
