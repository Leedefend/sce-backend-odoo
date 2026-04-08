# ITER-2026-04-08-1376 Report

## Batch
- Batch: `1/1`

## Summary of change
- 修复 `scene_legacy_deprecation_smoke` 的登录 token 解析。
- 变更文件：`scripts/verify/scene_legacy_deprecation_smoke.py`
  - 兼容新登录响应：优先读取 `data.session.token`，回退兼容 `data.token`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1376.yaml` ✅
- `make verify.scene.legacy_deprecation.smoke DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已消除 `scene_legacy_deprecation_smoke` 阻断；
  - 新阻断前移到 `verify.contract.governance.coverage`（聚合链既有门禁）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - 本批目标修复已生效并通过单项验收；
  - preflight 仍未全绿，需下一专批处理 governance coverage 失败。

## Rollback suggestion
- `git restore scripts/verify/scene_legacy_deprecation_smoke.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1376.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1376.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1376.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1377` 专批定位 `scripts/verify/contract_governance_coverage.py` 的失败项并修复，恢复 preflight 连续通过能力。
