# ITER-2026-04-01-527

- status: PASS
- layer_target: Agent Governance
- module: low-cost role-parallel policy
- risk: low

## Summary of Change

- extended low-cost policy to allow bounded role-parallel execution for explicitly declared low-risk tasks
- constrained role-parallel execution to single-stage batches, disjoint writes, and new session per role
- updated the low-cost task template with a `role_parallel` contract block
- updated `split_task.py` so generated stage tasks carry `role_parallel` defaults and per-stage allowed roles

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-527.yaml`: PASS
- `python3 agent_ops/scripts/split_task.py agent_ops/tasks/ITER-2026-04-01-522.yaml`: PASS

## Risk Analysis

- low risk
- governance-only change
- no product paths changed for this batch
- residual risk: low-risk tasks must still declare `role_parallel.enabled: true` before parallel execution is used

## Rollback Suggestion

- `git restore AGENTS.md`
- `git restore docs/ops/codex_low_cost_iteration_policy_v1.md`
- `git restore agent_ops/templates/task_low_cost.yaml`
- `git restore agent_ops/scripts/split_task.py`

## Next Iteration Suggestion

- continue the active product-usability line while allowing future low-risk tasks to opt into bounded role-parallel execution through the task contract
