# Business Approval Policy OCA Tier Sync Batch - 2026-04-27

## Scope

- Layer Target: Domain approval configuration sync
- Module: `smart_construction_core`
- Reason: 将业务配置管理员维护的 `sc.approval.policy` 作为配置源，同步到 OCA `tier.definition` 执行层，先覆盖已接入 OCA 的物资计划和付款/收款申请。

## Facts

- `project.material.plan` 和 `payment.request` 已继承 `tier.validation` 并调用 `request_validation()`。
- 升级前模拟库中 `tier.definition` 数量为 0，说明 OCA 执行层没有由业务配置生成审批定义。
- OCA `tier.definition` 可映射字段：
  - `model_id` / `model`
  - `review_type = group`
  - `reviewer_group_id`
  - `definition_type = domain`
  - `definition_domain`
  - `server_action_id`
  - `rejected_server_action_id`

## Changes

- `sc.approval.step` 新增 `tier_definition_id`，保存同步生成的 OCA 审批定义。
- `sc.approval.policy` 新增同步方法：
  - `sync_tier_definitions`
  - `sync_all_tier_definitions`
- 策略/步骤创建、修改、删除时同步 OCA `tier.definition`。
- 新增 `data/approval_policy_tier_sync.xml`，模块升级时执行全量同步。
- 当前同步范围：
  - `project.material.plan`
  - `payment.request`

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/support/approval_policy.py addons/smart_construction_core/__manifest__.py`
- `python3 -m xml.etree.ElementTree addons/smart_construction_core/data/approval_policy_seed.xml addons/smart_construction_core/data/approval_policy_tier_sync.xml`
- `git diff --check`
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_construction_core`
- OCA sync smoke:
  - `POLICY_OCA_SYNC_COUNT=2`
  - `TIER_DEFINITION_TOTAL=2`
  - `payment.request -> 财务中心审批 -> 付款申请审批通过/驳回回调`
  - `project.material.plan -> 物资中心审批 -> 物资计划审批通过/驳回回调`
  - `SYNC_AFTER_STEP_WRITE_DOMAIN=[('amount', '>=', 123.45)]`
  - `POLICY_OCA_SYNC_SMOKE=PASS`
- Business admin write smoke:
  - `BUSINESS_ADMIN_POLICY_WRITE=PASS`
  - `BUSINESS_ADMIN_TIER_DOMAIN=[('amount', '>=', 321.0)]`
- OCA execution smoke:
  - `MATERIAL_PLAN_TIER_SUBMIT_STATE=submit`
  - `MATERIAL_PLAN_TIER_REVIEW_COUNT=1`
  - `MATERIAL_PLAN_TIER_REVIEW_GROUPS=Smart Construction / SC 能力 - 物资中心审批`
  - `MATERIAL_PLAN_TIER_SMOKE=PASS`
- Restart and navigation:
  - `ENV=test ENV_FILE=.env.prod.sim ... make restart`
  - `ENV=test ENV_FILE=.env.prod.sim ... E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=143 scenes=16 trace=f57b4d342459`

## Next

- 继续验证付款/收款申请带附件提交后创建 OCA 待审，并完成财务审核通过/驳回链路。
- 评估是否将更多 `document_state` 单据逐步改造为 `tier.validation` 执行，而不是扩展自研审批引擎。
