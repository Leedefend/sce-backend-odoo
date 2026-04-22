# Project Management Dashboard Loading Screen CI

## Goal

Classify the real `/s/project.management` loading stall after scene-shell
convergence and decide whether the next repair belongs to backend semantic
supply or frontend load completion.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-PROJECT-MANAGEMENT-DASHBOARD-LOADING-SCREEN-CI.yaml`
   - PASS
2. Direct runtime intent diagnosis against `http://127.0.0.1:5174/api/v1/intent?db=sc_demo`
   - PASS
   - `login` succeeded with `wutao / demo`
   - `project.dashboard.enter` for project `925` returned `ok=true`
   - runtime fetch hints for `progress`, `risks`, and `next_actions` all
     returned `state=ready`, `degraded=false`, and completed within
     `149-212ms`
3. Direct `system.init` scene-ready diagnosis against `http://127.0.0.1:5174/api/v1/intent?db=sc_demo`
   - PASS
   - `scene_ready_contract_v1.scenes` contains a `project.management` row
   - but that row only provides minimal `page.route=/s/project.management`,
     toolbar actions, and search metadata
   - it does not provide dashboard `page_type/layout_mode` semantics for the
     generic frontend consumer
4. Existing browser artifact review:
   - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T063353Z/dashboard_timeout_snapshot.json`
   - the visible page had `视图切换 看板 列表 表单 ... 正在加载看板...`, proving the
     route had already fallen into `SceneView -> ActionView -> KanbanPage`
     rather than a dashboard-specific consumer

## Conclusion

This screen batch is `PASS`.

The bounded loading issue is not caused by backend dashboard block hydration:
the backend `project.dashboard.enter` path and its three deferred blocks are
healthy. The real gap is semantic supply on the startup contract path:
`system.init.scene_ready_contract_v1` currently exposes only a minimal
`project.management` scene row and does not deliver the dashboard page semantics
that the frontend would need to select a dashboard surface generically.

The next batch must return to the backend scene-orchestration battlefield and
decide how `system.init.scene_ready_contract_v1` should supply dashboard page
semantics for `project.management`. Frontend-only continuation would become a
scene-specific patch and is therefore not the correct next step.
