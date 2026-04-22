# Backend MyWork Completion Capability Contract Screen V1

## Problem

Frontend currently decides whether a MyWork row is completable through:

- `item.section === 'todo'`
- `item.source === 'mail.activity'`

This is invalid because completion eligibility is a workflow/action fact of the
row, not a frontend inference from source identity.

## Ownership

Primary owner:
- `business-fact layer`

Secondary owner:
- `scene-orchestration layer` only if a completion action envelope must be
  emitted in a scene-ready shape

## Minimum Contract Target

Each MyWork row should expose an explicit completion capability fact.

Minimum fact:

```json
{
  "can_complete": true
}
```

If completion is actionable from the current page, backend should also expose a
minimal action descriptor.

Minimum action envelope:

```json
{
  "can_complete": true,
  "complete_action": {
    "intent": "my_work.complete",
    "label": "完成",
    "enabled": true
  }
}
```

## Required Semantics

### Business-fact semantics

Per row:
- `can_complete`
- optional `complete_block_reason`

These facts answer:
- whether the row is completable now
- if not, why it is blocked

### Scene-orchestration semantics

Only needed if page should render/execute completion directly:
- `complete_action.intent`
- `complete_action.label`
- `complete_action.enabled`

Optional:
- `complete_action.confirmation_text`
- `complete_action.success_message`

## Frontend Consumption Rule

Frontend follow-up target:
- stop checking `item.source === 'mail.activity'`
- use `row.can_complete === true`
- if completion UI is rendered, bind it to `complete_action`

## Recommended Implementation Order

1. backend business-fact supply for `can_complete`
2. backend orchestration supply for `complete_action` if current page executes
   completion
3. frontend cleanup batch removing source-based inference

## Stop Boundary

Do not let frontend infer completion behavior from row source/model after this
contract lands.
