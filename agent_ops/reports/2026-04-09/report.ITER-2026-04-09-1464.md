# ITER-2026-04-09-1464 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Change summary (runtime baseline)
- 在 `sc_demo` 运行态将 `base.user_admin` 加入 `smart_core.group_smart_core_admin`（已 commit）。
- 校验结果：`release_admin_users = ['admin']`，`demo_pm` 存在且未授予发布权限。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1464.yaml` ✅
- `DB_NAME=sc_demo make verify.release.operator_orchestration_guard` ❌
  - 失败：`uid=27` 读取 `sc.edition.release.snapshot` 被 ACL 拒绝。
  - 原因：guard 仍以 `demo_pm` 执行 promote 流程；而你已要求发布权限仅平台 admin，故该用户理应被拒绝。

## Risk analysis
- 结论：`FAIL`
- 风险级别：low
- 说明：当前失败是验证脚本口径与最新权限策略不一致，不是 ACL 事实缺失。

## Rollback suggestion
- 运行态回滚（如需）：从 `base.user_admin` 移除 `smart_core.group_smart_core_admin`。

## Next suggestion
- 开新实现批仅修复 guard 口径：
  - `release_operator_orchestration_guard.sh` 不再使用 `demo_pm` 走发布流程，改用平台发布管理员身份执行。
