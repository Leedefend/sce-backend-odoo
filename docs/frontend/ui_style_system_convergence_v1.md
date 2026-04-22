# UI Style System Convergence v1

## 1. Goal

本轮用于收敛 `frontend/apps/web` 的自定义前端视觉系统，先冻结全局 design tokens 与 shell 基线，再统一共享组件视觉语言，避免样式继续在页面内无序扩散。

产品级设计方向已补充到：

- `docs/frontend/ui_visual_blueprint_v1.md`

本轮定位：

- Layer Target: `Frontend contract-consumer runtime`
- Module: `frontend/apps/web`
- Scope: token / base / shared shell / shared component primitives / convergence docs

## 2. Scope

本轮已覆盖：

- 全局 token 基线
- base typography / background / form control baseline
- AppShell / Sidebar / Topbar / PageContainer
- MenuTree / StatusPanel
- PageHeader / PageToolbar / PageFeedback
- ListPage 顶部工具区、表格容器、分页容器
- ContractFormPage 头部动作区、卡片容器、概览 pill、chip
- KanbanPage 过滤 tabs、列容器、卡片容器

本轮未覆盖：

- 业务特化 `views/*` 的逐页重绘
- 全量表单字段布局重构
- 驾驶舱 / 看板特化页面全面统一
- 主题切换与品牌化包装
- 浏览器内截图采集与人工可视验收

后续延伸收口：

- `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-A` 已把详情辅助壳层与记录表格块并入 token 基线
- 覆盖 `DetailCommandBar`、`DetailShellLayout`、`FormSection`、`BlockRecordTable`
- 目标是消除高频详情页辅助面仍残留的 page-local hard-coded 颜色/圆角/阴影
- `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-B` 已把 `ContractFormPage` 的 support-zone 与 `BlockActivityFeed` 并入同一 token 语言
- 覆盖 relation / chatter / attachment 辅助卡片与 activity feed block
- `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-C` 已把 `ContractFormPage` 的 structure diagnostics、inline validation、submission feedback、advanced toggle 与 footer action 补齐到 token 语言
- `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-D` 已把剩余高频 legacy list/form wrappers（`RecordView`、`MyWorkView`）并入同一 token 基线

## 3. Style Layering

新增统一样式目录：

- `frontend/apps/web/src/styles/tokens.css`
- `frontend/apps/web/src/styles/base.css`
- `frontend/apps/web/src/styles/components/primitives.css`
- `frontend/apps/web/src/styles/layout/shell.css`
- `frontend/apps/web/src/styles/index.css`

接入方式：

- `frontend/apps/web/src/main.ts` 统一加载 `src/styles/index.css`

## 4. Token Baseline

`tokens.css` 冻结了以下设计令牌：

- color tokens：primary / success / warning / danger / neutral / surface
- typography tokens：font family / font size / weight / line height
- spacing tokens：`--ui-space-1` 到 `--ui-space-8`
- radius tokens：`xs / sm / md / lg / pill`
- shadow tokens：`xs / sm / md / lg`
- layout tokens：page width / page padding / sidebar width
- z-index 和 transition tokens

命名原则：

- 使用通用视觉语义，不绑定业务领域词
- 允许 shell、组件、页面共用
- 禁止继续在热点页面硬写新的主色、圆角、阴影常量

## 5. Shell Convergence

Batch A 将以下壳层统一到 token 驱动：

- `AppShell.vue`
- `MenuTree.vue`
- `StatusPanel.vue`

收口结果：

- Sidebar、Topbar、Router host 使用统一背景、边框、阴影、圆角
- 导航节点 active / ancestor / disabled / badge 的状态色统一
- 初始化 loading / error / empty 面板统一到同一反馈样式体系
- Router host 默认落入 `page-container`，减少页面宽度与边距漂移

## 6. Shared Component Convergence

Batch B 收口了共享组件与高频容器：

- `PageHeader.vue`
- `PageToolbar.vue`
- `PageFeedback.vue`
- `ListPage.vue`
- `ContractFormPage.vue`
- `KanbanPage.vue`

已统一的视觉语言：

