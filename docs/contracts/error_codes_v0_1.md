# Error Codes v0.1

This document defines the standardized error envelope and handling guidance.

## Error envelope

```json
{
  "ok": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Missing required field: intent",
    "details": { "field": "intent" },
    "hint": "Check request payload",
    "fields": { "intent": "required" },
    "retryable": false
  },
  "meta": {
    "trace_id": "9f2a1c0e3b4d",
    "api_version": "v1",
    "contract_version": "v0.1"
  }
}
```

## Error codes

| code | HTTP | meaning | retryable | client action |
|---|---|---|---|---|
| BAD_REQUEST | 400 | Invalid or missing request parameters | no | Fix request payload, show validation message |
| AUTH_REQUIRED | 401 | Authentication required or token invalid/expired/revoked | no | Re-login, refresh token |
| PERMISSION_DENIED | 403 | User lacks permission | no | Show forbidden message or request access |
| INTENT_NOT_FOUND | 404 | Intent/endpoint not found | no | Report client misconfiguration |
| VALIDATION_ERROR | 422 | Contract validation/self-check failed | no | Report to backend team |
| INTERNAL_ERROR | 500 | Server error | maybe | Show error and allow retry |

## Trace ID
- `meta.trace_id` must be included in every error response.
- Use `trace_id` for backend log correlation.
