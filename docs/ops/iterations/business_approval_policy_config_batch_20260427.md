# Business Approval Policy Config Batch - 2026-04-27

## Scope

- Layer Target: Domain Layer / business approval configuration facts
- Module: `smart_construction_core`
- Reason: 业务系统需要回答“哪些业务需要审核、审核流程是什么”，且该能力应由业务配置管理员按业务需要维护，不应收窄普通内部用户的业务发起能力。

## Existing Facts

- `project.material.plan` 和 `payment.request` 已接入 `tier.validation`，提交后进入分级审批。
- `sc.workflow.*` 工作流模型已存在，但当前归平台系统管理员配置，且没有作为业务管理员可维护的审批矩阵暴露。
- 多个业务单据仍按单据状态按钮执行审核/确认，例如合同、采购、结算、费用等。

## Changes

- 新增 `sc.approval.policy` / `sc.approval.step`，承载业务审批规则和审核步骤。
- 新增“业务配置 / 审批规则”菜单，仅业务配置管理员可维护，内部用户具备只读访问。
- 初始化默认审批矩阵：
  - 项目合同：需要审核，确认时，合同中心审批。
  - 一般合同：需要审核，确认时，合同中心审批。
  - 采购/一般合同：需要审核，确认时，采购中心审批，当前为仅配置规则。
  - 物资计划：需要审核，提交时，物资中心审批，已接入分级审批。
  - 采购订单：需要审核，确认时，采购中心审批。
  - 结算单：需要审核，提交时，结算中心审批。
  - 付款/收款申请：需要审核，提交时，财务中心审批，已接入分级审批。
  - 费用/保证金：需要审核，提交时，财务中心审批。
  - 发票登记：默认登记类业务，不强制审核。

## Verification

- `python3 -m py_compile addons/smart_construction_core/models/support/approval_policy.py addons/smart_construction_core/__manifest__.py`
- `python3 -m xml.etree.ElementTree addons/smart_construction_core/data/approval_policy_seed.xml addons/smart_construction_core/views/support/approval_policy_views.xml`
- `git diff --check`
- `ENV=test ENV_FILE=.env.prod.sim ... make mod.upgrade MODULE=smart_construction_core`
- `APPROVAL_POLICY_SYNCED=8`
- `APPROVAL_POLICY_COUNT=9`
- `APPROVAL_POLICY_MENU=True ACTION=True`
- `WUTAO_BUSINESS_CONFIG=True`
- `ENV=test ENV_FILE=.env.prod.sim ... make restart`
- `ENV=test ENV_FILE=.env.prod.sim ... E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=143 scenes=16 trace=f90582b57d44`

## Next

- 将 `runtime_state=policy_only` 或 `document_state` 的业务动作逐步接入 `sc.approval.policy`，使运行时按业务管理员配置判断是否需要审核。
- 保持业务发起入口对内部用户开放，审核通过/驳回/完成继续由对应审批能力组控制。
