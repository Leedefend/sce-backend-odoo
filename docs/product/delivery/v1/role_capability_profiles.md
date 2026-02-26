# Role Capability Profiles V1

- version: v1
- role_count: 6
- unresolved_module_ref_count: 0
- unresolved_capability_ref_count: 0
- unresolved_default_scene_count: 0
- error_count: 0

| role | default_scene | visible_modules | capability_count |
|---|---|---|---:|
| 项目经理 (pm) | projects.dashboard | cost_budget_profit,masterdata_workspace,payment_request_approval,project_execution_collab,project_initiation_ledger,purchase_material_collab | 27 |
| 财务经理 (finance) | finance.center | cost_budget_profit,funding_settlement_ledger,masterdata_workspace,payment_request_approval | 17 |
| 采购经理 (purchase_manager) | cost.project_boq | cost_budget_profit,masterdata_workspace,project_initiation_ledger,purchase_material_collab | 17 |
| 老板/领导 (executive) | portal.dashboard | executive_dashboard,lifecycle_governance,masterdata_workspace | 13 |
| 系统管理员 (admin) | portal.capability_matrix | cost_budget_profit,executive_dashboard,funding_settlement_ledger,lifecycle_governance,masterdata_workspace,payment_request_approval,project_execution_collab,project_initiation_ledger,purchase_material_collab | 41 |
| 运营专员 (ops) | projects.list | masterdata_workspace,payment_request_approval,project_initiation_ledger | 14 |
