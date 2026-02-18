---
capability_stage: P0.1
status: active
---
# Releases Index (Authoritative)

This directory is the single source of truth for release entries.
Other release notes under `docs/release/` or GitHub Releases are supporting copies.

## Current Stable Recommendation
- v0.3.0-stable (tag: `v0.3.0-stable`)
  - Type: runtime
  - Status: stable
  - Notes: `docs/ops/release_notes_v0.3.0-stable.md`
  - Checklist: `docs/ops/release_checklist_v0.3.0-stable.md`
  - Verify: `make ci.gate.tp08 DB=sc_demo`
  - GitHub Release: (not published)

## Release List (Newest First)

1) 2026-02-04 — Portal Shell UI v0.7.1
   - Tag: `portal-shell-ui-v0.7.1` (planned)
   - Type: frontend
   - Status: draft
   - Docs: `docs/ops/releases/archive/frontend_history/frontend_v0_7_1_ui_notes.md`
   - Verify: `make verify.portal.ui.v0_7.container`, `make verify.portal.guard_groups`, `make verify.portal.recordview_hud_smoke.container`
   - GitHub Release: (not published)

2) 2026-01-20 — Infra Stage Exec v0.3 (SOP squash rebuild)
   - Tag: `infra-stage-exec-v0.3-squash1` (canonical)
   - Type: infra
   - Status: released
   - Docs: `docs/ops/stage_execution_template_v1.0.md`, `docs/ops/stage_defs/p2.yml`, `docs/ops/stage_defs/p3-runtime-r1.yml`
   - Verify: `make stage.run STAGE=p2 DB=sc_p2`, `make stage.run STAGE=p3-runtime-r1 DB=sc_p3`
   - GitHub Release: (not published)

3) 2026-01-20 — Infra Stage Exec v0.3
   - Tag: `infra-stage-exec-v0.3` (legacy, non-SOP; do not use)
   - Type: infra
   - Status: released
   - Docs: `docs/ops/stage_execution_template_v1.0.md`, `docs/ops/stage_defs/p2.yml`, `docs/ops/stage_defs/p3-runtime-r1.yml`
   - Verify: `make stage.run STAGE=p2 DB=sc_p2`, `make stage.run STAGE=p3-runtime-r1 DB=sc_p3`
   - GitHub Release: (not published)

4) 2026-01-20 — Infra Stage Exec v0.2
   - Tag: `infra-stage-exec-v0.2`
   - Type: infra
   - Status: released
   - Docs: `docs/ops/stage_execution_template_v1.0.md`, `docs/ops/stage_defs/p2.yml`, `docs/ops/stage_defs/p3-runtime-r1.yml`
   - Verify: `make stage.run STAGE=p2 DB=sc_p2`, `make stage.run STAGE=p3-runtime-r1 DB=sc_p3`
   - GitHub Release: (not published)

5) 2026-01-20 — Infra Stage Exec v0.1
   - Tag: `infra-stage-exec-v0.1`
   - Type: infra
   - Status: released
   - Docs: `docs/ops/stage_execution_template_v1.0.md`, `docs/ops/codex_rules_v1.0.md`, `docs/ops/codex_preamble_v1.0.txt`
   - Verify: `make stage.run STAGE=p2 DB=sc_p2`, `make stage.run STAGE=p3-runtime-r1 DB=sc_p3`
   - GitHub Release: (not published)

6) 2026-01-20 — Infra Codex Policy v0.1
   - Tag: `infra-codex-policy-v0.1`
   - Type: infra
   - Status: merged
   - Docs: `docs/ops/codex_rules_v1.0.md`
   - Verify: `make codex.preflight`, `make ci.gate.tp08 DB=sc_demo`
   - GitHub Release: (not published)

7) 2026-01-20 — P3 Runtime R1 v0.1
   - Tag: `p3-runtime-r1-v0.1`
   - Type: runtime
   - Status: active
   - Docs: `docs/release/p3_runtime_r1_v0.1.md`
   - Verify: `make ci.gate.tp08 DB=sc_demo`, `make p3.smoke DB=sc_p3`, `make p3.audit DB=sc_p3`
   - GitHub Release: (not published)

8) 2026-01-20 — P2 Runtime v0.1
   - Tag: `p2-runtime-v0.1`
   - Type: runtime
   - Status: active
   - Docs: `docs/release/p2_runtime_v0.1.md`
   - Verify: `make p2.smoke DB=sc_p2`
   - GitHub Release: (not published)

9) 2026-01-19 — Gate P2 v0.1
   - Tag: `p2-gate-v0.1`
   - Type: gate
   - Status: active
   - Docs: `docs/p2/p2_runtime_validation_matrix_v0.1.md`
   - Verify: `make ci.gate.tp08 DB=sc_demo`, `make p2.smoke DB=sc_p2`
   - GitHub Release: https://github.com/Leedefend/sce-backend-odoo/releases/tag/p2-gate-v0.1

10) 2026-01-19 — P1 Initiation v0.1
   - Tag: `p1-initiation-v0.1`
   - Type: phase
   - Status: active
   - Docs: `docs/ops/releases/release_notes_p1-initiation-v0.1.md`
   - Verify: `make ci.gate.tp08 DB=sc_demo`
   - GitHub Release: (not published)

11) 2026-01-18 — v0.3.0-stable
   - Tag: `v0.3.0-stable`
   - Type: runtime
   - Status: stable
   - Docs: `docs/ops/release_notes_v0.3.0-stable.md`
   - Verify: `make ci.gate.tp08 DB=sc_demo`
   - GitHub Release: (not published)

## Templates
- Notes template: `docs/ops/releases/templates/release_notes_TEMPLATE.md`
- Checklist template: `docs/ops/releases/templates/release_checklist_TEMPLATE.md`

## Current Review Baseline
- Menu scene coverage evidence:
  - `docs/ops/releases/current/menu_scene_coverage_evidence.md`
- Backend evidence & observability expansion (Phase Next):
  - `make verify.scene.catalog.governance.guard`
    - artifact: `artifacts/scene_catalog_runtime_alignment_guard.json`
    - release check: `summary.probe_source` should be `prod_like_baseline` (or explicit env override), not demo-only fallback
  - `make verify.role.capability_floor.prod_like`
    - artifact: `/mnt/artifacts/backend/role_capability_floor_prod_like.json` (fallback: `artifacts/backend/role_capability_floor_prod_like.json`)
  - `make verify.contract.assembler.semantic.smoke`
    - artifact: `/mnt/artifacts/backend/contract_assembler_semantic_smoke.json` (fallback: `artifacts/backend/contract_assembler_semantic_smoke.json`)
  - `make verify.runtime.surface.dashboard.report`
    - artifact: `/mnt/artifacts/backend/runtime_surface_dashboard_report.json` (fallback: `artifacts/backend/runtime_surface_dashboard_report.json`)
  - `make verify.backend.architecture.full.report`
    - artifact: `/mnt/artifacts/backend/backend_architecture_full_report.json` (fallback: `artifacts/backend/backend_architecture_full_report.json`)
  - `make verify.backend.evidence.manifest.guard`
    - artifact: `/mnt/artifacts/backend/backend_evidence_manifest.json` (fallback: `artifacts/backend/backend_evidence_manifest.json`)
