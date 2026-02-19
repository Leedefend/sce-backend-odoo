---
capability_stage: P0.1
status: active
---
# 版本发布索引

本索引用于稳定版本的发布记录与清单。

## 稳定版本
- v0.3.0-stable
  - Release Notes：`docs/ops/release_notes_v0.3.0-stable.md`
  - Release Checklist：`docs/ops/release_checklist_v0.3.0-stable.md`

## 模板
- Release Notes 模板：`docs/ops/releases/templates/release_notes_TEMPLATE.md`
- Release Checklist 模板：`docs/ops/releases/templates/release_checklist_TEMPLATE.md`
- Release Notes 模板（zh）：`docs/ops/releases/templates/release_notes_TEMPLATE.zh.md`
- Release Checklist 模板（zh）：`docs/ops/releases/templates/release_checklist_TEMPLATE.zh.md`

## 当前评审基线
- 菜单场景覆盖证据：
  - `docs/ops/releases/current/menu_scene_coverage_evidence.md`
- 前端契约驱动运行时（所有视图都以契约为唯一渲染依据）：
  - `make verify.frontend.contract_runtime.guard`
  - `make verify.frontend.typecheck.strict`
  - `make verify.frontend.build`
  - 发布检查：
    - `/a/:actionId`、`/r/:model/:id`、`/f/:model/:id` 必须由 `ui.contract`（`head/views/fields/buttons/toolbar/permissions/workflow/search`）驱动渲染，不以 `load_view` 作为主来源
    - 记录页运行时不得回退到 `load_view`，必须先解析 action 上下文并仅消费 `ui.contract` 的 form 载荷
    - 功能与交互变化应通过契约内容调整实现，不再新增按场景硬编码前端分支
    - 列表/看板需消费契约字段标签、契约筛选与契约动作（toolbar/buttons）作为运行时行为来源
    - 表单保存需按契约字段类型归一化 payload，并仅提交可写且发生变化的字段
    - 遗留模型页面（`ModelFormPage`/`ModelListPage`）仅允许作为兼容壳，必须委派到契约驱动运行时
- 后端证据与可观测扩展（Phase Next）：
  - `make verify.load_view.access.contract.guard`
    - 产物：`/mnt/artifacts/backend/load_view_access_contract_guard.json`（不可写时回落 `artifacts/backend/load_view_access_contract_guard.json`）
    - 发布检查：finance 夹具应至少有一个业务模型可读取，同时对 `ir.ui.view` 返回 `403/PERMISSION_DENIED`
  - `make verify.scene.catalog.governance.guard`
    - 产物：`artifacts/scene_catalog_runtime_alignment_guard.json`
    - 发布检查：`summary.probe_source` 应为 `prod_like_baseline`（或显式环境变量覆盖），不应依赖 demo-only 回退
  - `make verify.role.capability_floor.prod_like`
    - 产物：`/mnt/artifacts/backend/role_capability_floor_prod_like.json`（不可写时回落 `artifacts/backend/role_capability_floor_prod_like.json`）
  - `make verify.contract.assembler.semantic.smoke`
    - 产物：`/mnt/artifacts/backend/contract_assembler_semantic_smoke.json`（不可写时回落 `artifacts/backend/contract_assembler_semantic_smoke.json`）
  - `make verify.runtime.surface.dashboard.report`
    - 产物：`/mnt/artifacts/backend/runtime_surface_dashboard_report.json`（不可写时回落 `artifacts/backend/runtime_surface_dashboard_report.json`）
  - `make verify.boundary.import_guard`
    - 产物：`/mnt/artifacts/backend/boundary_import_guard_report.json`（不可写时回落 `artifacts/backend/boundary_import_guard_report.json`）
    - 发布检查：平台/业务/demo 分层之间不得出现禁用跨层 import 或禁用 manifest 依赖
  - `make verify.boundary.import_guard.schema.guard`
    - 发布检查：boundary import 报告 schema 固定，便于 CI 与差异审计
  - `SC_BOUNDARY_IMPORT_STRICT=1 make verify.backend.architecture.full`
    - 严格检查：执行 boundary import 的告警/违规阈值守卫（`SC_BOUNDARY_IMPORT_WARN_MAX`、`SC_BOUNDARY_IMPORT_VIOLATION_MAX`）
  - `make verify.backend.architecture.full.report`
    - 产物：`/mnt/artifacts/backend/backend_architecture_full_report.json`（不可写时回落 `artifacts/backend/backend_architecture_full_report.json`）
  - `make verify.backend.evidence.manifest.guard`
    - 产物：`/mnt/artifacts/backend/backend_evidence_manifest.json`（不可写时回落 `artifacts/backend/backend_evidence_manifest.json`）
  - `make verify.contract.evidence.guard`
    - 合同证据需包含 `load_view_access_contract` 区段（allowed model + forbidden status/code）
    - 合同证据需包含 `boundary_import_report` 区段（warning/violation/tracked modules），用于分层治理审计
