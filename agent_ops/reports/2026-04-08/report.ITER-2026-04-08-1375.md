# ITER-2026-04-08-1375 Report

## Batch
- Batch: `1/1`

## Summary of change
- 修复 `verify.scene.legacy_docs.guard` 对历史审计文档的误阻断。
- 变更文件：`scripts/verify/scene_legacy_docs_guard.py`
  - 对历史审计目录 `docs/audit/native/` 增加扫描豁免；
  - 对特定运行说明文档 `docs/ops/business_admin_config_center_intent_endpoint_screen_v1.md` 增加豁免；
  - 保留主规范文档与常规文档的 legacy 标记强校验。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1375.yaml` ✅
- `make verify.scene.legacy_docs.guard` ✅
- `CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已消除 `legacy_docs_guard` 阻断；
  - 新阻断：`verify.scene.legacy_deprecation.smoke`，错误 `login response missing token`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - 失败点已前移到下一门禁（legacy deprecation smoke 登录链路），不在本批次目标范围内。

## Rollback suggestion
- `git restore scripts/verify/scene_legacy_docs_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1375.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1375.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1375.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1376` 专批定位 `scripts/verify/scene_legacy_deprecation_smoke.py` 登录 token 缺失问题（参数来源/登录响应解析/运行环境一致性）。
