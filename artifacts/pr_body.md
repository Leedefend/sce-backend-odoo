## Summary

This branch consolidates the scene-orchestration recovery and governance closure work completed on `codex/next-round`.

- classifies and commits the remaining runtime, frontend, verify, and governance changes into bounded batches
- recovers canonical scene entry / handoff / delivery-root semantics across backend and frontend consumers
- materializes scene-governance documentation, generated assets, and release-gate tooling
- closes the remaining bounded payment residual batches under dedicated repository exceptions

## Architecture Impact

- strengthens scene-orchestration ownership in `smart_core` and `smart_construction_scene`
- keeps frontend as a generic scene-contract consumer instead of pushing business rules into UI branching
- formalizes scene-governance assets, verify guards, and bounded payment residual governance exceptions

## Layer Target

- Platform orchestration and governance
- Scene orchestration
- Frontend generic contract consumption
- Release and verification governance

## Affected Modules

- `addons/smart_core`
- `addons/smart_construction_core`
- `addons/smart_construction_scene`
- `addons/smart_enterprise_base`
- `frontend/apps/web`
- `scripts/verify`
- `docs/architecture`
- `docs/audit`
- `docs/verify`
- `docs/ops`
- `docs/contract/exports/scenes/stable`
- `AGENTS.md`
- `Makefile`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-22-GOV-PUSH-PR-TO-MAIN-PA82.yaml`
- `make verify.scene.governance.release_gate`

Current gate status:

- `make verify.scene.governance.release_gate` is currently failing in `scene_governance_export_consistency_guard`
- failure detail: `menu_scene_mapping_current_v1.csv` row-count and key drift versus the stored baseline (`baseline=70`, `current=68`)

## Notes

- payment and settlement residuals were not force-merged into ordinary batches; they were committed only after adding exact-path, high-risk governance exceptions and using those bounded allowlists.
