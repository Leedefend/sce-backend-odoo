# Module Scene Capability Map V1

- version: v1
- module_count: 10
- delivery_scope_scene_count: 66
- assigned_scope_scene_count: 66
- unassigned_scope_scene_count: 0
- declared_model_count: 44
- declared_capability_count: 63
- unknown_scene_ref_count: 0
- unknown_capability_ref_count: 0
- error_count: 0
- warning_count: 0

## Acceptance

- module_count_le_10: PASS
- each_module_has_scene: PASS
- scope_scene_unassigned_eq_0: PASS
- unknown_scene_ref_eq_0: PASS
- unknown_capability_ref_eq_0: PASS

| module_key | module_name | core_value | target_roles | entry_scenes | models | capabilities |
|---|---|---|---|---|---|---|
| project_initiation_ledger | 项目立项与台账 | 完成项目立项、台账建立与基础资料归档。 | pm,purchase_manager | projects.intake,projects.ledger,projects.list | project.project | project.document.open,project.initiation.enter,project.lifecycle.open,project.list.open,project.structure.manage,workspace.project.watch |
| project_execution_collab | 项目执行与任务协同 | 跟踪项目执行进度、风险与周报，推动日常协同。 | pm | project.management,projects.dashboard,projects.execution,risk.center,risk.monitor,task.center | project.task,project.project | project.board.open,project.dashboard.enter,project.dashboard.open,project.execution.advance,project.execution.enter,project.plan_bootstrap.enter,project.risk.list,project.task.board,project.task.list,project.weekly_report.open,workspace.today.focus |
| purchase_material_collab | 采购与物资协同 | 实现材料档案、采购申请、验收、出入库、租赁和专业分包履约协同。 | purchase_manager,pm | cost.project_boq,equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement,material.acceptance,material.catalog,material.center,material.inbound,material.outbound,material.price_library,material.procurement,material.rental,material.rental_order,material.rental_settlement,material.rfq,material.settlement,subcontract.management,subcontract.register,subcontract.request,subcontract.settlement | sc.material.catalog,sc.material.purchase.request,sc.material.rfq,sc.material.acceptance,sc.material.inbound,sc.material.outbound,sc.material.price,sc.material.settlement,sc.material.rental.plan,sc.material.rental.order,sc.material.rental.settlement,sc.labor.plan,sc.labor.request,sc.attendance.checkin,sc.labor.settlement,sc.equipment.plan,sc.equipment.request,sc.equipment.usage,sc.equipment.settlement,sc.subcontract.plan,sc.subcontract.request,sc.subcontract.register,sc.subcontract.settlement | cost.boq.manage,equipment.plan.manage,equipment.request.list,equipment.settlement.list,equipment.usage.list,labor.attendance.list,labor.plan.manage,labor.request.list,labor.settlement.list,material.catalog.open,material.procurement.list,project.document.open |
| site_execution_quality_safety | 现场执行与质量安全 | 覆盖施工计划、计划汇报、施工日志、质量问题闭环和安全问题闭环。 | pm,executive | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center,safety.recheck,safety.rectification | sc.plan,sc.plan.report,sc.construction.diary,sc.quality.issue,sc.quality.rectification,sc.quality.recheck,sc.safety.issue,sc.safety.rectification,sc.safety.recheck | construction.diary.open,construction.plan.manage,construction.plan.report,quality.issue.list,quality.recheck.list,quality.rectification.list,safety.issue.list,safety.recheck.list,safety.rectification.list |
| payment_request_approval | 付款申请与审批 | 完成付款申请发起、审批中心处理与异常识别。 | finance,pm | finance.center,finance.payment_requests,finance.workspace | payment.request | finance.approval.center,finance.exception.monitor,finance.payment_request.form,finance.payment_request.list |
| funding_settlement_ledger | 资金与结算台账 | 沉淀支付、资金、结算全链路台账并支持对账。 | finance | finance.payment_ledger,finance.settlement_orders,finance.treasury_ledger | account.payment,settlement.order | finance.invoice.list,finance.ledger.payment,finance.ledger.treasury,finance.plan.funding,finance.settlement.order |
| cost_budget_profit | 成本预算与利润分析 | 覆盖预算、成本、利润与进度关联分析。 | pm,finance | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_budget,cost.project_cost_ledger,cost.project_progress | project.budget,project.cost.ledger | cost.budget.manage,cost.ledger.open,cost.profit.compare,cost.progress.report |
| executive_dashboard | 经营指标与领导看板 | 为管理层提供经营指标、项目全局与异常洞察。 | executive | finance.operating_metrics,portal.dashboard | operating.metrics | analytics.dashboard.executive,analytics.exception.list,analytics.project.focus,finance.metrics.operating |
| lifecycle_governance | 生命周期与治理审计 | 保障能力矩阵、生命周期治理与审计可追溯。 | admin,executive | portal.capability_matrix,portal.lifecycle | capability.registry,scene.registry | analytics.lifecycle.monitor,contract.settlement.audit,governance.capability.matrix,governance.runtime.audit,governance.scene.openability |
| masterdata_workspace | 主数据与工作台 | 统一字典配置、默认工作台入口与基础数据管理。 | pm,finance,purchase_manager,executive | contract.center,contracts.workspace,data.dictionary,my_work.workspace,workspace.home | ir.model.data,res.users | contract.center.open,contract.expense.track,contract.income.track,project.lifecycle.transition |

## Diagnostics

- warnings: none
- errors: none
