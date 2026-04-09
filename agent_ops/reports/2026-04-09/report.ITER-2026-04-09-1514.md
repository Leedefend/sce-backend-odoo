# ITER-2026-04-09-1514 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Sidebar consumer core refactor`

## Architecture declaration
- Layer Target: `Frontend consumer layer`
- Module: `Sidebar navigation consumer pipeline`
- Module Ownership: `frontend web shell`
- Kernel or Scenario: `scenario`
- Reason: Sidebar 从半解释器切换为 nav_explained 纯消费组件。

## Change summary
- 新增类型协议：`frontend/apps/web/src/types/navigation.ts`
  - 定义 `ExplainedMenuNode` 与 `active_match` 结构。
- 新增消费入口：`frontend/apps/web/src/composables/useNavigationMenu.ts`
  - 单一获取 `/api/menu/navigation`
  - 归一化 `nav_explained.tree/flat`
  - 提供加载状态与缓存。
- 重构 `frontend/apps/web/src/layouts/AppShell.vue`
  - Sidebar 数据源改为 `navigationMenu.tree`
  - 新增 `navigateByExplainedMenuNode(node)` 统一点击分发
  - active 高亮改为基于 `active_match(menu/scene/action/route_prefix)` 匹配
  - 刷新链路同步调用 `loadNavigation(true)`。
- 重构 `frontend/apps/web/src/components/MenuTree.vue`
  - 组件类型切换到 `ExplainedMenuNode`
  - 目录节点点击只展开/折叠
  - unavailable 与不可点击节点统一禁用显示。
- 新增文档：`docs/frontend/sidebar_navigation_consumer_v1.md`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1514.yaml` ✅
- `pnpm --dir frontend/apps/web exec tsc --noEmit src/types/navigation.ts` ✅
- `rg -n "nav_explained|is_clickable|active_match|target_type|navigateByExplainedMenuNode" ...` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：medium
- 说明：当前仅完成 Sidebar 消费主链，未覆盖全站所有旧菜单解释调用点。

## Rollback suggestion
- `git restore frontend/apps/web/src/types/navigation.ts frontend/apps/web/src/composables/useNavigationMenu.ts frontend/apps/web/src/layouts/AppShell.vue frontend/apps/web/src/components/MenuTree.vue docs/frontend/sidebar_navigation_consumer_v1.md`

## Next suggestion
- 进入下一批：清理 AppShell/SceneView/MenuView/Resolver 中残留旧 menuTree 解释路径，并补充 sidebar 回归验证脚本。
