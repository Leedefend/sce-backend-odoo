# SCEMS v1.0 System Asset Inventory

## 1. Inventory Scope
- Code assets: backend modules, frontend app, scripts
- Contract assets: scene/capability/intent/exports
- Documentation assets: release, ops, demo, acceptance
- Verification assets: verify scripts, baselines, artifacts

## 2. Code Assets (Initial)

### 2.1 Backend
- `addons/smart_core`
- `addons/smart_construction_core`
- `addons/smart_construction_scene`

### 2.2 Frontend
- `frontend/apps/web`

### 2.3 Ops/Verification Scripts
- `scripts/verify`
- `scripts/ops`
- `scripts/test`

## 3. Contract and Export Assets
- `docs/contract/exports/scene_catalog.json`
- `docs/contract/exports/intent_catalog.json`
- `docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json`

## 4. Key Documentation Assets
- Master release blueprint: `docs/releases/construction_system_v1_release_plan.en.md`
- Ops/release index: `docs/ops/releases/README.md`
- Demo docs directory: `docs/demo`

## 5. Verification Assets (Current Key)
- `make verify.scene.catalog.governance.guard`
- `make verify.phase_next.evidence.bundle`
- `make verify.runtime.surface.dashboard.strict.guard`
- `make verify.project.form.contract.surface.guard`

## 6. Risks and Gaps
- Missing release-specific docs: deployment guide, demo script, acceptance checklist
- Missing dedicated V1 verification entry points (dashboard/route/permission)
- Need a standard v1 release evidence archive structure

## 7. Next Actions
- Produce: `docs/releases/release_gap_analysis.en.md`
- Build phase task board aligned to Phase 1~6

