---
capability_stage: P0.1
status: active
---
# Releases Index (Authoritative)

This directory is the single source of truth for release entries.
Other release notes under `docs/release/` or GitHub Releases are supporting copies.

## Current Stable Recommendation
- v0.3.0-stable (tag: `v0.3.0-stable`)
  - Notes: `docs/ops/release_notes_v0.3.0-stable.md`
  - Checklist: `docs/ops/release_checklist_v0.3.0-stable.md`

## Release List (Newest First)

1) 2026-01-20 — P2 Runtime v0.1\n   - Tag: `p2-runtime-v0.1`\n   - Notes: `docs/release/p2_runtime_v0.1.md`\n   - Verify: `make p2.smoke DB=sc_p2`\n   - GitHub Release: (if published)

2) 2026-01-19 — Gate P2 v0.1\n   - Tag: `p2-gate-v0.1`\n   - Notes: `docs/p2/p2_runtime_validation_matrix_v0.1.md`\n   - Verify: `make ci.gate.tp08 DB=sc_demo`, `make p2.smoke DB=sc_p2`\n   - GitHub Release: https://github.com/Leedefend/sce-backend-odoo/releases/tag/p2-gate-v0.1

3) 2026-01-19 — P1 Initiation v0.1\n   - Tag: `p1-initiation-v0.1`\n   - Notes: `docs/ops/releases/release_notes_p1-initiation-v0.1.md`\n   - Verify: `make ci.gate.tp08 DB=sc_demo`\n   - GitHub Release: (if published)

4) 2026-01-18 — v0.3.0-stable\n   - Tag: `v0.3.0-stable`\n   - Notes: `docs/ops/release_notes_v0.3.0-stable.md`\n   - Verify: `make ci.gate.tp08 DB=sc_demo`\n   - GitHub Release: (if published)

## Templates
- Notes template: `docs/ops/releases/_templates/release_notes_TEMPLATE.md`
- Checklist template: `docs/ops/releases/_templates/release_checklist_TEMPLATE.md`
