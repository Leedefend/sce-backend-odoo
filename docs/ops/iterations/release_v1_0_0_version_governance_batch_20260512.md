# Release v1.0.0 Version Governance Batch 20260512

## 1. This Batch

- Goal: establish the first formal release line governance for `v1.0.0`.
- Completed:
  - Added `docs/ops/release_notes_v1.0.0.md`.
  - Added `docs/ops/release_checklist_v1.0.0.md`.
  - Added `docs/ops/releases/v1.0.0/README.md`.
  - Added `docs/ops/releases/v1.0.0/evidence_manifest.md`.
  - Added `make verify.release.v1_0_0.preflight`.
  - Added `make verify.release.v1_0_0.product_hardening`.
  - Updated release index and versioning guidance.
- Not completed: no tag creation, no production deployment, no prod-sim runtime
  operation. Product hardening is now green in the local `sc_demo` dev
  verification environment and remains required again on the reviewed release
  commit before final tag creation.

## 2. Impact Scope

- Modules: `docs/ops`, `docs/ops/releases`, `Makefile`
- Startup chain: no
- Contract/schema: no
- Default route: no
- Public intent: no

## 3. Risk

- P0: none; this batch is release governance only.
- P1: `make verify.release.v1_0_0.product_hardening` is environment-sensitive
  and must be rerun on the reviewed release commit before final tag.
- P2: existing dirty worktree means this batch should be reviewed together with
  the current release-prep changes before merge.

## 4. Verification

- Commands:
  - `make verify.system.capability_baseline.report`
  - `make verify.release.v1_0_0.preflight`
  - `make verify.release.v1_0_0.product_hardening`
  - `git diff --check`
- Results:
  - `make verify.system.capability_baseline.report`: PASS.
  - `make verify.release.v1_0_0.preflight`: PASS.
  - `make verify.release.v1_0_0.product_hardening`: PASS after closing the
    release hardening continuation. `verify.bundle.installation.ready` is now
    PASS, and `verify.platform.performance.smoke` uses the same registry-mode
    `system.init` boot parameters as the Web startup path.
  - `python3 -m py_compile scripts/verify/platform_performance_smoke.py`: PASS.
  - `ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.platform.performance.smoke`: PASS.
  - `git diff --check`: PASS.

## 5. Artifacts

- Snapshot: `artifacts/backend/system_capability_baseline_report.json`
- Product hardening evidence:
  - `artifacts/backend/bundle_installation_report.json`
  - `artifacts/backend/platform_performance_smoke.json`
- Release docs: `docs/ops/releases/v1.0.0/`
- E2E: N/A

## 6. Rollback

- Commit: revert this batch commit.
- Method: remove `v1.0.0` release docs and `verify.release.v1_0_0.preflight`,
  then restore release index and versioning edits.

## 7. Next Batch

- Goal: rerun preflight plus product hardening on the reviewed release commit,
  then prepare `gate-release-v1.0`.
- Preconditions: working tree is reviewed and release-prep changes are ready for
  merge to `main`.
