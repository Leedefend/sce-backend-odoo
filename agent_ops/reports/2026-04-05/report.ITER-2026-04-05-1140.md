# ITER-2026-04-05-1140

- status: PASS
- mode: execute
- layer_target: Governance Monitoring
- module: runtime_capture_evidence
- risk: low
- publishability: internal

## Summary of Change

- added:
  - `agent_ops/tasks/ITER-2026-04-05-1140.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1140.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1140.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- updated:
  - `scripts/verify/capability_payload_real_env_capture.py`

## Root-Cause Diagnosis (Code First)

- finding:
  - previous script only extracted capabilities from `data.capabilities` / `data.catalog.capabilities`.
  - startup payload in current runtime minimal surface does not expose top-level `data.capabilities`; capabilities are emitted under `data.delivery_engine_v1.capabilities`.
- action:
  - updated extraction fallback chain to include `delivery_engine_v1.capabilities` (and `release_navigation_v1.capabilities` fallback).
- evidence:
  - trusted capture now returns non-empty counts: `v1_count=6`, `v2_count=6`.

## Root-Cause Diagnosis (DB Upgrade/State)

- live db probe (`sc_prod_sim`):
  - `smart_core` / `smart_construction_core` / `smart_construction_scene` are `installed`.
  - `smart_core.capability_registry_query_v2_enabled=0` present.
  - `sc.capability` has rows (sample keys include `project.board.open`, `governance.capability.matrix`).
- live db probe (`sc_demo`):
  - `smart_construction_scene` is `uninstalled`, `sc.capability` rows are 0.
- conclusion:
  - for `sc_prod_sim`, empty counts were **not** caused by missing DB upgrade; primary cause was extraction path mismatch.
  - DB state differences explain lane behavior variance (`sc_demo` data-lane is incomplete).

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1140.yaml`: PASS
- `python3 -m py_compile scripts/verify/capability_payload_real_env_capture.py`: PASS
- trusted capture:
  - `E2E_BASE_URL=http://127.0.0.1:18069 E2E_DB=sc_prod_sim E2E_LOGIN=admin E2E_PASSWORD=admin python3 scripts/verify/capability_payload_real_env_capture.py --out-dir artifacts/capability_payload_capture_1140 --request-timeout-sec 8`: PASS
  - output: `artifacts/capability_payload_capture_1140/latest/capture_report.json` (`trusted`, `v1_count=6`, `v2_count=6`)
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- low: issue root cause is isolated and fixed in verification tooling.
- note: v1/v2 diff is currently zero change (`changed_count=0`) on this lane, which is expected for current runtime output path.

## Rollback Suggestion

- `git restore scripts/verify/capability_payload_real_env_capture.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1140.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1140.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1140.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next step suggestion: if needed, add lane-specific check that fails when target DB is missing `smart_construction_scene` or `sc.capability` rows, to prevent false-zero captures.
