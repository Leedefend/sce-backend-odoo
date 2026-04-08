# ITER-2026-04-08-1374 Report

## Batch
- Batch: `1/1`

## Summary of change
- 修复 `verify.scene.legacy_endpoint.guard` allowlist 漏配。
- 变更文件：`scripts/verify/legacy_scene_endpoint_guard.py`
  - 新增允许项：
    - `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
    - `scripts/verify/scene_legacy_auth_runtime_probe.py`
    - `scripts/verify/native_business_fact_runtime_snapshot.py`
    - `scripts/verify/native_business_fact_static_usability_verify.py`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1374.yaml` ✅
- `make verify.scene.legacy_endpoint.guard` ✅
- `CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已消除 legacy endpoint guard 阻断；
  - 新阻断为既有 `verify.scene.legacy_docs.guard`，报大量文档缺少 deprecated/successor/migration/sunset 标记。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - preflight 仍未全绿，但失败点已从 endpoint allowlist 前移到 docs 治理门禁；
  - 属于下一独立治理批次范围，不在本任务 allowlist 内。

## Rollback suggestion
- `git restore scripts/verify/legacy_scene_endpoint_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1374.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1374.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1374.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1375` 文档治理批次，允许修改 `docs/audit/native/**` 与 `docs/ops/business_admin_config_center_intent_endpoint_screen_v1.md`，补齐 legacy docs guard 要求字段。
