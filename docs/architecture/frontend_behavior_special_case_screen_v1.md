# Frontend Behavior Special-Case Screen V1

## Scope

This screen covers only the remaining frontend behavior special-cases that were
already identified after copy-level cleanup:

1. `frontend/apps/web/src/views/MyWorkView.vue`
   - `isCompletableTodo(item)` uses `item.source === 'mail.activity'`
2. `frontend/apps/web/src/views/ActionView.vue`
   - `canBatchDelete` blocks delete when `model === 'project.project'`
   - `useDeleteOnlyBatchMode` gates delete-only batch mode by a hardcoded model set
3. `frontend/apps/web/src/app/action_runtime/useActionViewNavigationRuntime.ts`
   - row click removes `scene` and `scene_key` when `targetModel === 'project.project'`

## Classification

### 1. MyWork todo completion special-case

Current behavior:
- Frontend decides that only items from `mail.activity` are completable.

Ownership judgment:
- This is not a display concern.
- This is action availability semantics for a specific work item type.
- That availability belongs to backend business-fact or scene-orchestration supply.

Classification:
- `requires_backend_semantic_supply`

Reason:
- Frontend cannot infer from `source` which rows support completion.
- The correct contract should expose a row-level capability such as
  `can_complete`, `available_actions`, or an equivalent scene-ready action fact.

Required backend supply before removal:
- explicit row-level completion capability
- optional completion action intent / action key

Frontend follow-up once supplied:
- replace `item.source === 'mail.activity'` with contract capability check

### 2. ActionView batch delete special-cases

Current behavior:
- Frontend blocks batch delete for `project.project`
- Frontend forces delete-only batch mode for:
  - `project.task`
  - `res.company`
  - `hr.department`
  - `res.users`

Ownership judgment:
- This is action-surface behavior.
- The page is deciding destructive-action affordance from model names.
- That is not generic rendering behavior and must not be inferred from model.

Classification:
- `requires_backend_semantic_supply`

Reason:
- Whether batch delete is allowed or delete-only is a policy/action-envelope fact.
- Backend contract should declare:
  - whether batch delete is allowed
  - which batch actions are available
  - whether delete must be isolated as the only batch action mode

Required backend supply before removal:
- explicit batch action capability surface
- explicit destructive-action guard policy

Frontend follow-up once supplied:
- remove model-name gating
- consume contract batch action policy directly

### 3. ActionView project row-click carry-query special-case

Current behavior:
- Frontend strips `scene` and `scene_key` from carry query when target model is
  `project.project`

Ownership judgment:
- This is navigation orchestration behavior, not generic UI rendering.
- The special-case exists because project record routing likely conflicts with
  scene-context carry rules.

Classification:
- `requires_backend_semantic_supply`

Reason:
- Frontend cannot know from model name when scene context must be cleared.
- The correct owner is an orchestration semantic such as:
  - `clear_scene_context_on_record_open`
  - explicit carry-query whitelist
  - explicit record-open routing policy

Required backend supply before removal:
- record-open carry policy in action/scene contract

Frontend follow-up once supplied:
- replace project-model special-case with policy-driven carry-query handling

## Decision Summary

All three remaining special-cases are behavior-level and should not be removed
by frontend guesswork alone.

Summary:
- `MyWorkView.isCompletableTodo`: backend semantic supply required
- `ActionView` batch delete gating: backend semantic supply required
- `useActionViewNavigationRuntime` project carry-query clearing: backend
  semantic supply required

## Next Batch Recommendation

Open a backend-oriented screen / supply task line for:

1. work-item completion capability semantics for MyWork rows
2. batch action capability policy for ActionView list surfaces
3. record-open carry-query policy for ActionView navigation

Until those semantics are supplied, frontend should not attempt further direct
removal of these behavior special-cases.
