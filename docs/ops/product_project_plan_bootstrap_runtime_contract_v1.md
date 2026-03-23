# Product Plan Bootstrap Runtime Contract v1

## Scope
- Scene entry intent: `project.plan_bootstrap.enter`
- Runtime block intent: `project.plan_bootstrap.block.fetch`
- Product flow: `project.initiation.enter -> project.dashboard.enter -> project.plan_bootstrap.enter`

## Entry Contract
`project.plan_bootstrap.enter` returns only:
- `project_id`
- `scene_key`
- `scene_label`
- `state_fallback_text`
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
- `plan_summary_detail`
- `plan_tasks`
- `next_actions`

Public `project.plan_bootstrap.block.fetch` response keeps:
- `project_id`
- `block_key`
- `block`
- `degraded`

## Runtime Block Shape
`plan_summary_detail` keeps block-local shape and does not upgrade block failure to page failure.

Recommended data fields:
- `task_total`
- `task_open`
- `task_done`
- `task_overdue`
- `milestone_total`
- `milestone_done`
- `next_deadline`
- `planning_health`
- `summary`

Recommended `plan_tasks` fields:
- `items`
- `summary`

Recommended `next_actions` fields:
- `actions`
- `summary`

## Flow Guarantee
- dashboard `next_actions` must expose `project.plan_bootstrap.enter`
- `params.project_id` must stay equal to the original initiation record id
- plan entry must expose runtime fetch hints for `plan_summary_detail/plan_tasks/next_actions`
- plan `next_actions` must expose `project.execution.enter`
