# Phase 10 Backend Hardening: api.data.batch Structured Contract

## Summary

This PR aligns `api.data.batch` with Phase 10 structured failure/trace conventions.

## What Changed

- `addons/smart_core/handlers/api_data_batch.py`
  - add batch-level fields:
    - `request_id`
    - `trace_id`
    - `failed_retry_ids`
  - normalize idempotency default:
    - `idempotency_key` falls back to `request_id` when not provided
  - add per-row structured fields:
    - `retryable`
    - `error_category`
    - `suggested_action`
    - `trace_id`
  - classify common failures:
    - `NOT_FOUND` -> non-retryable, `not_found`, `refresh_list`
    - `CONFLICT` -> retryable, `conflict`, `reload_then_retry`
    - `PERMISSION_DENIED` -> non-retryable, `permission`, `request_access`
    - `WRITE_FAILED` -> retryable, `transient`, `retry`
  - failed CSV now includes:
    - `retryable`
    - `error_category`

- tests:
  - `addons/smart_construction_core/tests/test_api_data_batch_contract_backend.py`
  - registered in `addons/smart_construction_core/tests/__init__.py`

- docs:
  - `docs/contract/reason_codes.md` adds `api.data.batch` contract section

## Validation

```bash
make test MODULE=smart_construction_core TEST_TAGS=api_data_batch_backend,my_work_backend DB_NAME=sc_demo
```

Passed in this branch context.