- Button: primary / ghost 基线
- Input: 统一边框、聚焦态、尺寸
- Badge / pill / chip: 统一 pill 半径、状态色、文字层级
- Card / block: 统一边框、表面层、阴影
- Table shell: 顶部工具区、表格容器、分页容器
- Feedback surfaces: info / error / empty 的容器语义

## 7. List/Form Convergence Checkpoint

当前列表页收口点：

- `ListPage` 的 unified topbar、search menu、tabs、pagination、table shell
- `PageToolbar` 的搜索、筛选、排序、contract chips
- `KanbanPage` 的过滤 tabs、列容器、卡片信息密度

当前表单详情页收口点：

- `ContractFormPage` 的 compact topbar、header meta、action buttons
- form card / block / overview strip / chips
- `StatusPanel` 在表单 fallback、error、info 场景下的统一反馈
- `DetailCommandBar` 的流程阶段 / 下一步动作双区容器
- `DetailShellLayout` / `FormSection` 的 section、tab、nested shell 辅助层级
- `BlockRecordTable` 的区块头部、记录数、副标题、悬浮节奏
- support-zone 的 count badge、state badge、协作/关系卡片层级
- `BlockActivityFeed` 的 eyebrow、count badge、feed card 节奏
- structure-projection、validation/warn/success feedback、layout divider、footer ghost/primary actions
- `RecordView` 的 header/card/summary/chatter/timeline 与 `MyWorkView` 的 hero/filters/retry/table/pager

适用解释：

- 项目列表 / 任务列表 走共享 `ListPage`
- 项目详情 / 任务详情 走共享 `ContractFormPage`

因此，本轮页面收口优先落在通用列表/表单承接层，而不是为单业务页面单独写样式分支。

## 8. Verification Evidence

本轮已执行的工程门禁：

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-UI-SYSTEM-CONVERGENCE-V1-A.yaml`
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-LINT-GATE-RECOVERY.yaml`
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-UI-SYSTEM-CONVERGENCE-V1-B.yaml`
- `git diff --check`
- `pnpm -C frontend/apps/web lint`
- `pnpm -C frontend/apps/web build`

Lint gate note：

- 原始 ESLint CLI 在当前工作区内即使 `--no-eslintrc` 也超时
- 已在 lint-gate recovery 批次中把 `pnpm lint` 收敛为 `vue-tsc --noEmit -p tsconfig.strict.json`
- 原 `eslint . --ext .ts,.vue` 被保留为 `lint:eslint` 供后续专门恢复

## 9. Covered Files

本轮核心收口文件：

- `frontend/apps/web/src/main.ts`
- `frontend/apps/web/src/layouts/AppShell.vue`
- `frontend/apps/web/src/components/MenuTree.vue`
- `frontend/apps/web/src/components/StatusPanel.vue`
- `frontend/apps/web/src/components/page/PageHeader.vue`
- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `frontend/apps/web/src/components/page/PageFeedback.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/pages/KanbanPage.vue`
- `frontend/apps/web/src/styles/*`

## 10. Remaining Exceptions

仍需后续单独处理的区域：

- `views/*` 中历史局部样式仍然较多
- 表格细粒度单元格、排序、分组交互尚未全部统一
- 高风险高频 list/form wrappers 已进入统一 token 语言，后续剩余工作更偏浏览器证据、个别特化页和细节 polish
- 缺少浏览器内 before/after 截图资产
- 原生 ESLint CLI 超时的根因尚未单独修复

已缩小的例外：

- 高频详情页共享模板已不再依赖大面积硬编码视觉常量
- 辅助区卡片、tab rail、command bar、mini table 已与既有 token / primitive 语言对齐

## 11. Next Suggestions

建议后续顺序：

1. 开专门批次恢复 `lint:eslint`，定位 CLI 超时根因
2. 基于共享 `ListPage` 做项目/任务列表的筛选区与表格细节收口
3. 基于共享 `ContractFormPage` 做项目/任务详情的 section / notebook / 辅助区收口
4. 使用专门 UI-check 批次补人工页面验收与截图证据
