# ITER-2026-04-10-1723 Report

## Batch
- Batch: `P1-Batch46`
- Mode: `implement`
- Stage: `action view list-kanban switch convergence`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `frontend/apps/web ActionView`
- Module Ownership: `smart_core + frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 修复列表/看板切换时 `preferredViewMode` 与路由 `view_mode` 不一致导致的切换失效。

## Change summary
- 更新 `frontend/apps/web/src/app/action_runtime/useActionViewModeRuntime.ts`
  - 视图切换前增加 `beforeSwitchViewMode` 钩子。
- 更新 `frontend/apps/web/src/views/ActionView.vue`
  - 在切换视图前同步 `route.query.view_mode`，再触发加载，避免预检被旧 query 覆盖。
- 更新 `frontend/apps/web/src/app/pageContract.ts`
  - 修复 `sectionTagIs`：当 section key 未配置时按 fallback 处理，避免 `view_switch` 被误隐藏。
- 更新 `frontend/apps/web/src/views/ActionView.vue`
  - 对仅 `kanban` 声明场景补齐 `tree` 备选模式，确保列表/看板切换入口可见。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1723.yaml` ✅
- `python3 scripts/verify/frontend_api_smoke.py` ❌
  - 失败原因：`urlopen error timed out`（本地服务连接超时，环境不可用）
- 环境恢复尝试：
  - `make frontend.restart` ✅
  - `make restart` ✅
  - 重跑 `python3 scripts/verify/frontend_api_smoke.py` 仍 ❌（同样 timeout）
- 本轮新增修复后再次验证：
  - `make frontend.restart` ✅
  - `python3 scripts/verify/frontend_api_smoke.py` 仍 ❌（同样 timeout）

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：代码改动已完成，但验收烟测因环境未连通失败，按治理规则本批必须停止并先恢复环境验证。

## Rollback suggestion
- `git restore frontend/apps/web/src/app/action_runtime/useActionViewModeRuntime.ts`
- `git restore frontend/apps/web/src/views/ActionView.vue`

## Next suggestion
- 启动/确认前后端服务连通后，重跑：
  - `python3 scripts/verify/frontend_api_smoke.py`
- 通过后再进入下一轮表单视图收敛。
