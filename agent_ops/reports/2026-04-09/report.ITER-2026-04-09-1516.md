# ITER-2026-04-09-1516 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Sidebar residual routing cleanup`

## Architecture declaration
- Layer Target: `Frontend consumer layer`
- Module: `Sidebar AppShell navigation dispatcher`
- Module Ownership: `frontend web shell`
- Kernel or Scenario: `scenario`
- Reason: 清理 `/m/:id` 前端回退口径，统一消费解释层 `route`。

## Change summary
- 更新 `frontend/apps/web/src/layouts/AppShell.vue`
  - 面包屑跳转改为消费节点 `route`，目录/不可用节点不再生成跳转。
  - 新增 `findMenuNodeById`，角色快捷菜单点击改为定位解释层节点后走统一 `navigateByExplainedMenuNode`。
  - 删除 `openRoleMenu` 中 `/m/:id` 直接跳转回退。
- 更新 `scripts/verify/sidebar_navigation_consumer_verify.py`
  - 增加禁止项：前端不得出现 `` `/m/${` `` 菜单回退路由拼接。
- 更新 `docs/frontend/sidebar_navigation_consumer_v1.md`
  - 明确快捷入口与面包屑同样只消费解释层 `route`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1516.yaml` ✅
- `python3 scripts/verify/sidebar_navigation_consumer_verify.py` ✅
- `python3 scripts/verify/sidebar_active_chain_verify.py` ✅
- `python3 scripts/verify/sidebar_directory_rule_verify.py` ✅
- `python3 scripts/verify/sidebar_unavailable_guard_verify.py` ✅
- `bash -lc 'if rg -n "/m/\$\{" frontend/apps/web/src/layouts/AppShell.vue; then exit 1; fi'` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅前端消费层收口与门禁增强，未改变后端契约与业务语义。

## Rollback suggestion
- `git restore frontend/apps/web/src/layouts/AppShell.vue scripts/verify/sidebar_navigation_consumer_verify.py docs/frontend/sidebar_navigation_consumer_v1.md`

## Next suggestion
- 进入下一批：聚焦 Sidebar 纯消费化剩余 UX 验证（父链展开/不可用提示）与 smoke 采样。

