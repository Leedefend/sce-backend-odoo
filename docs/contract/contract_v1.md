# Contract v1

Back to contract hub: `docs/contract/README.md`

## Success response

All API responses use a uniform envelope.

```json
{
  "ok": true,
  "contract_version": "v1",
  "server_time": "2024-01-01T00:00:00Z",
  "trace_id": "2f9b3f1c-6d9a-4b59-9b8f-3c0f2d2f4c9a",
  "warnings": [],
  "data": {}
}
```

Fields:
- `ok`: boolean success flag.
- `contract_version`: string, fixed as `v1`.
- `server_time`: ISO-8601 UTC time.
- `trace_id`: per-request UUID v4.
- `warnings`: array of warning strings or objects.
- `data`: response payload.

## Error response

```json
{
  "ok": false,
  "contract_version": "v1",
  "server_time": "2024-01-01T00:00:00Z",
  "trace_id": "2f9b3f1c-6d9a-4b59-9b8f-3c0f2d2f4c9a",
  "warnings": [],
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid id",
    "details": {
      "field": "id"
    },
    "trace_id": "2f9b3f1c-6d9a-4b59-9b8f-3c0f2d2f4c9a"
  }
}
```

Fields:
- `error.code`: string error code.
- `error.message`: human readable error message.
- `error.details`: optional object for debugging.
- `error.trace_id`: same as top-level `trace_id`.

## Contract verification entry points

- `make verify.portal.envelope_smoke.container`
  - validates runtime envelope expectations (`ok=true`, `meta.trace_id`) for core intents:
    - `app.init`/scene contract path
    - `my.work.summary`
    - `execute_button`
    - cross-stack contract probe
- `make verify.portal.ui.v0_8.semantic.container`
  - includes `verify.portal.envelope_smoke.container` in semantic portal gate aggregation.

## Snapshot baseline migration

2026-01-25:
- Added `contract_version` at snapshot root for contract baselines.
- Canonicalized `meta_fields` ordering by field name and normalized domain `in/not in` value ordering.
- Updated baselines: menu_tree_admin, menu_tree_pm, project_list_pm, project_form_pm, execute_button_pm, form_save_simple_pm, attachment_list_pm.
