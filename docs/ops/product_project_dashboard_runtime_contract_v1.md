# Product Dashboard Runtime Contract v1

## Scope
- Scene entry intent: `project.dashboard.enter`
- Runtime block intent: `project.dashboard.block.fetch`
- Product flow: `project.initiation.enter -> project.dashboard.enter`
- Compat alias: `project.dashboard.open` (deprecated, thin wrapper only, target removal `Phase 12-G`)

## Entry Contract
`project.dashboard.enter` returns only:
- `project_id`
- `title`
- `summary`
- `blocks`
- `suggested_action`
- `runtime_fetch_hints`

Constraints:
- `summary` is minimal project context only
- `blocks` declares runtime block shells only
- heavy collections must not appear in entry payload:
  - tasks
  - risks collection rows
  - payments
  - costs

## Runtime Blocks
Supported `block_key` values:
- `progress`
- `risks`
- `next_actions`

Runtime fetch shape:
- `project_id`
- `block_key`
- `block`
- `degraded`

Block behavior:
- each block loads independently
- block failure must degrade to block-level error, not page-level error
- `project.dashboard.block.fetch` keeps `ok=true` for supported block keys and carries block state in `block.state`
- public block response shape is frozen to:
  - `project_id`
  - `block_key`
  - `block`
  - `degraded`

## Next Actions
- `next_actions` block is the reserved bridge from dashboard to the next scene
- current reserved direction:
  - `project.plan_bootstrap.enter`
- current status:
  - planned only
  - no full scene implementation in Phase 12-E

## Initiation Flow
- `project.initiation.enter` success path must return:
  - `suggested_action_payload.intent = project.dashboard.enter`
  - `suggested_action_payload.params.project_id = record.id`
- `project_id` must remain continuous across:
  - initiation record
  - suggested action params
  - dashboard entry
  - runtime block fetch params

## Verify
- `make verify.product.project_dashboard_flow`
- `make verify.product.project_dashboard_entry_contract_guard`
- `make verify.product.project_dashboard_block_contract_guard`
- `make verify.product.project_dashboard_baseline`
- `make verify.phase12b.baseline`
