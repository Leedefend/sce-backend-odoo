# Project Kanban Sidebar Exposure Chain Audit

日期：2026-03-29

## 结论

当前“项目看板入口消失”不是 `KanbanPage` 渲染器问题，也不是 `ActionView` 的 `kanban` 能力缺失。

根因在导航暴露链：

1. 左侧侧边栏只消费 `session.releaseNavigationTree || session.menuTree`
2. 这棵树来自 `system.init` 返回的 `release_navigation_v1.nav` 或 `nav`
3. `MenuTree` 只渲染 `NavNode`，不根据 `meta.view_modes` 派生视图级子入口
4. `MenuView` 点叶子后统一进入同一个 `action/:actionId` 或 `scene`
5. `kanban` 只在 `ActionView` 内部作为同一 action 的页面内 view switch 存在

因此：

- 如果产品化侧边栏只暴露“项目列表/项目台账”这一条 action/scene
- 而没有单独配置“项目看板”菜单节点或 scene 节点

那么左侧不会出现独立的“项目看板”入口，这是当前架构的真实表现。

## 证据链

### 1. 侧边栏数据源

`AppShell.vue`：

- `navigationTree = releaseNavigationTree.length ? releaseNavigationTree : menuTree`
- `MenuTree` 直接渲染 `filteredMenu`

说明左侧只消费导航树，不消费页面内 view mode。

### 2. system.init 导航装载

`stores/session.ts`：

- `releaseNav = result.release_navigation_v1?.nav`
- `menuTree = nav.map(addKeys)`
- `releaseNavigationTree = releaseNav.map(addKeys)`

说明产品化导航一旦存在，会覆盖普通 `menuTree` 成为左侧主导航来源。

### 3. NavNode 表达能力

`frontend/packages/schema/src/index.ts`：

- `NavNode` 只有 `menu_id / scene_key / meta.action_id`
- `NavMeta` 虽然可带 `view_modes`
- 但节点本身没有“view target entry”层级

说明 schema 允许节点携带 action 的多视图信息，但没有定义“每个 view mode 都是一个独立导航节点”。

### 4. 菜单点击行为

`menuResolverCore.js`：

- 有 `scene_key` 时，返回 `redirect`
- 有 `meta.action_id` 时，返回 `leaf`
- 没有任何逻辑把 `view_modes` 展开成菜单项

说明菜单解析只负责“跳 scene / 跳 action”，不负责“跳 action 的某个 view mode”。

### 5. kanban 的真实入口层

`ActionView.vue`：

- `availableViewModes` 来源于 contract/meta `view_modes`
- `actionableViewModes` 是页面内可切换视图集合
- `vm.page.availableViewModes` 用于 action 页顶部 view switch

说明 `kanban` 当前是 action 页内部的 view switch，不是侧边栏导航树入口。

## 精确判断

当前用户看到“没有项目看板入口”，更准确地说是：

- 当前产品化侧边栏没有单独暴露“项目看板”导航节点
- 而不是系统不会渲染看板

只要进入同一个 `project.project` action，并且该 action contract/meta 暴露 `kanban` 视图，页面内仍然可以切到 `kanban`。

## 边界结论

### 侧边栏负责

- 暴露产品/场景/菜单节点
- 决定用户能否从导航树进入某个 scene 或 action

### ActionView 负责

- 在进入某个 action 之后，根据 contract 暴露列表/看板/图表等 view switch

### 当前缺口不在

- `KanbanPage.vue`
- `resolveActionViewAvailableModes(...)`
- `ActionView` 的 kanban consumer

### 当前缺口在

- 产品化导航树是否需要单独暴露“项目看板”节点
- 或者是否接受“看板只作为 action 页内部视图切换存在”

## 下一步实现目标

有两条正确路径，二选一：

1. 保持当前架构
- 不给侧边栏单独加“项目看板”入口
- 只保证项目 action 页内部的 `kanban` 视图切换可见、可用

2. 明确把看板做成导航入口
- 在 `release_navigation_v1.nav` 或 scene/menu contract 中增加独立节点
- 该节点跳转到同一 action，但带 `view_mode=kanban`
- 前端仍不做模型特判，只消费新增导航事实

## 推荐

推荐先走路径 1：

- 风险最低
- 不改变产品导航语义
- 符合“侧边栏是产品菜单，view switch 是页面内能力”的当前分层

如果业务坚持左侧必须直接出现“项目看板”，再开一张导航 contract 任务补“独立导航节点”。
