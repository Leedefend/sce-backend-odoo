# Phase 10 Refactor: Idempotency Utility Extraction (My Work)

## Summary

This PR extracts reusable idempotency helpers for Phase 10 backend contracts and wires `my.work.complete_batch` to use them.

## Scope

- Added reusable utility module:
  - `addons/smart_core/utils/idempotency.py`
  - helpers:
    - request id normalization
    - fingerprint payload normalization
    - replay window parsing
    - recent audit lookup by idempotency key
    - ids summary (count/sample/hash)

- Refactored:
  - `addons/smart_construction_core/handlers/my_work_complete.py`
  - moved inline idempotency plumbing to shared helpers

## Behavior

- No contract regression intended.
- Existing replay/conflict semantics remain unchanged.

## Validation

```bash
make test MODULE=smart_construction_core TEST_TAGS=my_work_backend DB_NAME=sc_demo
```

Passed in this branch context.
