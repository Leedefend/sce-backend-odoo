# Scene Compression Model v1

- objective: compress runtime scenes into product-facing domains (<=25)
- runtime_scene_count: 66
- canonical_scene_count: 66
- domain_count: 9
- taxonomy_domain_count: 9
- unassigned_scene_count: 0
- unknown_domain_count: 0
- fallback_domain_scene_count: 0
- error_count: 0
- warning_count: 0

## Acceptance

- all_scene_assigned: PASS
- domain_count_le_25: PASS
- zero_unknown_domain: PASS
- zero_fallback_domain_scene: PASS

## Domain Mapping

| domain | runtime_scene_count | canonical_scene_count | sample_scenes |
|---|---:|---:|---|
| contract_workspace | 2 | 2 | contract.center,contracts.workspace |
| cost_control | 8 | 8 | cost.analysis,cost.budget_alloc,cost.cost_compare,cost.profit_compare,cost.project_boq,cost.project_budget,cost.project_cost_ledger,cost.project_progress |
| data_foundation | 1 | 1 | data.dictionary |
| finance_operations | 7 | 7 | finance.center,finance.operating_metrics,finance.payment_ledger,finance.payment_requests,finance.settlement_orders,finance.treasury_ledger,finance.workspace |
| portal_governance | 3 | 3 | portal.capability_matrix,portal.dashboard,portal.lifecycle |
| procurement_supply | 24 | 24 | equipment.management,equipment.request,equipment.settlement,equipment.usage,labor.attendance,labor.management,labor.request,labor.settlement |
| project_execution | 9 | 9 | project.management,projects.dashboard,projects.execution,projects.intake,projects.ledger,projects.list,risk.center,risk.monitor |
| site_quality_safety | 10 | 10 | construction.diary,construction.execution,construction.plan,construction.plan_report,quality.center,quality.recheck,quality.rectification,safety.center |
| workspace_shell | 2 | 2 | my_work.workspace,workspace.home |

## Scene -> Domain

- construction.diary -> site_quality_safety (canonical=construction.diary)
- construction.execution -> site_quality_safety (canonical=construction.execution)
- construction.plan -> site_quality_safety (canonical=construction.plan)
- construction.plan_report -> site_quality_safety (canonical=construction.plan_report)
- contract.center -> contract_workspace (canonical=contract.center)
- contracts.workspace -> contract_workspace (canonical=contracts.workspace)
- cost.analysis -> cost_control (canonical=cost.analysis)
- cost.budget_alloc -> cost_control (canonical=cost.budget_alloc)
- cost.cost_compare -> cost_control (canonical=cost.cost_compare)
- cost.profit_compare -> cost_control (canonical=cost.profit_compare)
- cost.project_boq -> cost_control (canonical=cost.project_boq)
- cost.project_budget -> cost_control (canonical=cost.project_budget)
- cost.project_cost_ledger -> cost_control (canonical=cost.project_cost_ledger)
- cost.project_progress -> cost_control (canonical=cost.project_progress)
- data.dictionary -> data_foundation (canonical=data.dictionary)
- equipment.management -> procurement_supply (canonical=equipment.management)
- equipment.request -> procurement_supply (canonical=equipment.request)
- equipment.settlement -> procurement_supply (canonical=equipment.settlement)
- equipment.usage -> procurement_supply (canonical=equipment.usage)
- finance.center -> finance_operations (canonical=finance.center)
- finance.operating_metrics -> finance_operations (canonical=finance.operating_metrics)
- finance.payment_ledger -> finance_operations (canonical=finance.payment_ledger)
- finance.payment_requests -> finance_operations (canonical=finance.payment_requests)
- finance.settlement_orders -> finance_operations (canonical=finance.settlement_orders)
- finance.treasury_ledger -> finance_operations (canonical=finance.treasury_ledger)
- finance.workspace -> finance_operations (canonical=finance.workspace)
- labor.attendance -> procurement_supply (canonical=labor.attendance)
- labor.management -> procurement_supply (canonical=labor.management)
- labor.request -> procurement_supply (canonical=labor.request)
- labor.settlement -> procurement_supply (canonical=labor.settlement)
- material.acceptance -> procurement_supply (canonical=material.acceptance)
- material.catalog -> procurement_supply (canonical=material.catalog)
- material.center -> procurement_supply (canonical=material.center)
- material.inbound -> procurement_supply (canonical=material.inbound)
- material.outbound -> procurement_supply (canonical=material.outbound)
- material.price_library -> procurement_supply (canonical=material.price_library)
- material.procurement -> procurement_supply (canonical=material.procurement)
- material.rental -> procurement_supply (canonical=material.rental)
- material.rental_order -> procurement_supply (canonical=material.rental_order)
- material.rental_settlement -> procurement_supply (canonical=material.rental_settlement)
- material.rfq -> procurement_supply (canonical=material.rfq)
- material.settlement -> procurement_supply (canonical=material.settlement)
- my_work.workspace -> workspace_shell (canonical=my_work.workspace)
- portal.capability_matrix -> portal_governance (canonical=portal.capability_matrix)
- portal.dashboard -> portal_governance (canonical=portal.dashboard)
- portal.lifecycle -> portal_governance (canonical=portal.lifecycle)
- project.management -> project_execution (canonical=project.management)
- projects.dashboard -> project_execution (canonical=projects.dashboard)
- projects.execution -> project_execution (canonical=projects.execution)
- projects.intake -> project_execution (canonical=projects.intake)
- projects.ledger -> project_execution (canonical=projects.ledger)
- projects.list -> project_execution (canonical=projects.list)
- quality.center -> site_quality_safety (canonical=quality.center)
- quality.recheck -> site_quality_safety (canonical=quality.recheck)
- quality.rectification -> site_quality_safety (canonical=quality.rectification)
- risk.center -> project_execution (canonical=risk.center)
- risk.monitor -> project_execution (canonical=risk.monitor)
- safety.center -> site_quality_safety (canonical=safety.center)
- safety.recheck -> site_quality_safety (canonical=safety.recheck)
- safety.rectification -> site_quality_safety (canonical=safety.rectification)
- subcontract.management -> procurement_supply (canonical=subcontract.management)
- subcontract.register -> procurement_supply (canonical=subcontract.register)
- subcontract.request -> procurement_supply (canonical=subcontract.request)
- subcontract.settlement -> procurement_supply (canonical=subcontract.settlement)
- task.center -> project_execution (canonical=task.center)
- workspace.home -> workspace_shell (canonical=workspace.home)
