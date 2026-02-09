# Reason Codes Contract (Phase 10)

This document defines the canonical reason-code taxonomy used by Phase 10 interaction contracts.

## 1. Registry Source

Backend registry module:

- `addons/smart_core/utils/reason_codes.py` (canonical registry + mapping)
- `addons/smart_construction_core/handlers/reason_codes.py` (compatibility export + scene-specific adapters)
- `addons/smart_core/handlers/reason_codes.py` (compatibility export for batch handlers)

Current shared consumers:

- `addons/smart_construction_core/handlers/my_work_complete.py`
- `addons/smart_construction_core/handlers/capability_visibility_report.py`

## 2. Canonical Reason Codes

- `OK`
- `DONE`
- `PARTIAL_FAILED`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `INVALID_ID`
- `UNSUPPORTED_SOURCE`
- `USER_ERROR`
- `INTERNAL_ERROR`
- `ACCESS_RESTRICTED`
- `CONFLICT`
- `WRITE_FAILED`
- `IDEMPOTENCY_CONFLICT`
- `REPLAY_WINDOW_EXPIRED`

## 3. My Work Failure Meta Contract

For `my.work.complete` and `my.work.complete_batch`, failures return:

- `reason_code`
- `retryable`
- `error_category`
- `suggested_action`

For batch completion (`my.work.complete_batch`), response also includes:

- `request_id` (caller-supplied or server-generated)
- `idempotency_key` (defaults to `request_id`)
- `idempotency_fingerprint`
- `idempotent_replay` (`true` when served from recent replay window)
- `replay_window_expired` (`true` when same key+fingerprint exists but outside replay window)
- `idempotency_replay_reason_code` (`REPLAY_WINDOW_EXPIRED` when expired)
- `trace_id` (server-generated batch trace)
- `failed_retry_ids` (default retry target list where `retryable=true`)

For generic batch write intent (`api.data.batch`), response includes:

- `request_id`
- `trace_id`
- `failed_retry_ids`
- `replay_window_expired`
- `idempotency_replay_reason_code`
- `replay_from_audit_id` (replay source audit id; `0` when not replayed)
- `replay_original_trace_id` (trace of original replay source; empty when not replayed)
- `replay_age_ms` (age from replay source timestamp; `0` when not replayed)

Idempotency semantics for `api.data.batch`:

- same key + same fingerprint -> replay (`idempotent_replay=true`)
- same key + different fingerprint -> `IDEMPOTENCY_CONFLICT` (409)
- same key + same fingerprint but outside replay window -> execute as new request with `replay_window_expired=true` and `idempotency_replay_reason_code=REPLAY_WINDOW_EXPIRED`
- `failed_reason_summary` (array of `{reason_code, count}`)
- `failed_retryable_summary` (`{retryable, non_retryable}`)
- per-row structured fields:
  - `reason_code`
  - `retryable`
  - `error_category`
  - `suggested_action`

Expected behavior:

- Access failures: `PERMISSION_DENIED`, non-retryable
- Input/validation failures: `INVALID_ID` / `UNSUPPORTED_SOURCE` / `USER_ERROR`, non-retryable
- Missing records: `NOT_FOUND`, non-retryable
- Unknown/runtime failures: `INTERNAL_ERROR`, retryable

Idempotency semantics for `my.work.complete_batch`:

- same key + same fingerprint -> replay (`idempotent_replay=true`)
- same key + different fingerprint -> `IDEMPOTENCY_CONFLICT` (HTTP-like conflict)
- suggested action for conflict: `use_new_request_id`
- conflict meta: `retryable=false`, `error_category=conflict`
- same key + same fingerprint but outside replay window -> execute as new request with `replay_window_expired=true` and `idempotency_replay_reason_code=REPLAY_WINDOW_EXPIRED`

## 4. Capability Suggested Action Mapping

Capability visibility report maps reason codes into `suggested_action`.

Examples:

- `PERMISSION_DENIED` -> `request_access`
- `FEATURE_DISABLED` -> `enable_feature_flag`
- `ENTITLEMENT_UNAVAILABLE` -> `upgrade_subscription`
- `ROLE_SCOPE_MISMATCH` -> `switch_role_or_scope`
- `CAPABILITY_SCOPE_MISMATCH` -> `switch_role_or_scope`
- `ACCESS_RESTRICTED` -> `check_prerequisites`
- `state=PREVIEW` -> `wait_release` (state-level override)

## 5. Extension Rule

When introducing new reason codes:

1. Add code to `reason_codes.py`.
2. Add/adjust mapping logic there (not in individual handlers).
3. Update this document.
4. Add/adjust backend tests for the new mapping.
