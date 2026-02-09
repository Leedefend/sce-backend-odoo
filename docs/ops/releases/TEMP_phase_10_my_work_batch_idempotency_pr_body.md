# Phase 10 Backend Hardening: my.work.complete_batch Idempotent Replay

## Summary

This PR adds idempotent replay support to `my.work.complete_batch` with audit-backed replay in a short time window.

## What Changed

- `addons/smart_construction_core/handlers/my_work_complete.py`
  - adds `idempotency_key` (defaults to `request_id`)
  - adds `idempotency_fingerprint`
  - adds `idempotent_replay`
  - adds replay lookup from recent `sc.audit.log` (`MY_WORK_COMPLETE_BATCH`)
  - writes batch audit payload for replayability
  - keeps existing response fields (`request_id`, `trace_id`, `failed_retry_ids`, etc.)

- `addons/smart_construction_core/tests/test_my_work_backend.py`
  - extends batch contract assertions for new idempotency fields
  - adds replay test when `sc.audit.log` is available

- `docs/contract/reason_codes.md`
  - documents `my.work.complete_batch` idempotency contract fields

## Validation

```bash
make test MODULE=smart_construction_core TEST_TAGS=my_work_backend DB_NAME=sc_demo
```

Passed in this branch context.
