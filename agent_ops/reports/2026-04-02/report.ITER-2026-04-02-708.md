# ITER-2026-04-02-708

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance atomic transition closure
- priority_lane: P0_execution_atomicity
- risk: low

## Summary of Change

- introduced `_ExecutionAdvanceAtomicRollback` as internal blocked-reason signal
- introduced `_apply_transition_atomically(...)`:
  - wraps task transition + project write + post alignment check in
    `self.env.cr.savepoint()`
  - any blocked reason raises rollback signal and reverts savepoint section
- replaced non-atomic sequential path in `handle(...)` with atomic helper call
- blocked return remains compatible and now always carries `suggested_action_payload`
  in this atomic section

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-708.yaml`: PASS

## Next Iteration Suggestion

- verify acceptance chain and then move to P1 explicit task targeting
