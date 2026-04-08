# ITER-2026-04-08-1398 Report

## Batch
- Batch: `1/1`
- Mode: `verify`

## Summary of change
- 修复文件：`frontend/apps/web/src/app/contractRecordRuntime.ts`
- 修复内容：
  - 删除 `effectiveCollapsed`（`effective.rights` 四权全 false 时强制回退 true）逻辑；
  - `resolveRights` 改为与 action runtime 同口径：
    1) 优先 `head.permissions[key]`；
    2) 其次 `permissions.effective.rights[key]`；
    3) 都缺失才回退 `true`。
- 目的：避免“后端明确下发 false，却在记录态被放开为 true”的只读/可编辑误判。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1398.yaml` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅调整前端权限消费回退策略，不改后端权限事实生成与发布语义。

## Rollback suggestion
- `git restore frontend/apps/web/src/app/contractRecordRuntime.ts`
- `git restore agent_ops/tasks/ITER-2026-04-08-1398.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1398.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1398.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 在 8069 开发环境做一次 UI 回归：
  - 角色入口配置页（新建/编辑）
  - 系统参数配置页
  - 对比同一账号在 list/form 的权限状态是否一致。
