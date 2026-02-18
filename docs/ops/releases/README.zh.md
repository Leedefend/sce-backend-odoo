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
- 后端证据与可观测扩展（Phase Next）：
  - `make verify.scene.catalog.governance.guard`
    - 产物：`artifacts/scene_catalog_runtime_alignment_guard.json`
    - 发布检查：`summary.probe_source` 应为 `prod_like_baseline`（或显式环境变量覆盖），不应依赖 demo-only 回退
  - `make verify.role.capability_floor.prod_like`
    - 产物：`/mnt/artifacts/backend/role_capability_floor_prod_like.json`（不可写时回落 `artifacts/backend/role_capability_floor_prod_like.json`）
  - `make verify.contract.assembler.semantic.smoke`
    - 产物：`/mnt/artifacts/backend/contract_assembler_semantic_smoke.json`（不可写时回落 `artifacts/backend/contract_assembler_semantic_smoke.json`）
  - `make verify.runtime.surface.dashboard.report`
    - 产物：`/mnt/artifacts/backend/runtime_surface_dashboard_report.json`（不可写时回落 `artifacts/backend/runtime_surface_dashboard_report.json`）
  - `make verify.backend.architecture.full.report`
    - 产物：`/mnt/artifacts/backend/backend_architecture_full_report.json`（不可写时回落 `artifacts/backend/backend_architecture_full_report.json`）
  - `make verify.backend.evidence.manifest.guard`
    - 产物：`/mnt/artifacts/backend/backend_evidence_manifest.json`（不可写时回落 `artifacts/backend/backend_evidence_manifest.json`）
