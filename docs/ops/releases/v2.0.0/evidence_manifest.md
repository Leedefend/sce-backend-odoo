# v2.0.0 Evidence Manifest

This manifest supersedes the planned `v1.0.0` release line because the remote
`v1.0.0` tag already exists and tag names must not be reused.

## Required Before `gate-release-v2.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| System capability baseline | `make verify.system.capability_baseline.report` | PASS | `artifacts/backend/system_capability_baseline_report.json` |
| System capability baseline schema | `make verify.system.capability_baseline.report.schema.guard` | PASS | `artifacts/backend/system_capability_baseline_report.json` |
| Platform release policy runtime | `make verify.platform.release_policy.runtime` | PASS | `artifacts/backend/platform_release_policy_runtime_probe.json` |
| Platform release policy runtime schema | `make verify.platform.release_policy.runtime.schema.guard` | PASS | `artifacts/backend/platform_release_policy_runtime_probe.json` |
| Backend contract closure | `make verify.backend.contract.closure.mainline` | PASS | `artifacts/backend/backend_contract_closure_mainline_summary.json` |
| Backend contract closure summary schema | `make verify.backend.contract.closure.mainline.summary.schema.guard` | PASS | `artifacts/backend/backend_contract_closure_mainline_summary.json` |
| Backend contract closure snapshot schema | `make verify.backend.contract.closure.snapshot.schema.guard` | PASS | `artifacts/backend/backend_contract_closure_snapshot.json` |
| Restricted product mainline | `make verify.restricted` | PASS | `artifacts/backend/delivery_mainline_run_summary.json` |
| Restricted product mainline schema | `make verify.product.delivery.mainline.summary.schema.guard` | PASS | `artifacts/backend/delivery_mainline_run_summary.json` |
| Diff hygiene | `git diff --check` | PASS | terminal output |

## Required Before `v2.0.0-rc1`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Release preflight | `make verify.release.v2_0_0.preflight` | PASS | aggregate terminal output |
| Action closure smoke | `make verify.product.delivery.action_closure.smoke` | PASS | `artifacts/backend/product_delivery_action_closure_report.json` |
| Action closure schema | `make verify.product.delivery.action_closure.schema.guard` | PASS | `artifacts/backend/product_delivery_action_closure_report.json` |
| Module capability smoke | `make verify.product.delivery.module_capability.smoke` | PASS | `artifacts/backend/product_delivery_module9_smoke_report.json` |
| Module capability schema | `make verify.product.delivery.module_capability.schema.guard` | PASS | `artifacts/backend/product_delivery_module9_smoke_report.json` |
| Intent alias snapshot | `make verify.intent.canonical_alias.snapshot.guard` | PASS | `artifacts/backend/intent_canonical_alias_snapshot.json` |
| Intent alias snapshot schema | `make verify.intent.canonical_alias.snapshot.schema.guard` | PASS | `artifacts/backend/intent_canonical_alias_snapshot.json` |

## Required Product Hardening Before Formal `v2.0.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Product release readiness | `make verify.release.v2_0_0.product_hardening` | PASS | `artifacts/backend/bundle_installation_report.json` and related product gate artifacts |
| Low-code boundary hardening | included in `make verify.release.v2_0_0.product_hardening` via `verify.product.surface.clean` | PASS | `artifacts/backend/lowcode_config_runtime_boundary_guard.json` and `artifacts/backend/business_config_contract_snapshot.json` |
| P2 user module low-code baseline | included in `make verify.release.v2_0_0.product_hardening` via `verify.lowcode_config.customer_module_asset.pipeline` and `verify.lowcode_config.customer_module_asset.release_hardening.guard` | PASS | `addons/smart_construction_custom/data/lowcode_customer_config_baseline_manifest_v1.json` |
| Bundle installation schema | `make verify.bundle.installation.ready.schema.guard` | PASS | `artifacts/backend/bundle_installation_report.json` |
| View richness hardening | included in `make verify.release.v2_0_0.product_hardening` | PASS | `docs/product/view_richness_post_ga_report_v1.md` |
| Platform performance smoke | included in `make verify.release.v2_0_0.product_hardening` | PASS | `artifacts/backend/platform_performance_smoke.json` |
| Platform performance schema | `make verify.platform.performance.smoke.schema.guard` | PASS | `artifacts/backend/platform_performance_smoke.json` |

## Required Before Formal `v2.0.0`

