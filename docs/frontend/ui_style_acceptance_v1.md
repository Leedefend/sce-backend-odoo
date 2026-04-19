# UI Style Acceptance v1

## 1. Acceptance Scope

本轮验收对象：

- shell baseline
- shared component primitives
- generic list/form consumer surfaces

目标页面链路：

- 项目列表
- 任务列表
- 项目详情
- 任务详情

说明：

- 本轮代码收口发生在共享 `ListPage` / `ContractFormPage` / `KanbanPage` 承接层
- 因此项目/任务链路的验收以“共享承接层是否已统一”为主
- 当前仓库执行 lane 未包含浏览器截图采集，故本文件记录工程门禁与结构级验收，不虚报人工截图

## 2. Implemented Acceptance Mapping

### Shell / Navigation

已验证覆盖：

- `AppShell.vue`
- `MenuTree.vue`
- `StatusPanel.vue`

结构结果：

- Sidebar / Topbar / Router host 已切到统一 token 与容器层级
- 导航选中态、祖先态、不可用态、badge 状态一致
- 初始化 loading / error / empty 反馈统一

### List Surfaces

已验证覆盖：

- `PageHeader.vue`
- `PageToolbar.vue`
- `ListPage.vue`
- `KanbanPage.vue`

结构结果：

- 列表页顶部标题区、搜索区、筛选区、分页区的边框/圆角/按钮层级一致
- 表格容器、分页容器、summary cards 统一到共享视觉语言
- Kanban filter tabs、列容器、记录卡片统一到同一 token 体系

### Form Surfaces

已验证覆盖：

- `ContractFormPage.vue`
- `StatusPanel.vue`

结构结果：

- 表单 compact topbar、header actions、meta line 统一
- card / block / overview strip / chips 已统一到共享视觉语言
- fallback / error / info 的反馈容器与按钮状态一致

## 3. Verification Commands

本轮已执行：

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-UI-SYSTEM-CONVERGENCE-V1-A.yaml`
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-LINT-GATE-RECOVERY.yaml`
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-UI-SYSTEM-CONVERGENCE-V1-B.yaml`
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-18-FE-UI-SYSTEM-CONVERGENCE-V1-C.yaml`
- `git diff --check`
- `pnpm -C frontend/apps/web lint`
- `pnpm -C frontend/apps/web build`

结果：

- task contracts: PASS
- diff integrity: PASS
- frontend lint gate: PASS
- frontend build: PASS

## 4. Solved Problems

本轮已解决：

- 样式基础值散落，缺少统一 token 基线
- AppShell / Sidebar / Topbar 视觉层级割裂
- 初始化反馈面板样式不统一
- PageHeader / PageToolbar / ListPage / ContractFormPage / KanbanPage 各自重复定义按钮、容器、pill
- `pnpm lint` 不可作为批次门禁的问题

## 5. Unresolved Problems

本轮未解决：

- 原始 ESLint CLI 超时的根因修复
- 浏览器内项目/任务页面的人工截图对比
- `views/*` 历史页面的全量样式收口
- 详情页 notebook / chatter / activity 等辅助区的统一规范
- 表格更细粒度的行态、排序态、操作列规范

## 6. Exception Notes

例外项说明：

- `pnpm lint` 当前是受控静态 gate，实际执行 `vue-tsc --noEmit -p tsconfig.strict.json`
- `lint:eslint` 仍保留，但不纳入本轮自动门禁
- 页面“已覆盖”指共享承接层已覆盖，不等于所有业务 view 单页都已人工核验

## 7. Suggested Next Acceptance Batch

建议下一轮验收：

1. 单开 UI-check 批次，人工验证项目列表、任务列表、项目详情、任务详情
2. 为项目/任务链路补 before/after 截图
3. 将 notebook / section / chatter 辅助区纳入详情页统一规范
