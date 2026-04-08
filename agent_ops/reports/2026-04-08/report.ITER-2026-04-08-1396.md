# ITER-2026-04-08-1396 Report

## Batch
- Batch: `1/1`
- Mode: `scan`（low-cost staged governance）

## Summary of change
- 按 scan 边界仅收集候选证据，不下根因结论、不做代码修复。
- 候选证据（供 screen 阶段分类）：
  - C1: `frontend/apps/web/src/app/contractActionRuntime.ts:46` 读取权限时优先 `head.permissions`，其次 `permissions.effective.rights`，未对“全 false”做特殊折叠。
  - C2: `frontend/apps/web/src/app/contractRecordRuntime.ts:47` 存在 `effectiveCollapsed` 逻辑：当 `effective.rights` 四权全 false 时回退 `true`（默认放开），与 C1 口径不同。
  - C3: `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py:299` 后端明确下发 `permissions = get_permission_contract(filter_runtime=True)`（含 `effective.rights`）。
  - C4: `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py:377` 同时在 `head.permissions` 再下发一次 ACL 概览（`check_access_rights`），存在双源并存路径。
  - C5: `addons/smart_core/app_config_engine/models/app_permission_config.py:142` + `addons/smart_core/app_config_engine/models/app_permission_config.py:191` 运行态 `effective.rights` 由 `compile_effective_for_user` 计算，默认从全 false 聚合命中组权限。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1396.yaml` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批仅 scan，不做归因裁决；若直接跨到修复有误判风险。

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-08-1396.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1396.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1396.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 启动 `screen` 阶段：对 C1~C5 做“事实源/消费者口径/冲突级别”分类，明确哪个与业务事实一致、哪个属于消费偏差。
