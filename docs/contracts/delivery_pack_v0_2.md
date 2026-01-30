# Delivery Pack v0.2

## Overview

Delivery Pack defines a portable bundle of capabilities and scenes with
integrity checking, deterministic diff, and upgrade policies.

## Pack Meta

Fields:
- `pack_id` (uuid)
- `pack_version` (v0.2)
- `hash_algo` (sha256)
- `payload_hash` (hash of normalized payload)
- `generated_at`
- `source_db`
- `modules`
- `contract_version`

Hash is calculated from:
```
{
  "upgrade_policy": {...},
  "capabilities": [...],
  "scenes": [...]
}
```

## Export

Endpoint: `GET /api/scenes/export`

Includes:
- `pack_meta`
- `upgrade_policy`
- `capabilities`
- `scenes`

## Import

Endpoint: `POST /api/scenes/import`

Rules:
- If `payload_hash` present, import validates hash. Mismatch => `PACK_HASH_MISMATCH`.
- `mode` defaults to `upgrade_policy.default_mode`.
- `replace` requires `confirm=true` unless `dry_run=true`.

## Diff v2

`diff_v2` structure:
```
{
  "mode": "merge|replace",
  "dry_run": true|false,
  "creates": [{ "entity_type": "...", "key": "...", "fields_changed": [...] }],
  "updates": [{ "entity_type": "...", "key": "...", "fields_changed": [...] }],
  "deletes": [{ "entity_type": "...", "scene": "...", "capability": "..." }],
  "risk_level": "low|medium|high"
}
```

Legacy `diff` is still returned for backward compatibility.

## Upgrade Policy

`upgrade_policy.merge_fields` defines allowed fields to update in merge mode:
- capability: `name`, `ui_label`, `ui_hint`, `intent`, `default_payload`, `tags`, `status`, `version`, `required_groups`, `smoke_test`, `is_test`
- scene: `name`, `layout`, `is_default`, `version`, `state`
- tile: `title`, `subtitle`, `icon`, `badge`, `visible`, `span`, `min_width`, `payload_override`, `sequence`, `active`

## Audit

Import creates audit logs:
- `sc.scene.audit.log` (payload_diff = diff_v2)
- `sc.capability.audit.log` for create/update with `source_pack_id`
