# 模型映射 v1（主线/投影/支撑/可删）

逐文件确认模型归属与关键字段，作为后续重构/删除的“拆除许可证”。

| 文件路径 | 主要模型(_name) | 主线位置 | 分类 | 权威字段 | 依赖/下游 |
| --- | --- | --- | --- | --- | --- |
| models/core/project_core.py | project.project, project.wbs, project.node 等 | 项目 | 主线 | 项目结构字段、boq_line_ids | 合同、采购、预算、结算、成本域引用 project_id/WBS |
| models/core/project_contract.py | construction.contract | 合同(收/支) | 主线 | amount_total, partner_id, type | 采购/结算/付款引用 contract_id |
| models/core/purchase_extend.py | purchase.order 扩展 | 采购/分包 | 主线 | amount_total, project_id, state | 结算、成本域、3WAY 校验 |
| models/core/material_plan.py | material.plan 等 | 采购前置 | 主线 | plan lines | RFQ 转换、采购 |
| models/core/boq.py | project.boq.line 等 | 成本清单 | 主线 | quantity, amount | 预算行、任务、WBS 关联 |
| models/core/cost_domain.py | project.budget.boq.line 等 | 成本域/分摊 | 主线 | budget_boq_line_id, amount | 预算分摊、成本报表 |
| models/core/project_budget.py | project.budget, project.budget.line | 预算 | 主线 | amount_*，boq_line_id | 成本域、报表 |
| models/core/project_project_financial.py | project.project 财务扩展 | 项目财务 | 主线 | financial fields | 报表、看板 |
| models/core/settlement_order.py | sc.settlement.order | 结算 | 主线 | amount_total, amount_paid, amount_payable | 付款申请、validator、3WAY |
| models/core/settlement.py | sc.settlement.order 辅助 | 结算 | 支撑 | 状态/行为 | 结算流程 |
| models/core/payment_request.py | payment.request | 资金/付款 | 主线 | amount, settlement_id, is_overpay_risk | 门禁、validator、台账 |
| models/core/project_extend_boq.py | project.extend.boq.* | BOQ 扩展 | 支撑 | 扩展字段 | BOQ 相关视图 |
| models/core/project_task_from_boq.py / task_boq_views | 任务生成 | 支撑 | - | 任务生成 | 任务、WBS |
| models/core/project_structure_views（XML） | - | 结构视图 | 支撑 | - | UI |
| models/projection/profit_report.py | profit.report | 投影 | 投影 | 计算字段 | 看板/报表 |
| models/projection/cost_report.py | cost.report | 投影 | 投影 | 计算字段 | 看板/报表 |
| models/projection/treasury_ledger.py | sc.treasury.ledger | 资金流水 | 投影 | amount, direction | 付款/收款完成后记录 |
| models/support/base_dictionary.py | sc.dictionary.* | 资料 | 支撑 | 字典字段 | 选择项 |
| models/support/project_dictionary.py | project.dictionary.* | 资料 | 支撑 | - | 选择项 |
| models/support/budget_compat.py | project.budget.line(兼容) | 兼容 | 支撑 | 继承 project.budget.boq.line | 老库升级 |
| models/support/account_extend.py | account.* 扩展 | 财务扩展 | 支撑 | - | 记账辅助 |
| models/support/stock_extend.py | stock.* 扩展 | 库存扩展 | 支撑 | - | 采购/库存 |
| models/support/product_extend.py | product.* 扩展 | 资料扩展 | 支撑 | - | 物料档案 |
| models/support/quota_spec.py | quota.spec.* | 资料 | 支撑 | QUOTA_SPEC | 导入向导 |
| models/support/account_move_line_ext.py | account.move.line 扩展 | 财务扩展 | 支撑 | - | 报表口径 |
| models/support/contract_center.py | contract.* 辅助 | 合同辅助 | 支撑 | boq_line_id 等 | 合同/BOQ 同步 |
| models/support/document_center.py | sc.document.* | 文档 | 支撑 | - | 文档中心 |
| models/support/task_extend.py | project.task 扩展 | 任务 | 支撑 | boq_line_ids | 任务成本 |
| models/support/work_breakdown.py | work.breakdown.* | WBS/拆分 | 支撑 | boq_line_ids | 成本分摊/任务 |
| models/support/tender.py | tender.* | 招投标 | 支撑 | - | 项目前置 |
| models/support/res_config_settings.py | res.config.settings 扩展 | 配置 | 支撑 | - | 配置项 |
| models/support/tier_definition_ext.py | tier.* 扩展 | 审批 | 支撑 | - | 审批流 |
| models/support/sc_workflow.py | sc.workflow.* | 审批/流程 | 支撑 | - | 流程控制 |
| models/support/sc_data_validator.py | sc.data.validator | 护栏 | 支撑 | validate_or_raise | 门禁、validator |

说明：
- “主线位置”按经营流：项目/合同/预算/成本/资金/护栏。
- “可删”目前为空；未来标记后可作为拆除依据。
- 兼容模型：`project.budget.line` 仍存在，勿删除。
