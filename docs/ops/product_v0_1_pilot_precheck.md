# Product v0.1 Pilot Precheck

## Purpose
- Provide a first-pilot gate before users run `project.execution.advance`.
- Keep the gate auditable and aligned with the runtime contract.

## Runtime Surface
- Scene: `project.execution.enter`
- Runtime block: `project.execution.block.fetch(block_key=pilot_precheck)`
- Verify:
  - `make verify.product.project_execution_pilot_precheck_guard`

## Checks
- `root_task`
  - at least one project root task exists
- `single_open_task`
  - exactly one open task exists under the v0.1 controlled model
- `execution_task_consistency`
  - `project.project.sc_execution_state` matches `project.task.sc_state`
- `required_fields`
  - core pilot fields are complete
- `activity_rule`
  - `mail.activity` follow-up count matches the current execution state rule
- `lifecycle_state`
  - project lifecycle is not in a pilot-blocked state

## Result Model
- `overall_state=ready`
  - project can enter first-pilot execution flow
- `overall_state=blocked`
  - user must resolve the primary blocker before pilot execution

## Main Reason Codes
- `PILOT_ROOT_TASK_MISSING`
- `PILOT_SINGLE_OPEN_TASK_REQUIRED`
- `PILOT_REQUIRED_FIELDS_MISSING`
- `PILOT_LIFECYCLE_STATE_BLOCKED`
- `EXECUTION_PROJECT_TASK_STATE_DRIFT`
- `EXECUTION_PROJECT_ACTIVITY_DRIFT`

## Operational Rule
- v0.1 keeps `single_open_task_only`.
- Pilot precheck is informative in its own block and also drives `next_actions` blocked messaging.
