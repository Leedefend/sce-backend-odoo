# Reason Codes Contract (Phase 10)

This document defines the canonical reason-code taxonomy used by Phase 10 interaction contracts.

## 1. Registry Source

Backend registry module:

- `addons/smart_construction_core/handlers/reason_codes.py`

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

## 3. My Work Failure Meta Contract

For `my.work.complete` and `my.work.complete_batch`, failures return:

- `reason_code`
- `retryable`
- `error_category`
- `suggested_action`

For batch completion (`my.work.complete_batch`), response also includes:

- `request_id` (caller-supplied or server-generated)
- `trace_id` (server-generated batch trace)
- `failed_retry_ids` (default retry target list where `retryable=true`)

Expected behavior:

- Access failures: `PERMISSION_DENIED`, non-retryable
- Input/validation failures: `INVALID_ID` / `UNSUPPORTED_SOURCE` / `USER_ERROR`, non-retryable
- Missing records: `NOT_FOUND`, non-retryable
- Unknown/runtime failures: `INTERNAL_ERROR`, retryable

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
