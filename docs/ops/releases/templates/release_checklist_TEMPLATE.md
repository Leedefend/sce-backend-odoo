# Release Checklist — <VERSION>

## Preconditions
- Working tree clean
- Tag exists locally and on origin
- Release notes reviewed

## Guard Verification (required)
- `ENV=prod make verify.prod.guard` passes (guard-only)
- JSON summary emitted by `scripts/verify/prod_guard_smoke.sh`
- Release is approved iff JSON reports `rc=0`
- Backend evidence bundle is up-to-date:
  - `make verify.phase_next.evidence.bundle`
  - `make verify.phase_next.evidence.bundle.strict`
  - `make verify.contract.evidence.guard`
  - `make verify.backend.architecture.full.report`
  - `make verify.backend.architecture.full.report.guard`
  - `make verify.backend.evidence.manifest.guard`
  - required artifacts:
    - `/mnt/artifacts/backend/load_view_access_contract_guard.json` (fallback `artifacts/backend/...`; finance fixture should reject `ir.ui.view` with 403)
    - `artifacts/scene_catalog_runtime_alignment_guard.json` (`summary.probe_source` should be `prod_like_baseline` or explicit env override)
    - `/mnt/artifacts/backend/role_capability_floor_prod_like.json` (fallback `artifacts/backend/...`)
    - `/mnt/artifacts/backend/contract_assembler_semantic_smoke.json` (fallback `artifacts/backend/...`)
    - `/mnt/artifacts/backend/runtime_surface_dashboard_report.json` (fallback `artifacts/backend/...`)
    - `/mnt/artifacts/backend/backend_architecture_full_report.json` (fallback `artifacts/backend/...`)
    - `/mnt/artifacts/backend/backend_architecture_full_report_guard.json` (fallback `artifacts/backend/...`)
    - `/mnt/artifacts/backend/backend_evidence_manifest.json` (fallback `artifacts/backend/...`)
    - `artifacts/business_capability_baseline_report.json`
    - `artifacts/contract/phase11_1_contract_evidence.json`
- Phase 9.8 menu/scene coverage summary is present:
  - `make verify.menu.scene_resolve.summary`
  - required keys in `artifacts/codex/summary.md`:
    - `menu_scene_resolve_effective_total`
    - `menu_scene_resolve_coverage`
    - `menu_scene_resolve_enforce_prefixes`
  - default business enforcement scope:
    - `MENU_SCENE_ENFORCE_PREFIXES=smart_construction_core.,smart_construction_demo.,smart_construction_portal.`

## Production Safety Checks
- `ENV=prod` forbids: `make db.reset`, `make demo.*`, `make ci.*`, `make gate.*`
- `ENV=prod` requires `PROD_DANGER=1` for `mod.install`, `mod.upgrade`, policy apply
- `seed.run` in prod requires explicit DB name (`SEED_DB_NAME_EXPLICIT=1`)

## Seed Base (if running)
- `SC_SEED_PROFILE=base` only
- `SC_BOOTSTRAP_USERS=1` requires `SEED_ALLOW_USERS_BOOTSTRAP=1` and password

## Post-Release
- Record verification output (JSON) in release log
- Confirm branch `main` matches tag
