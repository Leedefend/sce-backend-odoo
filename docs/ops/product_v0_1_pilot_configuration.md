# Product v0.1 Pilot Configuration

## Scope
- First pilot only
- Controlled single-project-manager operating mode
- Controlled single-open-task execution mode

## Role Scope
- Required operator:
  - project manager or assigned internal owner with `base.group_user`
- Recommended pilot actors:
  - `project.project.user_id` as primary operator
  - optional `manager_id` alignment with `user_id`

## Required Fields
- `project.project.name`
- `project.project.project_code`
- `project.project.date_start`
- `project.project.lifecycle_state`
- one responsible user:
  - `user_id` or `manager_id`

## Task Initialization
- Project bootstrap must create at least one root task.
- v0.1 pilot requires exactly one open task before execution.
- Business state authority is:
  - `project.task.sc_state`

## Execution Preconditions
- `pilot_precheck.overall_state=ready`
- `next_actions.summary.pilot_precheck_state=ready`
- no multi-open-task ambiguity
- no `project/task/activity` drift

## Activity And Chatter Rules
- `project.project` chatter records execution progress notes.
- `mail.activity(summary="执行推进跟进")` is the only v0.1 follow-up activity pattern for execution.
- expected activity count:
  - `in_progress`: `1`
  - `done`: `0`
  - `ready/blocked`: `0` or `1`, but never more than `1`

## Operator Guidance
- Do not batch-complete tasks through `推进`.
- Do not interpret kanban visuals as the business source of truth.
- If pilot precheck is blocked, resolve the first blocker before retrying execution.
