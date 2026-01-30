# Capability Contract v0.2

## Overview

Capability Contract defines how platform capabilities are described, discovered,
validated, and tested. This contract is designed for multi-industry extensions
and catalog-driven delivery packs.

## Versioning

- Contract version: v0.2
- API version: v1
- Backward compatibility:
  - Adding fields is backward compatible.
  - Removing fields requires a major contract bump.
  - Behavior changes require explicit migration notes.

## Capability Describe (intent)

Intent: `capability.describe`

Input (params):
- `key` (string) OR `capability_id` (int)
- `capability_key` is accepted as alias for `key`

Output:
- `key`, `name`, `ui_label`, `ui_hint`
- `intent`
- `default_payload`
- `payload_schema` (inferred types)
- `required_groups` (xmlid list)
- `tags`
- `status` (alpha/beta/ga)
- `version`
- `smoke_test` (boolean)
- `contract_version`, `api_version`

Example:
```
{
  "intent": "capability.describe",
  "params": {
    "key": "project.list"
  }
}
```

## Capability Search (HTTP)

Endpoint: `GET /api/capabilities/search`

Query parameters:
- `q`: keyword match on key/name/ui_label
- `tags`: comma-separated tags (match any)
- `status`: comma-separated status values
- `intent`: exact intent name
- `smoke`: `1|true|yes` to filter `smoke_test=true`

Response:
```
{
  "ok": true,
  "data": {
    "capabilities": [ ... ],
    "count": 12
  }
}
```

## Capability Lint (HTTP)

Endpoint: `GET /api/capabilities/lint` (admin only)

Output:
- `status`: `pass|fail`
- `issues`: list of structured issues

Lint rules (minimum):
- key uniqueness
- intent present and allowed
- required group xmlids exist
- menu/action xmlids resolve (when provided)
- test-only capabilities (is_test=true) are excluded by default; include_tests=1 to validate them

## Capability Smoke Tests

Smoke tests are generated from catalog entries marked with:
- `smoke_test=true`

`make verify.e2e.capability_smoke` will:
- Discover smoke capabilities via `search?smoke=1`
- Call each capability intent using `default_payload`
- Write raw and normalized outputs under `/tmp/capability_smoke`

## Error Handling

- Missing capability: 404
- Permission denied: 403
- Admin-required lint: 403

## Delivery Pack Notes

Capabilities in delivery packs should include:
- `key`, `name`, `intent`, `default_payload`, `tags`, `status`, `version`
- `smoke_test` may be used to mark safe test targets
