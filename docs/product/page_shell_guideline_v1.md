# 页面骨架规范 v1

## 1. 目标

在不做组件大迁移的前提下，统一页面“产品壳”语言：标题区、工具条、内容区、状态区。

## 2. Scene Header 结构

推荐顺序：

1. 主标题（业务对象）
2. 副标题（当前范围/筛选上下文/更新时间）
3. 状态标签（加载完成、空态、异常态）
4. 快速动作（刷新、主动作）

## 3. 副标题/描述/面包屑/快速动作放置原则

- 副标题：一行内表达“我现在看的是哪一批数据”；
- 描述：仅在 dashboard/workspace 使用，用于决策语义提示；
- 面包屑：保留在路由层，不在每个 block 重复；
- 快速动作：右上角，最多 1 主 + 2 辅。

## 4. Summary Strip（可选）

- 位置：Header 下方，Toolbar 上方；
- 用途：展示记录数、预警数、关键金额/进度等“第一屏要点”；
- 适用：dashboard 必选，workspace 推荐，list 按场景可选。

## 5. 搜索/筛选/排序/批量操作条

- 搜索/筛选/排序：统一在 Toolbar；
- 批量操作：靠近列表区域顶部，避免与 Header 混杂；
- 多视图切换：放在 Toolbar 上游（可折叠）。

## 6. 主内容区容器与间距

- 顶层页面容器：统一 `grid + gap`；
- Header、Toolbar、Summary Strip、内容区分层明确；
- 区块内卡片使用统一圆角、边框与阴影等级。

## 7. 状态表达统一

- 加载态：`正在加载…` + 可重试入口（必要时）；
- 空态：业务语义文案 + 建议动作；
- 错误态：错误标题 + trace 信息 + 重试；
- 无权限态：说明缺失能力，不暴露内部错误码细节。

## 8. 本轮结构收敛落点（最小公共承载）

### 8.1 承载点

- 列表型页面：`ListPage.vue`（统一 Header/Toolbar/Batch bar/Table）
- 驾驶舱：`PageRenderer.vue` + `ProjectManagementDashboardView.vue`

### 8.2 本轮收敛页面

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

### 8.3 收敛方式

- 不改底层 contract 结构；
- 通过页面模式识别 + 字段语义映射完成表达层收敛；
- 通过 Summary Strip 和状态色增强关键信息可读性。
