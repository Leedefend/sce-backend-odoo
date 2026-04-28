# Batch-Business-Approval-Scope-Config

## 1. 本轮变更
- 目标：让业务系统管理员按业务语言配置审批人范围，避免在审批规则页面理解底层能力组。
- 完成：
  - `sc.approval.policy` 新增 `默认审批岗位`，映射到底层 `manager_group_id`。
  - `sc.approval.step` 新增 `审批岗位`，映射到底层 `approve_group_id`。
  - 审批规则页面隐藏底层执行组字段，只展示项目负责人、物资审核人、采购审核人、财务审核人、合同审核人、成控审核人、结算审核人。
  - 种子规则补齐审批岗位键，保留原有 OCA 执行组兼容。
- 未完成：暂未开放“直接指定人员”，本批只做审批岗位业务化表达。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无。
- P1：自定义非标准审批组不会出现在业务下拉项中，需要后续扩展审批岗位字典。
- P2：底层字段仍保留在模型中，技术管理员可通过开发者模式查看。

## 4. 验证
- `python3 -m py_compile addons/smart_construction_core/models/support/approval_policy.py`
- `python3 xml.etree.ElementTree parse for approval_policy_views.xml, approval_policy_seed.xml`
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_core`
- `make odoo.shell.exec` 回滚式验证既有 8 类策略审批岗位回填、新建步骤按审批岗位映射到 OCA reviewer group。
- `make verify.business.oca_runtime_smoke`
- 结果：PASS。

## 5. 产物
- snapshot：N/A
- logs：命令输出已记录在本轮 Codex 会话。
- e2e：N/A

## 6. 回滚
- commit：回退本批提交。
- 方法：回退代码后执行 `make mod.upgrade MODULE=smart_construction_core`，审批规则页面恢复直接选择底层执行组。

## 7. 下一批次
- 目标：继续输出真实用户业务办理矩阵，核对业务连续办理缺口。
- 前置条件：模拟生产库已完成模块升级。
