## Summary

- audited the live `project.project` form contract through `ui.contract(op=model, view_type=form)` to re-baseline detail-page work on real backend facts
- confirmed the backend form metadata is already sufficient for a fact-first detail implementation batch
- established that the next detail batch should focus on frontend structure and consumption, not backend completeness

## Live Facts

- live request target:
  - `model=project.project`
  - `view_type=form`
  - `contract_mode=user`
- live form contract already provides:
  - `views.form.layout`
  - `views.form.statusbar.field = lifecycle_state`
  - `views.form.field_modifiers = 70`
  - `buttons = ["提交立项", "执行结构"]`
  - `field_groups = 2`
  - `visible_fields = 25`
- live top-level form payload already carries:
  - `layout`
  - `parser_contract`
  - `view_semantics`
  - `surface_mapping`
  - `form_profile`
  - `field_semantics`

## Conclusion

- backend detail facts are already strong enough for the next delivery batch
- the next detail implementation should stay frontend-only and target:
  - stronger section/page skeleton from `views.form.layout`
  - cleaner page identity and status expression
  - tighter projection of `field_modifiers`, `field_groups`, and visible fields
  - preserving the cleaned live button facts without reintroducing extra action surfaces

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-222.yaml`
- host-side live query against `http://127.0.0.1:8070/api/v1/intent?db=sc_demo` using:
  - `intent=login`
  - `intent=ui.contract`, `params={op:model, model:project.project, view_type:form, contract_mode:user}`

## Risk

- low-risk audit batch
- no code-path changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-222.yaml`

## Next Suggestion

- implement a low-risk detail-page structure batch that keeps `ContractFormPage` generic but lets the live form layout, statusbar, field groups, and modifier facts dominate the rendered page
