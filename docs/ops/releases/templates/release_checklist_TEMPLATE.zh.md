# Release Checklist — <VERSION>

## 前置条件
- 工作区干净
- Tag 本地与远端均存在
- Release Notes 已审阅

## Guard 验证（必须）
- `ENV=prod make verify.prod.guard` 通过（guard-only）
- `scripts/verify/prod_guard_smoke.sh` 产出 JSON 结果
- 仅当 JSON 报告 `rc=0` 时允许发布
- 后端证据包已更新：
  - `make verify.phase_next.evidence.bundle`
  - `make verify.phase_next.evidence.bundle.strict`
  - `make verify.boundary.import_guard.schema.guard`
  - `SC_BOUNDARY_IMPORT_STRICT=1 make verify.backend.architecture.full`
  - `make verify.contract.evidence.guard`
  - `make verify.backend.architecture.full.report`
  - `make verify.backend.architecture.full.report.guard`
  - `make verify.backend.evidence.manifest.guard`
  - 必须产物：
    - `/mnt/artifacts/backend/load_view_access_contract_guard.json`（不可写时回落 `artifacts/backend/...`；finance 夹具应对 `ir.ui.view` 返回 403）
    - `artifacts/scene_catalog_runtime_alignment_guard.json`（`summary.probe_source` 应为 `prod_like_baseline` 或显式环境变量覆盖）
    - `/mnt/artifacts/backend/role_capability_floor_prod_like.json`（不可写时回落 `artifacts/backend/...`）
    - `/mnt/artifacts/backend/contract_assembler_semantic_smoke.json`（不可写时回落 `artifacts/backend/...`）
  - `/mnt/artifacts/backend/runtime_surface_dashboard_report.json`（不可写时回落 `artifacts/backend/...`）
  - `/mnt/artifacts/backend/boundary_import_guard_report.json`（不可写时回落 `artifacts/backend/...`）
  - `/mnt/artifacts/backend/backend_architecture_full_report.json`（不可写时回落 `artifacts/backend/...`）
    - `/mnt/artifacts/backend/backend_architecture_full_report_guard.json`（不可写时回落 `artifacts/backend/...`）
    - `/mnt/artifacts/backend/backend_evidence_manifest.json`（不可写时回落 `artifacts/backend/...`）
    - `artifacts/business_capability_baseline_report.json`
    - `artifacts/contract/phase11_1_contract_evidence.json`
      - 必须包含 `load_view_access_contract`，且 `forbidden_status=403`、`forbidden_error_code=PERMISSION_DENIED`
      - 必须包含 `boundary_import_report`，且 `warning_count=0`、`violation_count=0`
- 已包含 Phase 9.8 菜单/场景覆盖汇总证据：
  - `make verify.menu.scene_resolve.summary`
  - `artifacts/codex/summary.md` 必须包含：
    - `menu_scene_resolve_effective_total`
    - `menu_scene_resolve_coverage`
    - `menu_scene_resolve_enforce_prefixes`
  - 默认业务强校验范围：
    - `MENU_SCENE_ENFORCE_PREFIXES=smart_construction_core.,smart_construction_demo.,smart_construction_portal.`

## 生产安全检查
- `ENV=prod` 禁止：`make db.reset`, `make demo.*`, `make ci.*`, `make gate.*`
- `ENV=prod` 必须 `PROD_DANGER=1`：`mod.install`, `mod.upgrade`, policy apply
- 生产 seed 需显式 DB：`SEED_DB_NAME_EXPLICIT=1`

## Seed Base（如需执行）
- 仅允许 `SC_SEED_PROFILE=base`
- `SC_BOOTSTRAP_USERS=1` 必须同时提供 `SEED_ALLOW_USERS_BOOTSTRAP=1` 与密码

## 发布后
- 记录 guard JSON 到发布日志
- 确认 `main` 与 tag 一致
