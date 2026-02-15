# Ops 文档入口

本目录聚合发布、验证、运行治理相关文档。

## 主要入口
- Release 证据目录: `docs/ops/releases/`
- 菜单场景覆盖率证据（当前基线）: `docs/ops/releases/current/menu_scene_coverage_evidence.md`
- 验证入口（含 strict/兼容模式说明）: `docs/ops/verify/README.md`
- 基线冻结策略: `docs/ops/baseline_freeze_policy.md`
- 场景观测命令分层:
  - preflight refresh: `make verify.portal.scene_observability_preflight.refresh.container DB_NAME=<name>`
  - preflight smoke: `make verify.portal.scene_observability_preflight_smoke.container`
  - preflight latest artifact: `make verify.portal.scene_observability_preflight.latest`
  - gate smoke aggregate: `make verify.portal.scene_observability_gate_smoke.container`
  - smoke aggregate: `make verify.portal.scene_observability_smoke.container`
  - strict aggregate: `make verify.portal.scene_observability_strict.container`
- 业务增量前置检查:
  - `make verify.business.increment.preflight`
  - `make verify.business.increment.preflight.strict`
  - 可选 profile: `BUSINESS_INCREMENT_PROFILE=base|strict`
- 导航对齐审计:
  - `make audit.nav.alignment DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
  - outputs: `artifacts/audit/nav_alignment_report.latest.json`, `artifacts/audit/nav_alignment_report.latest.md`
- 角色菜单差异审计:
  - `make audit.nav.role_diff DB_NAME=sc_demo`
  - outputs: `artifacts/audit/role_nav_diff.latest.json`, `artifacts/audit/role_nav_diff.latest.md`
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`
- 临时归档（非正式、仅追溯）: `docs/ops/releases/archive/temp/`

## 与契约/审计的关系
- Contract 总览: `docs/contract/README.md`
- Audit 入口: `docs/audit/README.md`

## Bilingual
- English version: `docs/ops/README.en.md`
