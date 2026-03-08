# Capability Catalog v1

- generated_on: 2026-03-09
- capability_count: 42

| capability_key | name | domain | source_model | main_scene | status | role_scope |
|---|---|---|---|---|---|---|
| analytics.dashboard.executive | 经营驾驶舱 | dashboard | sc.dashboard.metric | projects.dashboard | ready | 施工 |
| analytics.exception.list | 异常列表 | dashboard | sc.dashboard.metric | finance.operating_metrics | ready | 施工 |
| analytics.lifecycle.monitor | 生命周期监控 | dashboard | sc.dashboard.metric | portal.lifecycle | ready | 施工 |
| analytics.project.focus | 我关注的项目 | dashboard | sc.dashboard.metric | projects.list | ready | 施工 |
| contract.center.open | 合同中心 | contract | sc.contract | projects.ledger | ready | 施工 |
| contract.expense.track | 支出合同 | contract | sc.contract | projects.ledger | ready | 施工 |
| contract.income.track | 收入合同 | contract | sc.contract | projects.ledger | ready | 施工 |
| contract.settlement.audit | 结算审核 | contract | sc.contract | finance.settlement_orders | ready | 施工 |
| cost.boq.manage | 工程量清单 | cost | sc.cost.ledger | cost.project_boq | ready | 施工 |
| cost.budget.manage | 预算管理 | cost | sc.cost.ledger | cost.project_budget | ready | 施工 |
| cost.ledger.open | 成本台账 | cost | sc.cost.ledger | cost.project_cost_ledger | ready | 施工 |
| cost.profit.compare | 盈亏对比 | cost | sc.cost.ledger | cost.profit_compare | ready | 施工 |
| cost.progress.report | 进度填报 | cost | sc.cost.ledger | cost.project_progress | ready | 施工 |
| finance.approval.center | 审批中心入口 | payment | sc.payment.request | finance.center | ready | 施工 |
| finance.exception.monitor | 财务异常 | payment | sc.payment.request | finance.operating_metrics | ready | 施工 |
| finance.invoice.list | 发票列表 | payment | sc.payment.request | finance.center | ready | 施工 |
| finance.ledger.payment | 收付款台账 | payment | sc.payment.request | finance.payment_ledger | ready | 施工 |
| finance.ledger.treasury | 资金台账 | payment | sc.payment.request | finance.treasury_ledger | ready | 施工 |
| finance.metrics.operating | 经营指标 | payment | sc.payment.request | finance.operating_metrics | ready | 施工 |
| finance.payment_request.form | 付款申请表单 | payment | sc.payment.request | finance.payment_requests | ready | 施工 |
| finance.payment_request.list | 付款申请列表 | payment | sc.payment.request | finance.payment_requests | ready | 施工 |
| finance.plan.funding | 资金计划 | payment | sc.payment.request | finance.center | ready | 施工 |
| finance.settlement.order | 结算单 | payment | sc.payment.request | finance.settlement_orders | ready | 施工 |
| governance.capability.matrix | 能力矩阵 | workflow | sc.workflow.ticket | portal.capability_matrix | ready | 施工 |
| governance.runtime.audit | 运行态审计 | workflow | sc.workflow.ticket | portal.dashboard | ready | 施工 |
| governance.scene.openability | 场景可打开性 | workflow | sc.workflow.ticket | portal.capability_matrix | ready | 施工 |
| material.catalog.open | 物资目录 | dictionary | sc.dictionary.item | projects.ledger | ready | 施工 |
| material.procurement.list | 采购清单 | dictionary | sc.dictionary.item | projects.ledger | ready | 施工 |
| project.board.open | 项目看板 | project | project.project | projects.ledger | ready | 业主,施工,通用 |
| project.dashboard.open | 项目驾驶舱 | project | project.project | projects.dashboard | ready | 施工 |
| project.document.open | 项目文档 | project | project.project | projects.ledger | ready | 施工 |
| project.initiation.enter | 项目立项 | project | project.project | projects.intake | ready | 施工 |
| project.lifecycle.open | 生命周期视图 | project | project.project | portal.lifecycle | ready | 施工 |
| project.lifecycle.transition | 生命周期流转 | project | project.project | portal.lifecycle | ready | 施工 |
| project.list.open | 项目列表 | project | project.project | projects.list | ready | 业主,施工,通用 |
| project.risk.list | 风险清单 | project | project.project | projects.ledger | ready | 施工 |
| project.structure.manage | 执行结构 | project | project.project | cost.project_boq | ready | 施工 |
| project.task.board | 任务看板 | project | project.project | projects.ledger | ready | 施工 |
| project.task.list | 任务列表 | project | project.project | projects.ledger | ready | 业主,施工,通用 |
| project.weekly_report.open | 周报入口 | project | project.project | projects.ledger | ready | 施工 |
| workspace.project.watch | 我关注的项目 | workspace | smart_core.workspace | projects.list | ready | 业主,施工,通用 |
| workspace.today.focus | 今日关键动作 | workspace | smart_core.workspace | portal.dashboard | ready | 业主,施工,通用 |
