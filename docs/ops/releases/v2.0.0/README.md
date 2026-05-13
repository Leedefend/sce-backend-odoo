# v2.0.0 Release Control

## Status

- Version: `v2.0.0`
- Status: planned
- Release type: formal release
- Planned gate tag: `gate-release-v2.0`
- Planned RC tag: `v2.0.0-rc1`
- Planned final tag: `v2.0.0`
- Governance date: 2026-05-12

## Layer Target / Module / Reason

- Layer Target: Ops / Release Governance
- Module: versioning, release checklist, release notes, release evidence manifest
- Reason: establish the active formal release line before RC and production
  deployment work begins, avoiding reuse of the existing remote `v1.0.0` tag.

## Release Boundaries

This release-control directory defines release governance only.

It does not:

- create Git tags
- deploy production
- reset or replace databases
- change public intent semantics
- change frontend runtime behavior

## Required Gates

```bash
make verify.release.v2_0_0.preflight
git diff --check
```

Supporting gates:

```bash
make verify.system.capability_baseline.report
make verify.backend.contract.closure.mainline
make verify.restricted
```

Formal-release hardening gate:

```bash
make verify.release.v2_0_0.product_hardening
```

## Release Documents

- Release notes: `docs/ops/release_notes_v2.0.0.md`
- Release checklist: `docs/ops/release_checklist_v2.0.0.md`
- Evidence manifest: `docs/ops/releases/v2.0.0/evidence_manifest.md`

## Promotion Order

1. Finish release governance on a feature branch.
2. Merge reviewed release governance and code changes to `main`.
3. Run release preflight on `main`.
4. Create `gate-release-v2.0` after gate evidence passes.
5. Close product hardening gate.
6. Create `v2.0.0-rc1` after RC evidence passes.
7. Run prod-sim acceptance.
8. Create `v2.0.0` after formal release signoff.

## Rollback

Release governance rollback is file-level:

- remove `docs/ops/releases/v2.0.0/`
- remove `docs/ops/release_notes_v2.0.0.md`
- remove `docs/ops/release_checklist_v2.0.0.md`
- remove `verify.release.v2_0_0.preflight` from `Makefile`
- restore release index and versioning edits

Runtime rollback is outside this governance batch and must follow the production
runbook if production deployment has started.
