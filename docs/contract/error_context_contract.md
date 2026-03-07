# Error Context Contract (Frontend Consumption)

Version: `v0.1`  
Scope: `/api/v1/intent` error envelope + frontend status consumption

## Contract Shape

Backend error envelope may include:

```json
{
  "ok": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "...",
    "reason_code": "PERMISSION_DENIED",
    "error_category": "permission",
    "retryable": false,
    "suggested_action": "request_access",
    "details": {
      "intent": "api.data.batch",
      "model": "project.project",
      "op": "batch.archive"
    }
  },
  "meta": {
    "trace_id": "..."
  }
}
```

## Frontend Mapping

`frontend/apps/web/src/api/client.ts`

- Parse and expose:
  - `reason_code`
  - `error_category`
  - `retryable`
  - `suggested_action`
  - `details` (`model/op/intent`)
- Store in `ApiError.details`.

`frontend/apps/web/src/composables/useStatus.ts`

- `StatusError.details` must preserve `ApiError.details`.
- `resolveErrorCopy` should include context hint:
  - `Context: model/op [REASON]`

`frontend/apps/web/src/components/StatusPanel.vue`

- HUD mode: show `Model` and `Operation`.
- Non-HUD mode: show compact context line:
  - `Context: model/op [REASON]`

## Governance Rule

`scripts/verify/frontend_error_context_contract_guard.py` enforces required tokens in:

- `api/client.ts`
- `composables/useStatus.ts`
- `components/StatusPanel.vue`
- `app/errorContext.ts`

Run:

```bash
make verify.frontend.error_context.contract.guard
```
