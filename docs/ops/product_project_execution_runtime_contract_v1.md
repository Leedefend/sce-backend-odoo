# Product Execution Runtime Contract v1

## Scope
- Scene entry intent: `project.execution.enter`
- Runtime block intent: `project.execution.block.fetch`
- Product flow: `project.initiation.enter -> project.dashboard.enter -> project.plan_bootstrap.enter -> project.execution.enter`

## Entry Contract
`project.execution.enter` returns only:
- `project_id`
- `title`
- `summary`
- `blocks`
- `suggested_action`
- `runtime_fetch_hints`

## Entry Summary Keys
- `project_code`
- `manager_name`
- `stage_name`
- `date_start`
- `date_end`

## Runtime Blocks
Current supported runtime blocks:
- `execution_tasks`

Public `project.execution.block.fetch` response keeps:
- `project_id`
- `block_key`
- `block`
- `degraded`

## Runtime Block Shape
`execution_tasks` keeps block-local shape and does not upgrade block failure to page failure.

Recommended data fields:
- `items`
- `summary`

## Flow Guarantee
- plan `next_actions` must expose `project.execution.enter`
- `params.project_id` must stay equal to the original initiation record id
- execution entry must expose runtime fetch hint for `execution_tasks`
