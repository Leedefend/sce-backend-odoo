# 页面模式规范 v1

## 1. 目的

统一页面语义，避免所有场景都呈现为“万能页面”。本规范定义三类页面模式：`dashboard`、`workspace`、`list`。

## 2. 三类页面模式

### 2.1 dashboard

- 产品目标：在 10 秒内回答“现在状态如何、风险在哪、下一步做什么”。
- 页面骨架：
  1) Scene Header（标题/项目上下文/关键动作）
  2) Summary Strip（可选，指标或状态徽标）
  3) 主内容分区（指标、风险、进度、专题块）
- 典型信息结构：
  - 顶部指标卡（KPI）
  - 高优先级风险提醒
  - 进度与执行概览
  - 资金/成本/合同辅助块

### 2.2 workspace

- 产品目标：支持角色在一个业务域内连续处理任务。
- 页面骨架：
  1) Scene Header（标题+业务意图）
  2) 操作条（搜索/筛选/快捷操作）
  3) 主工作区（列表/卡片/分组）
- 典型信息结构：
  - 待处理对象
  - 状态分层与异常提示
  - 批量动作入口

### 2.3 list

- 产品目标：稳定、高效地进行台账式浏览、筛选、排序与批量处理。
- 页面骨架：
  1) Scene Header（标题、记录数、刷新）
  2) Table Toolbar（搜索/筛选/排序）
  3) 列表区（关键列优先、状态可读）
- 典型信息结构：
  - 关键识别列（名称/状态/负责人）
  - 业务量化列（金额/更新时间）
  - 批量操作与导出

## 3. 核心页面归类

- `project.management` → `dashboard`
- `my_work.workspace` → `workspace`
- `risk.center` → `workspace`
- `projects.ledger` → `workspace`（带 dashboard-like 总览层）
- `projects.list` / `task.center` / `cost.project_boq` → `list`

说明：`projects.ledger` 当前采用卡片台账承载，且需要先展示项目群总览，再下钻单项目，故归为 `workspace` 更合理。

## 4. 前端渲染层消费方式

## 4.1 已有可承载位置

可复用 `Scene.layout.kind` 作为 page mode 的最小语义来源，并在前端增加归一化映射：

- `layout.kind=ledger|workspace` → `workspace`
- `layout.kind=list` → `list`
- `project.management` 强制归类为 `dashboard`

## 4.2 最小接入建议（本轮）

1. 在前端新增 page mode 归一化工具（仅展示层使用）；
2. `ProjectManagementDashboardView` 与 `ActionView/ListPage` 读取 page mode；
3. 将 page mode 用于：
   - 页面 Header 文案；
   - Summary Strip 是否出现；
   - 工具条布局风格与优先级；
4. 保持 scene registry / contract envelope 不变。

## 5. 后续演进建议（非本轮）

- 在 scene payload 的 page 节点中统一补充 `page_mode`，减少推断；
- 在 page contract 里补充 mode-specific render hints；
- 将 mode 作为设计验收与回归检查项。
