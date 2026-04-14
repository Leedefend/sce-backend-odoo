# Project State Alignment Actions v1

## Goal

Align implementation with the frozen rule:

```text
lifecycle_state = 主状态
stage_id = UI投影
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
```

This document is advisory only. It does not change code.

## Recommended Actions

### Action 1: Keep Lifecycle As The Only Business Transition Entry

All business transitions should continue to use:

```text
action_set_lifecycle_state(...)
write({"lifecycle_state": ...})
```

Do not create new business actions that write only `stage_id`.

### Action 2: Reclassify Manual Stage Writes As UI-Only

Later implementation should make manual `stage_id` writes one of:

- blocked unless they exactly match the lifecycle-derived stage; or
- allowed only under an explicit UI-only context and never interpreted as
  lifecycle truth.

### Action 3: Decide Signal-Based Stage Sync Policy

The team must choose one:

| Option | Meaning |
| --- | --- |
| Accept signal sync | `_sync_stage_from_signals` remains, but documentation and UI must treat it as guidance only |
| Restrict signal sync | stage sync only follows lifecycle; business signals must trigger lifecycle transition gates |

For strict governance, restrict signal sync.

### Action 4: Import Gate Rule

Before expanding create-only import:

1. confirm `stage_id=筹备中` is acceptable for skeleton records;
2. confirm stage is UI-only;
3. do not import normalized stage separately;
4. when lifecycle conversion is approved, write lifecycle and derive stage.

### Action 5: Later Code Alignment Batch

If strict enforcement is required, open a separate implementation batch to:

- audit all `stage_id` write callers;
- block standalone `stage_id` writes from user operations;
- keep lifecycle-to-stage sync;
- either remove or re-scope `_sync_stage_from_signals`;
- add tests proving `stage_id` cannot mutate `lifecycle_state`.

## Current Next-Step Decision

Do not expand import yet. First decide whether the existing signal-based stage
sync is acceptable as UI-only behavior or must be restricted.
