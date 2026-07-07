# Tag & Release Naming Convention v1.0

Goal: establish a durable, enforceable naming and release order for all future tags.
This spec does not rewrite or clean historical tags.

## 1) Tag Types

- phase: capability milestone for a phase or stage (e.g. P1/P2).
- gate: runtime or policy gate baseline (guard rails).
- release: production/stable release for general delivery.
- infra: infrastructure or environment baseline.
- exp: experiment or temporary spike.

## 2) Naming Formats (Regex)

phase
- Format: `p<phase>-<scope>-v<major>.<minor>`
- Regex: `^p[0-9]+-[a-z0-9-]+-v[0-9]+\.[0-9]+$`
- Examples: `p1-initiation-v0.1`, `p2-runtime-v0.1`

gate
- Format (new): `gate-<scope>-v<major>.<minor>`
- Regex: `^gate-[a-z0-9-]+-v[0-9]+\.[0-9]+$`
- Legacy allowed (do not extend): `p<phase>-gate-v<major>.<minor>`
- Legacy regex: `^p[0-9]+-gate-v[0-9]+\.[0-9]+$`
- Example: `p2-gate-v0.1` (legacy)

release
- Format: `v<major>.<minor>.<patch>` (optional suffix)
- Regex: `^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9-]+)?$`
- Examples: `v0.3.0`, `v0.3.0-stable`

infra
- Format: `infra.<scope>-<YYYY-MM>`
- Regex: `^infra\.[a-z0-9-]+-[0-9]{4}-[0-9]{2}$`
- Example: `infra.compose.stable-2026-01`

exp
- Format: `exp-<scope>-v<major>.<minor>`
- Regex: `^exp-[a-z0-9-]+-v[0-9]+\.[0-9]+$`
- Example: `exp-ux-sprint-v0.1`

## 3) When to Tag

- phase: phase milestone reached and documented; required for P1/P2 milestone signoff.
- gate: gate baseline ready for CI/local verification and audit coverage.
- release: stable delivery or production-ready cut.
- infra: baseline for environment or compose stack freeze.
- exp: short-lived experiment; must declare expiry in the notes.

## 4) GitHub Release Requirements

- MUST: gate, release
- SHOULD: phase (required if externally announced)
- OPTIONAL: infra, exp

## 5) Version Progression Rules

- Use `v<major>.<minor>` for phase/gate/exp.
  - Increment minor for new scope coverage or new validation items.
  - Increment major for incompatible changes to behavior or policy.
- Use `v<major>.<minor>.<patch>` for release.
  - Increment patch for fixes, minor for features, major for breaking changes.
- Never reuse a tag name.

## 6) No History Rewrite

- Historical tags remain untouched.
- This document only constrains new tags from this point forward.

## 7) Tag Pre-Check List (Process)

Before creating a new tag, confirm:

- Type: phase / gate / release / infra / exp
- Anchored on main
- Requires GitHub Release? (gate/release required)
- Validation commands PASS
- Release index updated (docs/ops/releases/README.md)

## 8) v2.0.0 Formal Release Line

The active formal release line uses the standard release format. The older
`v1.0.0` tag name already exists remotely and must not be reused, so the current
release-governance track is `v2.0.0`.

- gate baseline: `gate-release-v2.0`
- release candidates: `v2.0.0-rc1`, `v2.0.0-rc2` only when blocker fixes require a new candidate
- formal release: `v2.0.0`

Promotion order:

1. Merge reviewed release-prep work to `main`.
2. Run `make verify.release.v2_0_0.preflight` on the reviewed release commit.
3. Create `gate-release-v2.0` only after gate evidence passes.
4. Run `make verify.release.v2_0_0.product_hardening` and close any blocker.
5. Run `make verify.release.v2_0_0.governance.guard`.
6. Run `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard` after prod-sim acceptance evidence is recorded.
7. Create `v2.0.0-rc1` only after RC evidence passes.
8. Create `v2.0.0` only after prod-sim acceptance and release checklist signoff.

Recorded sample artifact directories may validate schema shape only; final
release signoff requires the recorded prod-sim acceptance run directory for that
release candidate.

Production deployment is not implied by creating `v2.0.0`; deployment remains a
separate supervised operation under `docs/ops/production_deployment_runbook_v1.md`.
