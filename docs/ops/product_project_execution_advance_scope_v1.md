# Product Execution Advance Scope v1

## Objective
- Freeze `project.execution.advance` to a stable, low-complexity operating scope for v0.1.
- Keep task lifecycle semantics on `project.task.sc_state` as the only business state source.

## In Scope
- Intent: `project.execution.advance`
- Project state field: `project.project.sc_execution_state`
- Task state field: `project.task.sc_state`
- Follow-up activity: `mail.activity(summary="执行推进跟进")`

## Frozen Behavior
- One advance call changes at most one task.
- One advance call changes at most one project execution state.
- Follow-up activity is reconciled after each successful state change.
- Runtime next-actions summary exposes consistency evidence only; it does not expand the action contract.

## Allowed Behavior
- `ready -> in_progress`
  - prepares `draft` task to `ready` when needed
  - starts the same task to `in_progress`
- `in_progress -> done`
  - completes the single in-progress task
- `blocked -> ready`
  - recovers the single actionable task back to executable readiness

## Forbidden Behavior
- Bulk-advance multiple tasks in one call
- Choose between multiple open tasks implicitly
- Mark project execution as `done` while open tasks still exist
- Depend on `kanban_state` as business truth
- Expand public intent shape beyond:
  - `result`
  - `project_id`
  - `from_state`
  - `to_state`
  - `reason_code`
  - `suggested_action`

## Guard Reasons
- `EXECUTION_TASK_MISSING`
- `EXECUTION_TASK_NOT_IN_PROGRESS`
- `EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED`
- `EXECUTION_PROJECT_TASK_STATE_DRIFT`
- `EXECUTION_PROJECT_ACTIVITY_DRIFT`

## Consistency Rules
- Project `ready` must not have in-progress tasks.
- Project `in_progress` must have exactly one in-progress task.
- Project `done` must have zero open tasks.
- Follow-up activity count must be:
  - `1` for `ready/in_progress/blocked` with open tasks
  - `0` for `done`

## Compatibility Note
- `kanban_state` may still be synchronized as a derived compatibility field for native Odoo views.
- All product logic and verification must read `sc_state`, not `kanban_state`.
