# Project State Write Policy v1

## Data Import

Import policy:

- write `lifecycle_state` as the normalized business status;
- then derive `stage_id` from the lifecycle mapping;
- preserve raw source values in `legacy_state`, `legacy_stage_id`, and
  `legacy_stage_name`;
- do not infer lifecycle from project name, company text, or UI stage.

For safe create-only skeleton imports:

- if lifecycle conversion is not approved, write no explicit lifecycle and let
  system default produce `lifecycle_state=draft` and `stage_id=筹备中`;
- when lifecycle conversion is approved, write lifecycle first and map stage
  second.

## User Stage Drag / Stage Change

Target policy:

- stage drag may adjust UI placement only within allowed stage guard rules;
- stage drag must not reverse-update `lifecycle_state`;
- stage drag must not bypass lifecycle transition guards;
- stage drag must not become the business truth.

This means:

```text
stage_id -> lifecycle_state reverse sync is forbidden
```

## Lifecycle Change

Lifecycle change policy:

```text
lifecycle_state change -> validate transition -> update stage_id from mapping
```

Lifecycle is allowed to update stage because stage is the UI projection.

## Existing Implementation Note

Current code already maps lifecycle to stage during create/write. It also blocks
manual stage movement beyond derived business signals. This governance document
freezes the desired direction as one-way truth flow:

```text
lifecycle_state => stage_id
stage_id != lifecycle_state truth
```
