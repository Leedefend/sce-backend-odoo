# Release Checklist - v2.0.0

## Preconditions

- Working tree is clean at release cut time.
- Release commit is merged to `main`.
- `main` is fast-forwarded and reviewed.
- Release notes reviewed: `docs/ops/release_notes_v2.0.0.md`.
- Evidence manifest reviewed: `docs/ops/releases/v2.0.0/evidence_manifest.md`.
- Versioning reviewed: `docs/ops/versioning.md`.
- Release indexes reviewed: `docs/ops/releases/README.md` and
  `docs/ops/releases/README.zh.md`.
- Verify catalog reviewed: `docs/ops/verify/README.md`.
- No production command is executed from a dirty worktree.

## Version And Tag Checks

- Gate tag planned: `gate-release-v2.0`.
- RC tag planned: `v2.0.0-rc1`.
- Formal tag planned: `v2.0.0`.
- Tags are created only after the corresponding gate evidence is attached.
- A tag name must never be reused.
- GitHub Release is required for `gate-release-v2.0` and `v2.0.0`.

## Local / CI Gate

Required before RC:

```bash
make verify.release.v2_0_0.preflight
git diff --check
```

The preflight target expands to:

- `make verify.system.capability_baseline.report`
- `make verify.platform.release_policy.runtime`
- `make verify.backend.contract.closure.mainline`
- `make verify.restricted`

Required before formal `v2.0.0`:

```bash
make verify.release.v2_0_0.product_hardening
make verify.release.v2_0_0.governance.guard
PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard
make verify.release.v2_0_0.control_docs.guard
make verify.release.v2_0_0.evidence_manifest.guard
```

This target expands to `make verify.product.release.ready` and must be green
before the final tag.
The readiness chain includes `make verify.docs.product_boundary`, so new addon
modules and product-boundary edits must keep the formal product boundary
catalog complete before release.
The readiness chain includes `make verify.industry_module.product_boundary`,
which runs the industry boundary regression test before the guard and rejects
production manifest `demo` entries, bare runtime `pass`, bare runtime
`NotImplementedError`, and app delivery fallback boundary drift.
The readiness chain also includes `make verify.product.menu.release.ready`, so
formal product menu changes, system configuration entries, and runtime user
menu configuration boundaries must pass the menu release gate before release.
The readiness chain also includes
`make verify.frontend.widget_richness.post_ga.guard`, so x2many inline editing,
backend subviews, kanban/view-type semantics, and v2 chatter/attachments
projection remain part of formal hardening.

The platform performance sub-gate must measure the Web boot path with
`scene_ready_mode=registry`; full scene hydration remains a deep-link/runtime
path and is not the baseline startup payload.

The product readiness target expands to:

  - `verify.docs.product_boundary`
  - `verify.industry_module.product_boundary`
  - `verify.user_module.product_boundary`
  - `verify.product.surface.clean`
  - `verify.product.menu.release.ready`
  - `verify.product.complexity.bound`
  - `verify.product.bundle.isolation`
  - `verify.product.tier.enforcement`
  - `verify.product.delivery.productization.readiness.strict`
  - `verify.frontend.widget_richness.post_ga.guard`
  - `verify.ui.product.stability`
  - `verify.delivery.reproducible`
  - `verify.product.sla.baseline`

## Contract And Startup Gate

- `login -> system.init -> ui.contract` must remain unchanged.
- `role_surface.role_code` remains the role source of truth.
- `default_route` must come from the backend contract.
- Public intents must not be renamed.
- Intent canonical/alias snapshot must pass.
- Contract closure mainline must pass.

## Product Hardening Gate

- `make verify.release.v2_0_0.product_hardening` must pass before formal tag.
- If `verify.bundle.installation.ready` fails, update or repair the bundle
  installation baseline in a separate batch with explicit evidence.
- If `verify.platform.performance.smoke` fails on `system.init` payload size,
  confirm the smoke is exercising the Web boot registry mode before changing
  thresholds or startup contracts.
- Product hardening failures must not be hidden by the governance preflight.

## Dev Acceptance Gate

For `sc_demo` acceptance:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \
  ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
  make release.daily_dev.acceptance.publish
```

Required evidence:

- `artifacts/backend/dev_acceptance_release_probe.json`
- uploaded package checksum validation
- served frontend bundle DB/env verification
- `/api/v1/intent?db=sc_demo` OPTIONS/GET behavior
- required daily real-user login and `system.init` result
- product navigation guard result: action count range, forbidden label list, required path list, and required action target list all pass

## Prod-Sim Gate

Before formal release:

- `sc_prod_sim` upgrade or replay path is executed only through Makefile targets.
- Prod-sim acceptance evidence is validated with
  `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard`.
- Recorded sample artifact directories may validate schema shape only; they are
  not release signoff evidence.
- Frontend static assets are rebuilt for the intended target DB/env.
- Real-user acceptance uses named business users, not only service smoke users.
- Prod-sim evidence is kept separate from production evidence.

## Production Safety

Production release is a separate supervised operation.

- Follow `docs/ops/production_release_flow_standard_v1.md`.
- Follow `docs/ops/production_deployment_runbook_v1.md`.
- Follow `docs/ops/prod_command_policy.md`.
- `ENV=prod` and `.env.prod` are not allowed in Codex autonomous development.
- Production database is `sc_prod`.
- Production destructive reset is forbidden.
- Any production module upgrade requires `PROD_DANGER=1` and an allowed Makefile target.

## Post-Release

- Confirm `git rev-parse v2.0.0` equals the intended `main` commit.
- Publish GitHub Release for `v2.0.0`.
- Attach or link evidence from `docs/ops/releases/v2.0.0/evidence_manifest.md`.
- Record deployment acceptance separately if production deployment follows.
- If production deployment follows, create a concrete deployment record from `docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md` and run `make verify.production_deployment.record.guard`.
- If production deployment follows, rerun `make verify.production_release.flow.guard` to verify the production release-flow control plane remains wired at deployment time.
- If production deployment includes migrated or legacy attachments, run `make history.attachment.custody.probe.prod`; if it reports a marker gap, snapshot affected `ir_attachment` rows before `make legacy_attachment.custody_marker.backfill.prod`.

## Stop Conditions

- Any required gate fails.
- Snapshot drift is not explained.
- Public intent rename or semantic drift is detected.
- Prod and prod-sim evidence are mixed.
- The release commit is not clean or not on `main`.
