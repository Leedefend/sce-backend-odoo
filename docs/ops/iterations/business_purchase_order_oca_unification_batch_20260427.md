# Business Purchase Order OCA Unification Batch - 2026-04-27

## Scope

- Layer Target: `Business approval OCA execution unification`
- Module: `smart_construction_core`
- Reason: `采购订单确认必须与其他业务单据一致：业务发起人可发起，审核由采购审批能力组通过统一 OCA tier.validation 执行。`

## Changes

- `purchase.order` 接入 `tier.validation`，保留原生 `button_confirm` 作为用户入口。
- 启用审批时，业务发起人点击确认只提交统一审批，不直接确认采购订单。
- OCA 审批通过回调调用原生采购确认，采购订单进入 `purchase/done`。
- OCA 审批驳回保留采购订单草稿态，并记录驳回原因。
- 取消审批时，采购订单仍直接走原生确认。
- 采购订单确认按钮开放给业务发起人、采购办理、采购审核能力组；审核动作仍由 OCA review 的采购经理能力组控制。
- 审批规则同步支持 `purchase.order`，并生成采购订单 active tier definition。

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/core/purchase_extend.py addons/smart_construction_core/models/support/approval_policy.py addons/smart_construction_core/models/support/tier_definition_ext.py scripts/verify/business_oca_runtime_smoke.py scripts/verify/business_document_state_policy_switch_smoke.py`
- `python3 xml.etree.ElementTree parse` for purchase action/view/seed XML.
- `git diff --check`
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_construction_core`
- `ENV=test ENV_FILE=.env.prod.sim ... make verify.business.oca_runtime_smoke`
- `ENV=test ENV_FILE=.env.prod.sim ... make verify.business.document_state_policy_switch`
- `APPROVAL_POLICY_RUNTIME=purchase.order required=True mode=single runtime=tier_validation tier_defs=1 active=1`

## Result

- PASS.
- `PURCHASE_OCA_ACTORS=caisiqi->chenshuai`
- 启用审批：`draft/waiting -> validate_tier -> purchase/validated`。
- 驳回：`draft/waiting -> reject_tier -> draft/rejected`，保留驳回原因。
- 取消审批：非审核用户确认采购订单可直达 `purchase`。

## Rollback

- 回退本批 commit。
- 重新执行 `make mod.upgrade MODULE=smart_construction_core` 并重启模拟生产服务。
