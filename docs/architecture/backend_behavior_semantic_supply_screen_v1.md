# Backend Behavior Semantic Supply Screen V1

## Input

Frontend screen conclusion:
- `MyWorkView.isCompletableTodo(item)` currently depends on
  `item.source === 'mail.activity'`
- `ActionView` batch delete behavior depends on model-name special-cases
- `useActionViewNavigationRuntime` clears `scene/scene_key` for
  `project.project`

The frontend conclusion is already fixed:
- these are not display issues
- frontend must not remove them by further guessing

## Backend Sub-Layer Decision

### 1. MyWork row completion capability

Question:
- should frontend know a todo is completable from `source=model`?

Decision:
- `business-fact layer` for row-level action capability
- `scene-orchestration layer` only if a scene-ready action envelope is needed

Reason:
- whether a row supports completion is a workflow fact of that row
- it is not a page-layout concern
- frontend needs an explicit fact such as:
  - `can_complete`
  - or an `available_actions` entry for completion

Minimum backend supply:
- row-level completion capability fact
- optional action execution descriptor if completion is exposed through a scene

Recommended ownership split:
- business-fact emits whether completion is allowed
- scene-orchestration packages it into scene-ready row actions if needed

### 2. ActionView batch delete and delete-only mode

Question:
- should frontend know batch delete policy from model names?

Decision:
- `scene-orchestration layer`

Reason:
- this is not a base record truth like current state or owner
- this is a page/action-surface policy about what the current action allows
- frontend needs a scene-ready action policy such as:
  - `batch_delete_allowed`
  - `batch_delete_only_mode`
  - explicit available batch actions

Minimum backend supply:
- list-surface batch action policy
- destructive-action guard policy
- explicit batch action availability list

### 3. Record-open carry-query policy for project records

Question:
- should frontend know when to strip `scene` / `scene_key` from record-open navigation?

Decision:
- `scene-orchestration layer`

Reason:
- this is navigation policy for a scene/action transition
- it depends on orchestration rules, not intrinsic business truth of
  `project.project`
- frontend needs an explicit carry policy such as:
  - `clear_scene_context_on_record_open`
  - `record_open_carry_query_keys`
  - or a `carry_query_policy`

Minimum backend supply:
- explicit record-open carry-query policy in action or scene-ready contract

## Consolidated Supply Plan

### Business-fact supply needed

1. MyWork row completion capability fact

### Scene-orchestration supply needed

1. MyWork completion action envelope if completion is scene-driven
2. ActionView batch action policy surface
3. ActionView record-open carry-query policy

## Recommended Batch Order

1. backend screen / contract design for MyWork row completion capability
2. backend screen / contract design for ActionView batch action policy
3. backend screen / contract design for record-open carry-query policy
4. frontend cleanup batches only after each semantic supply lands

## Stop Rule

Do not delete the remaining frontend behavior special-cases until the matching
backend semantic supply is implemented and verified.
