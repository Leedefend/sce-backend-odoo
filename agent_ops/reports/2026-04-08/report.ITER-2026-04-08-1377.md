# ITER-2026-04-08-1377 Report

## Batch
- Batch: `1/1`

## Summary of change
- 修复 `ui.contract` handler 缺失显式治理调用导致的 coverage 失败。
- 变更文件：`addons/smart_core/handlers/ui_contract.py`
  - 引入 `apply_contract_governance`
  - 在 `shape_handler_delivery_data` 后显式执行治理收口

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1377.yaml` ✅
- `make verify.contract.governance.coverage` ✅
- `CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已消除 governance coverage 阻断；
  - 新阻断前移到 `verify.docs.links`（`missing_count=185`）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：preflight 进入 docs 链接完整性门禁，属于现存文档债务，不在本批次单点治理目标内。

## Rollback suggestion
- `git restore addons/smart_core/handlers/ui_contract.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1377.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1377.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1377.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1378`：为 `verify.contract.preflight` 增加受控开关，允许在 `BASELINE_FREEZE_ENFORCE=0` 快速链路下跳过 `verify.docs.all`，并保留默认严格策略。
