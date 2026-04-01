# ITER-2026-04-01-607

- status: PASS
- mode: implement
- layer_target: Frontend Layer
- module: project list row-action continuity hint
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- made list row hint model-aware in `ListPage.vue`
- for `project.project`, hint now reads: `点击项目行可进入项目管理`
- other models keep previous hint: `点击列表行可查看详情`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-607.yaml`: PASS

## Risk Analysis

- frontend-only copy-level change
- no navigation behavior, backend contract, or permission changes

## Rollback Suggestion

- restore `frontend/apps/web/src/pages/ListPage.vue`

## Next Iteration Suggestion

- run strict typecheck and project-management acceptance in `ITER-2026-04-01-608`