| Evidence | Command | Required Result | Artifact |
|---|---|---|---|
| Dev acceptance publish | `make release.daily_dev.acceptance.publish` with dev env vars, including product navigation path and action-target guards | PASS | `artifacts/backend/dev_acceptance_release_probe.json` |
| Dev acceptance schema | `make verify.dev.acceptance.release.schema.guard` | PASS | `artifacts/backend/dev_acceptance_release_probe.json` |
| Prod-sim acceptance | governed prod-sim Makefile flow | PASS | `artifacts/migration/fresh_replay_validity_20260508T1720` |
| Prod-sim acceptance schema | `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.prod.sim.acceptance.evidence.schema.guard` | PASS | `scbs_release_acceptance_strict_result_v1.json`, `scbs_release_acceptance_strict_v1.md`, and `scbs_no_legacy_replay_acceptance_result_v1.json` under the recorded run dir |
| Release checklist signoff | manual review | PASS | `docs/ops/release_checklist_v2.0.0.md` |
| Release checklist guard | `make verify.release.v2_0_0.checklist.guard` | PASS | `docs/ops/release_checklist_v2.0.0.md` |
| Evidence manifest guard | `make verify.release.v2_0_0.evidence_manifest.guard` | PASS | `docs/ops/releases/v2.0.0/evidence_manifest.md` |
| Release control docs guard | `make verify.release.v2_0_0.control_docs.guard` | PASS | `docs/ops/releases/v2.0.0/README.md`, `docs/ops/release_notes_v2.0.0.md`, `docs/ops/versioning.md`, `docs/ops/releases/README.md`, `docs/ops/releases/README.zh.md`, and `docs/ops/verify/README.md` |
| Release governance guard | `make verify.release.v2_0_0.governance.guard` | PASS | release-control docs, evidence manifest, checklist, and production release-flow guard terminal output |
| Formal evidence schema guard | `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard` | PASS | governance, bundle installation schema, platform performance schema, dev acceptance schema, and prod-sim acceptance evidence shape guard terminal output |

## Evidence Rules

- Evidence from `sc_prod_sim` must not be presented as `sc_prod` evidence.
- Production deployment evidence is recorded separately after supervised
  deployment begins.
- If production deployment includes migrated or legacy attachments, production
  evidence must include `make history.attachment.custody.probe.prod`.
- If the attachment custody probe reports a marker gap, snapshot affected
  `ir_attachment` rows before `make legacy_attachment.custody_marker.backfill.prod`.
- Snapshot changes must include the command that produced them.
- Failed evidence is not overwritten without preserving the failure reason in an
  iteration record.

## Current Local Verification Status

- Command: `make verify.release.v2_0_0.product_hardening`
- Status: PASS in the current local `sc_demo` dev verification environment
  after uninstalling `smart_construction_demo` and clearing the remaining
  `smart_construction_demo` XMLID rows that Odoo could not remove because
  audit-log foreign keys still reference retained users.
- Demo-data release gate:
  `DB_NAME=sc_demo make verify.product.no_demo_data` PASS.
- Demo-data closure facts on `sc_demo`:
  `smart_construction_demo` module state is `uninstalled`,
  `smart_construction_demo` XMLID count is `0`, and
  `verify.product.no_demo_data` reports PASS.
- Previous blocker preserved:
  before local cleanup, `verify.product.no_demo_data` failed because
  `smart_construction_demo` was installed, `res.partner` had 3 active
  demo-name records, and `smart_construction_demo` XMLID count was 112.
- Latest passing sub-gate in this batch:
  `make verify.product.sla.baseline`.
- Closed hardening target:
  `make verify.release.v2_0_0.product_hardening` PASS.
- Release hardening also includes
  `verify.frontend.widget_richness.post_ga.guard` for x2many, subviews,
  kanban/view-type semantics, and v2 chatter/attachments projection, plus
  `verify.lowcode_config.customer_module_asset.pipeline` for customer low-code
  asset candidate, draft, decision template, dry-run apply, safety tests, and
  replay guard, and
  `verify.lowcode_config.customer_module_asset.release_hardening.guard` to keep
  the customer asset pipeline wired into formal product release readiness.
- Artifacts:
  - `artifacts/backend/bundle_installation_report.json`
  - `artifacts/backend/platform_performance_smoke.json`
  - `artifacts/backend/non_demo_data_contamination_guard.json`
- Evidence shape guards:
  - `make verify.product.no_demo_data.schema.guard`
  - `make verify.bundle.installation.ready.schema.guard`
  - `make verify.platform.performance.smoke.schema.guard`
- Schema-only guard runs may use recorded artifact directories to verify evidence
  shape, but recorded sample artifacts are not release signoff evidence.
- Recorded prod-sim schema evidence path:
  `artifacts/migration/fresh_replay_validity_20260508T1720`, verified with
  `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=artifacts/migration/fresh_replay_validity_20260508T1720 make verify.release.v2_0_0.formal_evidence.schema.guard`.
- Note: before creating `gate-release-v2.0` or `v2.0.0-rc1`, rerun required
  gates on a clean reviewed release database and attach the fresh artifacts.
- Note: before creating final `v2.0.0`, rerun
  `PROD_SIM_ACCEPTANCE_ARTIFACT_DIR=<run_dir> make verify.release.v2_0_0.formal_evidence.schema.guard`
  against the recorded prod-sim acceptance run directory for that release
  candidate.
