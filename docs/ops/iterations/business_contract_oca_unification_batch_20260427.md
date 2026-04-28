# Batch-Business-Contract-OCA-Unification

## 1. 本轮变更
- 目标：补齐项目合同、一般合同、采购/一般合同的统一 OCA 审批执行层。
- 完成：
  - `construction.contract`、`sc.general.contract`、`sc.legacy.purchase.contract.fact` 接入 `tier.validation`。
  - 新增三类合同 OCA 审批通过/驳回回调动作。
  - 审批策略同步支持三类合同模型，并将种子策略运行态收口为 `tier_validation`。
  - 合同表单展示驳回原因，确认/提交入口保持业务发起人可办理，审核仍由对应 manager 能力组通过 OCA review 控制。
  - `business_oca_runtime_smoke` 与 `business_document_state_policy_switch_smoke` 扩展覆盖三类合同。
- 未完成：发票登记当前策略仍为 `approval_required=False`，未纳入本批统一审批覆盖。

## 2. 影响范围
- 模块：`addons/smart_construction_core`、`scripts/verify`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无。
- P1：合同审批通过后进入确认态，签署/执行仍按原业务按钮继续办理，需要下一轮做端到端连续办理矩阵。
- P2：历史合同存量的公司字段按项目关联回填，缺项目的采购/一般合同会落空公司，但审批策略可按全局规则匹配。

## 4. 验证
- `python3 -m py_compile addons/smart_construction_core/models/support/contract_center.py addons/smart_construction_core/models/core/general_contract.py addons/smart_construction_core/models/support/legacy_purchase_contract_fact.py addons/smart_construction_core/models/support/approval_policy.py addons/smart_construction_core/models/support/tier_definition_ext.py scripts/verify/business_oca_runtime_smoke.py scripts/verify/business_document_state_policy_switch_smoke.py`
- `python3 xml.etree.ElementTree parse for contract_tier_actions.xml, approval_policy_seed.xml, contract/general/legacy purchase views`
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_core`
- `make verify.business.oca_runtime_smoke`
- `make verify.business.document_state_policy_switch`
- 结果：PASS。

## 5. 产物
- snapshot：N/A
- logs：命令输出已记录在本轮 Codex 会话。
- e2e：N/A

## 6. 回滚
- commit：回退本批提交。
- 方法：回退代码后执行 `make mod.upgrade MODULE=smart_construction_core` 并重启模拟生产服务。

## 7. 下一批次
- 目标：基于当前八类 OCA 可审批业务，输出真实用户业务办理矩阵与缺口判断。
- 前置条件：使用模拟生产库，保持 `smart_construction_core` 已升级。
