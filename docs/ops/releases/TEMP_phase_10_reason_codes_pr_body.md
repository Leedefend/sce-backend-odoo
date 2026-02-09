# Phase 10 Backend Hardening: Reason Codes + Batch Contract + Auto-fix Audit

## Summary

This PR continues Phase 10 backend hardening with three focused changes:

- centralize reason-code registry and mapping logic
- enrich `my.work.complete_batch` response contract for replay/idempotency workflows
- make extension auto-fix output traceable with old/new audit values

## Scope

Included:

- new backend registry module:
  - `addons/smart_construction_core/handlers/reason_codes.py`
- migrated mappings in:
  - `addons/smart_construction_core/handlers/my_work_complete.py`
  - `addons/smart_construction_core/handlers/capability_visibility_report.py`
- batch contract enrichment:
  - `request_id`
  - `trace_id`
  - `failed_retry_ids`
  - `failed_items[*].trace_id`
- extension auto-fix auditability:
  - `scripts/ops/apply_extension_modules.sh` now logs `trace_id`, `old`, `new`
- documentation:
  - `docs/contract/reason_codes.md`
- tests:
  - `addons/smart_construction_core/tests/test_reason_codes_backend.py`
  - updates in `addons/smart_construction_core/tests/test_my_work_backend.py`

## Validation

```bash
make test MODULE=smart_construction_core TEST_TAGS=reason_codes_backend DB_NAME=sc_demo
make test MODULE=smart_construction_core TEST_TAGS=my_work_backend,capability_contract_backend DB_NAME=sc_demo
make test MODULE=smart_construction_core TEST_TAGS=my_work_backend,reason_codes_backend DB_NAME=sc_demo
make verify.extension_modules.guard DB_NAME=sc_demo
```

All passed in this branch context.

## Notes

- Contract is backward-compatible for existing consumers; wrapper functions are retained in handlers.
- No owner-scene (`T10.4.x`) scope is included.
