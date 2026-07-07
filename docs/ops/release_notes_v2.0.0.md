# Release Notes - v2.0.0

## Release Intent

`v2.0.0` is the active formal release line for the construction management
system. It promotes the current product-delivery posture from iterative
acceptance into a governed release candidate flow.

The earlier `v1.0.0` tag name already exists in the remote repository and must
not be reused. This line therefore intentionally advances the formal release
track to `v2.0.0`.

## Scope

- Product delivery baseline: 10 modules and 22 scoped scenes.
- Startup contract: `login -> system.init -> ui.contract`.
- Role authority: `role_surface.role_code`.
- Route authority: backend-provided `default_route`.
- Frontend acceptance: served static bundle must match the target DB and app env.
- Dev acceptance path: uploaded backup validation, static rebuild, API lock, and
  optional real-user `system.init` probe.
- Release gate: one-command preflight through `make verify.release.v2_0_0.preflight`.
- Release governance docs: release-control README, release notes, versioning,
  release indexes, evidence manifest, checklist, and verify catalog.

## Tag Plan

- Gate baseline: `gate-release-v2.0`
- Release candidates: `v2.0.0-rc1`, then `v2.0.0-rc2` only if blocker fixes are required.
- Formal release: `v2.0.0`

Tags must be created only after the release checklist is complete and `main`
matches the reviewed release commit.

## Verification

Minimum pre-release verification:

```bash
make verify.release.v2_0_0.preflight
make verify.release.v2_0_0.product_hardening
make verify.release.v2_0_0.governance.guard
PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard
make verify.system.capability_baseline.report
make verify.platform.release_policy.runtime
make verify.backend.contract.closure.mainline
make verify.restricted
```

Environment-specific acceptance:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \
  ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
  make release.daily_dev.acceptance.publish
```

Daily acceptance now treats product navigation as release evidence: menu action
count range, forbidden legacy labels, required product paths, and locked action
targets must all pass in `artifacts/backend/dev_acceptance_release_probe.json`.

Production deployment is not part of this release-note batch. Production must
follow `docs/ops/production_deployment_runbook_v1.md` and
`docs/ops/prod_command_policy.md`.

## Known Limits

- `v2.0.0` release governance does not authorize production data replacement.
- `make verify.release.v2_0_0.product_hardening` is a formal-release hardening
  gate and may expose product bundle baseline drift that must be closed before
  final tag.
- Strict live checks may require a live-enabled runner; local restricted evidence
  is not a substitute for production deployment acceptance.
- Recorded sample artifact directories may validate evidence schema shape, but
  are not release signoff evidence.
- RC tags are immutable once published. Any blocker fix requires a new commit and
  a new RC tag.
