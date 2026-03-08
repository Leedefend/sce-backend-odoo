# Role Scene Matrix v1

| role_key | home_scene | high_frequency_scenes | disabled_scenes | default_capability_groups |
|---|---|---|---|---|
| construction_manager | projects.dashboard | projects.dashboard,contracts.monitor,cost.control | - | project_management,contract_management,cost_management,analytics |
| project_manager | projects.execution | projects.execution,projects.detail,my_work.workspace | - | project_management,cost_management,contract_management,others |
| owner_manager | projects.dashboard | projects.dashboard,contracts.monitor,payments.approval | governance.runtime.audit | project_management,contract_management,finance_management,analytics |
| finance_manager | payments.approval | payments.approval,cost.control,contracts.monitor | - | finance_management,contract_management,cost_management,analytics |
| risk_manager | risk.center | risk.center,my_work.workspace,projects.detail | finance.settlement_orders | governance,analytics,project_management |
| regulator_viewer | risk.center | risk.center,projects.dashboard | finance.payment_requests,cost.project_budget | governance,analytics |
