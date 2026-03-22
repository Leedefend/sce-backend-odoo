# Product v0.1 Odoo Native Alignment

## Objective
- Freeze the native Odoo dependency boundary for the first pilot.

## Native Models In Use
- `project.project`
  - execution owner record
  - chatter carrier via `message_post`
- `project.task`
  - execution task carrier
  - business state source via `sc_state`
- `mail.activity`
  - execution follow-up carrier
  - constrained to summary `执行推进跟进`

## Boundary Rules
- `project.task.sc_state` is the only business state source for execution logic.
- `project.task.kanban_state` remains compatibility-only for native Odoo visual alignment.
- `project.project.sc_execution_state` is the scene-facing execution state, not a replacement for task truth.
- chatter and activity are supporting evidence channels; they do not override task state.

## Allowed Native Usage
- Read and write `project.project.sc_execution_state`
- Transition `project.task.sc_state` through task methods
- Post chatter notes on `project.project`
- Reconcile one follow-up `mail.activity`

## Forbidden Native Usage
- Use `kanban_state` as execution truth
- Use multiple open tasks with implicit selection in v0.1
- Create multiple execution follow-up activities for the same project state
- Bypass task transition methods with direct `sc_state` writes

## Compatibility Note
- v0.1 stays intentionally narrow to reduce pilot complexity.
- Any move to multi-task pilot execution requires a new semantic phase.
