# ITER-2026-04-01-604

- status: PASS
- mode: implement
- layer_target: Frontend Layer
- module: project empty-state create-entry guidance
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- extended `resolveEmptyCopy` to accept optional model context
- for `project.project` list empty state, show explicit create-entry guidance:
  - title: `暂无项目`
  - message: `点击右上角“创建项目”开始项目管理闭环。`
- wired `ListPage` empty copy call to pass `props.model`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-604.yaml`: PASS

## Risk Analysis

- frontend-only copy-layer adjustment
- no backend contract, ACL, or data-semantics changes

## Rollback Suggestion

- restore `frontend/apps/web/src/composables/useStatus.ts`
- restore `frontend/apps/web/src/pages/ListPage.vue`

## Next Iteration Suggestion

- run strict typecheck and project-management acceptance in `ITER-2026-04-01-605`
