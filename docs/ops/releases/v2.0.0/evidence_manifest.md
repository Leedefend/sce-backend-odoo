# v2.0.0 Evidence Manifest

This manifest supersedes the planned `v1.0.0` release line because the remote
`v1.0.0` tag already exists and tag names must not be reused.

## Required Before `gate-release-v2.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| System capability baseline | `make verify.system.capability_baseline.report` | PASS | `artifacts/backend/system_capability_baseline_report.json` |
| Backend contract closure | `make verify.backend.contract.closure.mainline` | PASS | `artifacts/backend/backend_contract_closure_mainline_summary.json` |
| Restricted product mainline | `make verify.restricted` | PASS | `artifacts/backend/delivery_mainline_run_summary.json` |
| Diff hygiene | `git diff --check` | PASS | terminal output |

## Required Before `v2.0.0-rc1`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Release preflight | `make verify.release.v2_0_0.preflight` | PASS | aggregate terminal output |
| Action closure smoke | `make verify.product.delivery.action_closure.smoke` | PASS | `artifacts/backend/product_delivery_action_closure_report.json` |
| Module-9 smoke | `make verify.product.delivery.module9.smoke` | PASS | `artifacts/backend/product_delivery_module9_smoke_report.json` |
| Intent alias snapshot | `make verify.intent.canonical_alias.snapshot.guard` | PASS | `artifacts/backend/intent_canonical_alias_snapshot.json` |

## Required Product Hardening Before Formal `v2.0.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Product release readiness | `make verify.release.v2_0_0.product_hardening` | PASS | `artifacts/backend/bundle_installation_report.json` and related product gate artifacts |
| Platform performance smoke | included in `make verify.release.v2_0_0.product_hardening` | PASS | `artifacts/backend/platform_performance_smoke.json` |

## Required Before Formal `v2.0.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Dev acceptance publish | `make release.dev.acceptance.publish` with dev env vars | PASS | `artifacts/backend/dev_acceptance_release_probe.json` |
| Prod-sim acceptance | governed prod-sim Makefile flow | PASS | prod-sim acceptance artifact path to be recorded |
| Release checklist signoff | manual review | PASS | `docs/ops/release_checklist_v2.0.0.md` |

## Evidence Rules

- Evidence from `sc_prod_sim` must not be presented as `sc_prod` evidence.
- Production deployment evidence is recorded separately after supervised
  deployment begins.
- Snapshot changes must include the command that produced them.
- Failed evidence is not overwritten without preserving the failure reason in an
  iteration record.

## Current Blocker Status

- Command: `make verify.release.v2_0_0.product_hardening`
- Status: PASS in the local `sc_demo` dev verification environment.
- Closed sub-gates: `verify.bundle.installation.ready` and
  `verify.platform.performance.smoke`.
- Artifacts:
  - `artifacts/backend/bundle_installation_report.json`
  - `artifacts/backend/platform_performance_smoke.json`
- Note: before creating `gate-release-v2.0` or `v2.0.0-rc1`, rerun required
  gates on the reviewed release commit and attach the fresh artifacts.
