# ITER-2026-04-09-1458 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Architecture declaration
- Layer Target: `Backend permission-boundary recovery`
- Module: `release_orchestrator_sudo_write_path`
- Module Ownership: `smart_core backend contract stack`
- Kernel or Scenario: `scenario`
- Reason: 基于 1457 screen 结果，执行最小边界修复。

## Change summary
- `addons/smart_core/delivery/release_orchestrator.py`
  - `sc.release.action` / `sc.edition.release.snapshot` 访问从 `sudo()` 下沉为调用用户上下文。
- `addons/smart_core/delivery/release_operator_write_model_service.py`
  - `_approve_identity` 从 `sudo().browse(...)` 下沉为用户上下文 `browse(...)`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1458.yaml` ✅
- `DB_NAME=sc_demo make verify.release.operator_orchestration_guard` ❌
  - 失败信息：`Access Denied by ACLs ... model: sc.edition.release.snapshot`（uid: 27）
  - 错误归因：guard 运行用户缺少 `sc.edition.release.snapshot` 读取权限，原先由 `sudo` 隐式掩盖。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：触发“verify 失败立即停止”硬规则，本批进入停止态。

## Rollback suggestion
- `git restore addons/smart_core/delivery/release_orchestrator.py`
- `git restore addons/smart_core/delivery/release_operator_write_model_service.py`

## Next suggestion
- 开新批次先做权限基线 screen：
  - 分类 guard 执行用户是否应具备 `release snapshot` 读权限（业务事实层权限问题）
  - 或 guard 需切换到具备发布角色的测试身份（验证口径问题）
