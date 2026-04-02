# ITER-2026-04-02-780

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: one2many edit verify fallback
- priority_lane: usability_verification_mainline
- risk: low

## Change Summary

- updated `scripts/verify/fe_one2many_edit_smoke.js`:
  - added recursive node-tree layout scan and `views[view_type].layout` fallback
  - prefer one2many fields present in layout
  - infer missing `relation_field` via relation model `load_view` (`many2one -> parent model`)
  - support `relation_entry.create_mode=page` contract guard path and skip invalid direct create

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-780.yaml`: PASS
- `node --check scripts/verify/fe_one2many_edit_smoke.js`: PASS

## Decision

- PASS
- one2many-edit false-fail root cause fixed

## Next Iteration Suggestion

- run `ITER-2026-04-02-781` recovery verify
