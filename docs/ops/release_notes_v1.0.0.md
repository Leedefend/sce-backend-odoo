# Release Notes - v1.0.0

## Release Intent

`v1.0.0` is the first formal release line for the construction management
system. It promotes the current product-delivery posture from iterative
acceptance into a governed release candidate flow.

## Scope

- Product delivery baseline: 9 modules and 22 scoped scenes.
- Startup contract: `login -> system.init -> ui.contract`.
- Role authority: `role_surface.role_code`.
- Route authority: backend-provided `default_route`.
- Frontend acceptance: served static bundle must match the target DB and app env.
- Dev acceptance path: uploaded backup validation, static rebuild, API lock, and
  optional real-user `system.init` probe.
- Release gate: one-command preflight through `make verify.release.v1_0_0.preflight`.

## Tag Plan

- Gate baseline: `gate-release-v1.0`
- Release candidates: `v1.0.0-rc1`, then `v1.0.0-rc2` only if blocker fixes are required.
- Formal release: `v1.0.0`

Tags must be created only after the release checklist is complete and `main`
matches the reviewed release commit.

## Verification

Minimum pre-release verification:

```bash
make verify.release.v1_0_0.preflight
make verify.release.v1_0_0.product_hardening
make verify.system.capability_baseline.report
make verify.restricted
make verify.backend.contract.closure.mainline
```

Environment-specific acceptance:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \
  ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
  make release.dev.acceptance.publish
```

Production deployment is not part of this release-note batch. Production must
follow `docs/ops/production_deployment_runbook_v1.md` and
`docs/ops/prod_command_policy.md`.

## Known Limits

- `v1.0.0` release governance does not authorize production data replacement.
- `make verify.release.v1_0_0.product_hardening` is a formal-release hardening
  gate and may expose product bundle baseline drift that must be closed before
  final tag.
- Strict live checks may require a live-enabled runner; local restricted evidence
  is not a substitute for production deployment acceptance.
- RC tags are immutable once published. Any blocker fix requires a new commit and
  a new RC tag.
