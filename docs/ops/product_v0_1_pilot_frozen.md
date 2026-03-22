# Product v0.1 Pilot Frozen

## Freeze Decision
- v0.1 is frozen for first-pilot execution under a controlled operating model.
- This phase does not expand architecture or product scope.

## Frozen Capability Boundary
- Supported operator path:
  - initiation -> dashboard -> plan -> execution -> advance
- Supported execution state machine:
  - `ready -> in_progress -> done`
  - `blocked -> ready`
- Supported business truth:
  - `project.task.sc_state`
- Supported runtime guard:
  - `pilot_precheck`
- Supported execution scope:
  - `single_open_task_only`

## Frozen Rules
- Exactly one open task is allowed before execution advance.
- `project.project.sc_execution_state` must stay aligned with task truth.
- `mail.activity(summary="执行推进跟进")` remains the only pilot follow-up activity pattern.
- Chatter stays on native `project.project` / `project.task`.

## Explicit Limitations
- No multi-open-task execution.
- No parallel execution orchestration.
- No attempt to productize native kanban colors as business truth.
- No custom task subsystem beyond native `project.task`.
- No additional role-specific flows beyond the controlled pilot operator path.

## Allowed Fix Policy
- Only blocking issues and high-priority understanding issues may be fixed inside v0.1 frozen pilot.
- Structural expansion requires a new semantic phase.

## Exit Condition
- Move beyond this freeze only after pilot feedback proves that:
  - current scope is insufficient
  - the missing capability cannot be solved by copy, guard, or operator guidance alone
