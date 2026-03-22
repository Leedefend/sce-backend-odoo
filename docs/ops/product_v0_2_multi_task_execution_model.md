# Product v0.2 Multi-Task Execution Model

## Purpose
- Define the target multi-task execution model for v0.2 expansion.
- This document is design-only for Phase 16-A.
- No runtime behavior is changed in v0.1.

## Why v0.2 Needs This
- v0.1 is intentionally frozen to `single_open_task_only`.
- Pilot evidence shows that the current rule is stable and understandable, but it blocks any scenario where more than one task must advance in parallel.
- v0.2 therefore needs a model that expands execution semantics without removing `project.task.sc_state` as the business truth.

## Design Principles
- Keep `project.task.sc_state` as the only task-level business truth.
- Do not invent a second task system.
- Keep project-level execution state as an aggregate projection, not a manually maintained truth source.
- Preserve explainability for non-developer operators.
- Make ambiguity explicit rather than hiding it behind heuristics.

## Proposed Semantic Layers
- Task truth:
  - `project.task.sc_state`
- Execution aggregate:
  - `project.project.sc_execution_state`
- Execution focus:
  - one selected task or task set that the product is currently explaining to the operator
- Execution policy:
  - a declared scope model that tells the UI and guards how multiple open tasks should be interpreted

## Proposed v0.2 Scope Modes
- `single_open_task_only`
  - keep current v0.1 behavior for compat and fallback
- `multi_open_task_explicit_queue`
  - more than one open task allowed
  - product surfaces one operator focus task at a time
  - queue order must be explicit, not inferred from view order
- `multi_open_task_parallel`
  - more than one task may be in progress
  - project aggregate must explain whether the project is blocked, active, or mixed
  - not recommended for v0.2 first cut

## Recommended v0.2 Direction
- Choose `multi_open_task_explicit_queue` as the first multi-task model.
- Reason:
  - it preserves operator clarity
  - it keeps guards auditable
  - it extends from v0.1 without forcing full parallel-state semantics

## Aggregate State Proposal
- `ready`
  - at least one queued task is ready and no task is currently in progress
- `in_progress`
  - exactly one focus task is in progress under the explicit queue model
- `blocked`
  - queue cannot move because the focus task or required prerequisite is blocked
- `done`
  - all in-scope queued tasks are done
- `mixed`
  - temporary aggregate state used only when queue integrity is broken or scope is not fully explainable
  - should be treated as a guarded exception, not a normal steady state

## Required New Concepts
- `execution_scope_mode`
  - identifies whether the project is still under v0.1 single-task mode or a future v0.2 queue mode
- `focus_task_id`
  - the task currently being explained as the next execution target
- `queue_order`
  - stable ordering key for open tasks
- `queue_blocker_reason`
  - explicit explanation for why the queue cannot continue

## Guard Requirements
- queue ordering must be deterministic
- only one focus task may exist at a time in the explicit queue model
- project aggregate state must be derived from task truth and queue truth
- blocked state must explain whether the blocker is:
  - task-level
  - prerequisite-level
  - queue-policy-level
- activity/chatter must be bound to the focus task transition, not to every open task indiscriminately

## Out Of Scope In Phase 16-A
- no model fields added
- no handler changes
- no UI changes
- no migration or compat path implementation

## Recommended Phase Order
1. define queue semantics and aggregate-state contract
2. define compat mode from `single_open_task_only`
3. define guard-first validation rules
4. only then implement runtime behavior
