# Documentation Hub

This directory is the top-level documentation entry aligned with current implemented capabilities: `contract` / `ops` / `audit`.

## Direction Anchor
- Project Direction Anchor: `docs/00_overview/project_direction.en.md`
- 中文版: `docs/00_overview/project_direction.md`

## Capability Navigation
- Contract (contracts and catalogs): `docs/contract/README.md`
- Ops (release and operational evidence): `docs/ops/README.md`
- Audit (audit method and artifact entry): `docs/audit/README.md`
- Baseline Freeze policy: `docs/ops/baseline_freeze_policy.en.md`

## Current Authoritative Contract Exports
- Intent Catalog: `docs/contract/exports/intent_catalog.json`
- Scene Catalog: `docs/contract/exports/scene_catalog.json`

## Current-Phase Release Evidence (no migration in this phase)
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`

## Quick Generation/Export (existing Make targets)
```bash
make contract.catalog.export
make contract.evidence.export
make audit.intent.surface
```

## 双语
- 中文版: `docs/README.md`
