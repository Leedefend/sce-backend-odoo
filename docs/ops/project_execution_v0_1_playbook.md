# Project Execution v0.1 Playbook

## Audience
- Project manager
- Delivery lead
- Non-developer operator

## Preconditions
- User can open the project management dashboard.
- Project already exists.
- Project has exactly one open execution task for v0.1 controlled flow.

## Standard Path
1. Open the target project.
2. Check the dashboard or execution page:
   - `计划任务` / `执行任务` should show one active task source from `project.task`.
   - `执行下一步` should be available, not blocked.
3. Click `进入` from planning into execution.
4. Click `推进` once:
   - expected project state: `执行就绪 -> 执行中`
   - expected task state: `draft/ready -> in_progress`
   - expected follow-up: one `执行推进跟进` activity
5. Complete the real task work in Odoo.
6. Click `推进` again:
   - expected project state: `执行中 -> 执行完成`
   - expected task state: `in_progress -> done`
   - expected follow-up activity count: `0`

## When The Action Is Blocked
- `EXECUTION_TASK_MISSING`
  - create or prepare the project task first
- `EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED`
  - reduce to one open execution task before using `推进`
- `EXECUTION_PROJECT_TASK_STATE_DRIFT`
  - project state and task state are inconsistent; ask the delivery owner to reconcile task/project status
- `EXECUTION_PROJECT_ACTIVITY_DRIFT`
  - activity synchronization failed; retry after refresh, then escalate if it remains

## Operator Rules
- Do not use `推进` to batch-complete multiple tasks.
- Do not treat kanban color/status as the business truth.
- Use `sc_state`-driven execution blocks as the authoritative product signal.
- If more than one task must run in parallel, v0.1 playbook does not cover that scenario.

## Verification Checklist
- `执行任务` summary shows `source_model=project.task`
- next-actions summary shows `execution_scope=single_open_task_only`
- task state changes after each successful `推进`
- follow-up activity appears in progress and disappears on completion
