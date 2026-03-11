# 文档总入口（Docs Hub）

本目录为系统文档导航入口，围绕当前已落地能力组织：`contract` / `ops` / `audit`。

## 方向锚点
- 项目方向锚定文: `docs/00_overview/project_direction.md`
- English mirror: `docs/00_overview/project_direction.en.md`

## 能力域导航
- Contract（契约与目录）: `docs/contract/README.md`
- Ops（发布与运行证据）: `docs/ops/README.md`
- Audit（审计方法与产物入口）: `docs/audit/README.md`
- Baseline Freeze（基线冻结策略）: `docs/ops/baseline_freeze_policy.md`

## 当前权威 Contract Exports
- Intent Catalog: `docs/contract/exports/intent_catalog.json`
- Scene Catalog: `docs/contract/exports/scene_catalog.json`

## 当前阶段 Release 证据（暂不迁移）
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`

## SCEMS v1.0 Release Planning
- Master release plan: `docs/releases/construction_system_v1_release_plan.en.md`
- Scope freeze: `docs/releases/release_scope_v1.en.md`
- System asset inventory: `docs/releases/system_asset_inventory.en.md`
- Release gap analysis: `docs/releases/release_gap_analysis.en.md`
- Execution board: `docs/releases/construction_system_v1_execution_board.en.md`
- Phase 0 execution record: `docs/releases/phase_0_scope_freeze_execution.en.md`
- Phase 1 checklist: `docs/releases/phase_1_navigation_convergence_checklist.en.md`
- Phase 1 mapping: `docs/releases/phase_1_navigation_scene_mapping.en.md`
- Phase 1 convergence report: `docs/releases/phase_1_navigation_convergence_report.en.md`
- Phase 2 checklist: `docs/releases/phase_2_core_scenarios_closure_checklist.en.md`
- Phase 2 W1 (7-block verify): `docs/releases/phase_2_w1_project_management_7block_verify_report.en.md`
- Phase 2 W1 (my-work minimum loop): `docs/releases/phase_2_w1_my_work_minimum_loop_report.en.md`
- Phase 2 W1 (ledger-to-management route): `docs/releases/phase_2_w1_ledger_to_management_route_report.en.md`
- Phase 2 (`contracts.workspace` implementation): `docs/releases/phase_2_contracts_workspace_implementation_report.en.md`
- Phase 2 (`cost.analysis` implementation): `docs/releases/phase_2_cost_analysis_implementation_report.en.md`
- Phase 2 (`finance.workspace` implementation): `docs/releases/phase_2_finance_workspace_implementation_report.en.md`
- Phase 2 (`risk.center` implementation): `docs/releases/phase_2_risk_center_implementation_report.en.md`
- Phase 2 (workspace closure report): `docs/releases/phase_2_workspace_closure_report.en.md`
- Phase 3 checklist: `docs/releases/phase_3_role_permission_system_checklist.en.md`
- Phase 3 (role-permission matrix): `docs/releases/role_permission_matrix_v1.en.md`
- Phase 3 (execution report): `docs/releases/phase_3_role_permission_execution_report.en.md`
- Phase 3 (system-admin minimum-permission audit): `docs/releases/phase_3_system_admin_minimum_permission_audit_report.en.md`
- Phase 3 (exit readiness): `docs/releases/phase_3_exit_readiness_report.en.md`
- Phase 4 checklist: `docs/releases/phase_4_frontend_stability_checklist.en.md`
- Phase 4 (execution report): `docs/releases/phase_4_frontend_stability_execution_report.en.md`
- Phase 5 checklist: `docs/releases/phase_5_verification_deployment_checklist.en.md`
- Phase 5 (execution report): `docs/releases/phase_5_verification_deployment_execution_report.en.md`
- Deployment guide: `docs/deploy/deployment_guide_v1.en.md`
- Demo script: `docs/demo/system_demo_v1.en.md`
- User acceptance checklist: `docs/releases/user_acceptance_checklist.en.md`
- Phase 6 checklist: `docs/releases/phase_6_pilot_launch_checklist.en.md`

## 快速生成/导出（现有 Make 目标）
```bash
make contract.catalog.export
make contract.evidence.export
make audit.intent.surface
make verify.business.increment.preflight
```

## Bilingual
- English version: `docs/README.en.md`
