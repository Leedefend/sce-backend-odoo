# Product Execution State Machine v1

## Scope
- Intent: `project.execution.advance`
- Runtime block: `project.execution.block.fetch(block_key=next_actions)`
- Persistence field: `project.project.sc_execution_state`
- Advance boundary: `docs/ops/product_project_execution_advance_scope_v1.md`

## Frozen State Set
- `ready`
- `in_progress`
- `blocked`
- `done`

## Allowed Transitions
- `ready -> in_progress`
- `in_progress -> done`
- `blocked -> ready`

All other directions are illegal and must return:
- `result=blocked`
- stable `reason_code`
- `from_state`
- `to_state` equal to current persisted state

## Advance Result Contract
`project.execution.advance` returns only:
- `result`
- `project_id`
- `from_state`
- `to_state`
- `reason_code`
- `suggested_action`

`result` is frozen to:
- `success`
- `blocked`

## Next Actions Binding
`execution_next_actions` is generated from current execution state:
- `ready`: expose legal advance action to `in_progress`
- `in_progress`: expose legal advance action to `done`
- `blocked`: expose legal recovery action back to `ready`
- `done`: expose blocked action with `EXECUTION_ALREADY_DONE`

Each action keeps:
- `intent`
- `state`
- `reason_code`
- `params.project_id`
- `params.target_state`
