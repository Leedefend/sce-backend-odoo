## Summary

- audited the live `project.project` list contract through `ui.contract(op=model, view_type=tree)` instead of relying on wrapped snapshots
- confirmed backend list facts are already sufficient for a fast-delivery list implementation
- established the next implementation target: keep the current `ListPage` table core and trim noisy list-surface actions/filters to match the live fact profile

## Live Facts

- live request target:
  - `model=project.project`
  - `view_type=tree`
  - `contract_mode=user`
- live `views.tree` already provides:
  - `columns = ["name", "user_id", "partner_id", "stage_id", "lifecycle_state", "date_start", "date"]`
  - `row_actions`
  - `toolbar`
  - `search`
  - `page_size`
  - `row_classes`
- live `search` already provides:
  - `filters = 8`
  - `group_by = 67`
  - `saved_filters`
- live `list_profile` already provides:
  - stable columns
  - `column_labels`
  - `row_primary = name`
  - `row_secondary = stage_id`
  - `status_field = lifecycle_state`
- live action facts are noisier than the table facts:
  - `toolbar.header = ["Create a Project", "Projects", "Projects", "Projects"]`
  - `buttons = ["Create project", "Set a Rating Email Template on Stages", "项目设置", "进入下一阶段", "查看任务", "查看合同", "查看成本", "查看财务"]`

## Conclusion

- backend fact metadata is already strong enough for list-first delivery
- the fastest next batch is frontend-only:
  - preserve the current `ListPage` table/tooling core
  - shrink project-list pre-table surfaces in `ActionView`
  - map visible list actions more tightly to the live list fact profile

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-220.yaml`
- host-side live query against `http://127.0.0.1:8070/api/v1/intent?db=sc_demo` using:
  - `intent=login`
  - `intent=ui.contract`, `params={op:model, model:project.project, view_type:tree, contract_mode:user}`

## Risk

- low-risk audit batch
- no code-path changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-220.yaml`

## Next Suggestion

- implement a low-risk project-list shell batch that keeps `ListPage` intact but suppresses non-essential pre-table `ActionView` blocks and reduces header/button noise to the live list fact set
