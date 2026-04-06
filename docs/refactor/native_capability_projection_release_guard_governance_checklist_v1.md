# Native Capability Projection Release Guard Governance Checklist v1

## Objective

Provide a compact operational checklist for the native capability projection
release guard bundle, mapping each guard to risk class and owner module.

## Bundle Target

- make target: `verify.architecture.native_capability_projection_release_guard_bundle`
- ownership: `platform` (`smart_core` + `scripts/verify`)
- intended usage: release readiness gate for native capability projection surface

## Guard Matrix

| Guard | Risk Class | Owner Module | Purpose |
| --- | --- | --- | --- |
| `verify.architecture.native_capability_ingestion_guard` | P0 | `scripts/verify` + `app_config_engine.capability.native` | Verify native ingestion path exists and is connected |
| `verify.architecture.native_capability_ingestion_lint_bundle` | P0 | `scripts/verify` + `app_config_engine.capability.native` | Ensure six native projection families are present |
| `verify.architecture.native_capability_runtime_exposure_baseline_guard` | P0 | `scripts/verify` + `app_config_engine.capability.projection` | Enforce centralized native type-to-intent baseline ownership |
| `verify.architecture.native_capability_runtime_exposure_payload_guard` | P1 | `scripts/verify` + `app_config_engine.capability.projection` | Ensure list/workspace projections expose runtime fields |
| `verify.architecture.runtime_exposure_projection_schema_snapshot_guard` | P1 | `scripts/verify` + `app_config_engine.capability.projection` | Freeze projection field schema for drift detection |
| `verify.architecture.runtime_exposure_evidence_snapshot_guard` | P2 | `scripts/verify` | Freeze runtime exposure evidence summary for regression tracking |
| `verify.architecture.native_capability_projection_coverage_report` | P1 | `scripts/verify` | Confirm native projection type coverage completeness |
| `verify.architecture.native_capability_projection_snapshot_guard` | P1 | `scripts/verify` | Freeze native projection adapter/call/type topology snapshot |
| `verify.architecture.native_capability_projection_release_readiness_summary_guard` | P1 | `scripts/verify` | Aggregate readiness into single PASS/FAIL envelope |

## Operational Checklist

1. Run `verify.architecture.native_capability_projection_release_guard_bundle`.
2. Confirm all guard statuses are PASS.
3. If FAIL occurs:
   - classify by guard risk class (P0/P1/P2),
   - route to owner module listed above,
   - stop release progression until corrected or explicitly waived.
4. For intentional structural change:
   - update implementation first,
   - refresh relevant baseline snapshots explicitly,
   - rerun full bundle to PASS,
   - record rationale in iteration report.

## Stop Rules

- Any P0 guard FAIL -> immediate stop.
- Repeated P1 FAIL across two iterations -> stop and open focused governance screen batch.
- P2 FAIL may proceed only with explicit platform owner sign-off and documented follow-up batch.

## Handoff Notes

- This checklist is governance metadata only; it does not modify runtime behavior.
- Runtime-facing truth remains in capability projection/runtime resolver modules.

