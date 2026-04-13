# v2 App Governance Gate Usage v1

## Purpose

Provide a single low-cost verification entry for v2 app governance chain.

## Recommended entry points

- Script alias:
  - `python3 scripts/verify/v2_app_verify_all.py --json`
- Make targets:
  - `make verify.v2.app.governance`
  - `make verify.v2.app.all`
  - `make verify.v2.app.verify_all_failure_path`

## Included checks

- `v2_app_reason_code_audit.py`
- `v2_app_contract_guard_audit.py`
- `v2_app_contract_snapshot_audit.py`
- `v2_session_bootstrap_contract_audit.py`
- `v2_meta_describe_model_contract_audit.py`
- `v2_ui_contract_contract_audit.py`
- `v2_first_scenario_contract_audit.py`
- `v2_execute_button_contract_audit.py`
- `v2_api_data_contract_audit.py`
- `v2_api_onchange_contract_audit.py`
- `v2_api_data_batch_contract_audit.py`
- `v2_api_data_create_contract_audit.py`
- `v2_api_data_unlink_contract_audit.py`
- `v2_file_upload_contract_audit.py`
- `v2_file_download_contract_audit.py`
- `v2_load_contract_contract_audit.py`
- `v2_intent_migration_freeze_audit.py`
- `v2_app_intent_contract_linkage_audit.py`
- `v2_app_ci_light_entry_audit.py`
- `v2_boundary_audit.py`
- `v2_rebuild_audit.py`
- `v2_intent_comparison_audit.py`
- `v2_focus_intent_promotion_state_machine_audit.py`
- `v2_app_verify_all_failure_path_audit.py`

## Failure-path guard

- Script:
  - `python3 scripts/verify/v2_app_verify_all_failure_path_audit.py --json`
- Purpose:
  - inject delegate failure and assert `v2_app_verify_all` returns `status=FAIL` with non-empty root `errors`.

## Focus compare diagnosis (non-blocking)

- Script:
  - `python3 scripts/verify/v2_focus_intent_compare_failure_summary.py --json`
- Included in governance gate as non-blocking diagnostics detail:
  - `non_blocking_diagnostics`
- Purpose:
  - expose `failure_stage/error_code/minimal_repro_payload/suggested_fix_area` for
    `session.bootstrap` / `meta.describe_model` / `ui.contract`
  - keep diagnosis visible without turning current compare period into hard block.

## Focus intent promotion/rollback state machine (blocking)

- Script:
  - `python3 scripts/verify/v2_focus_intent_promotion_state_machine_audit.py --json`
- Purpose:
  - use `allow_v2_candidate` from compare failure summary to produce per-intent
    promotion/rollback transition plan
  - hard-fail when any focus intent stays on `v2_primary` while candidate gate is
    not allowed

- Rollback-ready policy snapshot:
  - `artifacts/v2/v2_focus_intent_route_policy_rollback_v1.json`
  - keeps `session.bootstrap` / `meta.describe_model` / `ui.contract` fallback
    target at `v2_shadow`

## Output semantics

- `gate_version`: governance output schema version marker
- `gate_profile`: execution profile marker (`full` or `ci_light`)
- `summary.total_checks`: total included checks
- `summary.pass_checks`: passed checks count
- `summary.fail_checks`: failed checks count
- `failure_reasons`: flattened failure reason list with `check:reason` format

## Output schema guard

- Snapshot baseline:
  - `artifacts/v2/v2_app_governance_output_schema_v1.json`
- Guard audit:
  - `python3 scripts/verify/v2_app_governance_output_schema_audit.py --json`
- Snapshot also freezes `expected_checks` for governance detail chain.
- Migration freeze snapshot:
  - `artifacts/v2/v2_intent_migration_freeze_v1.json`
  - Blocks newly added v2 intents outside frozen baseline/allowlist.

## Notes

- This gate is for governance verification only.
- It does not replace single-script diagnosis when triaging specific failures.

## CI light entry

- Preferred CI light target:
  - `make verify.v2.app.ci.light`
- This target delegates to `verify.v2.app.all` and keeps governance checks lightweight.

- ci-light audit output includes:
  - `gate_version`
  - `gate_profile`

## Common output contract

- All `v2_app_*_audit` scripts expose at least:
  - `gate_version`
  - `gate_profile`
  - `status`
  - `errors`

- `v2_app_verify_all.py` root output also includes `errors`.

- Extended to core v2 audits:
  - `v2_boundary_audit.py`
  - `v2_rebuild_audit.py`
  - `v2_intent_comparison_audit.py`
