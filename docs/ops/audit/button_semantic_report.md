# Button Semantic Report

- taxonomy: state_transition / permission_guard / fallback / deprecated
- snapshot_case_count: 8
- execute_button_statuses: [404]
- observed_404_count: 1
- explained_404_count: 1
- unexplained_404_count: 0
- unclassified_404_count: 0
- error_count: 0
- warning_count: 0

## 404 Allowlist

- execute_button:404 -> fallback (NOT_FOUND) [record missing/stale res_id under dry_run probe is expected fallback]

## Snapshot Case Classification

- execute_button_error -> fallback (docs/contract/snapshots/execute_button_error.json)
- execute_button_intent_dry_run_pm -> state_transition (docs/contract/snapshots/execute_button_intent_dry_run_pm.json)
- execute_button_missing_method -> fallback (docs/contract/snapshots/execute_button_missing_method.json)
- execute_button_missing_record -> fallback (docs/contract/snapshots/execute_button_missing_record.json)
- execute_button_not_allowed -> permission_guard (docs/contract/snapshots/execute_button_not_allowed.json)
- execute_button_pm -> state_transition (docs/contract/snapshots/execute_button_pm.json)
- portal_execute_button_not_allowed -> permission_guard (docs/contract/snapshots/portal_execute_button_not_allowed.json)
- portal_execute_button_pm -> state_transition (docs/contract/snapshots/portal_execute_button_pm.json)
