# First Slice Frontend Boundary Audit

## 范围

- `frontend/apps/web/src/views/ProjectsIntakeView.vue`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

## 结论

- 总体判断：`首发链已基本满足“前端只消费 contract”`
- 详细结论：
  - 创建页：基本满足
  - 驾驶舱页：已从 `P1` 收敛到 `P2` 展示 fallback 库存

## 创建页审计

### 结果

- 判断：`A. 已基本满足`

### 证据

- `ProjectsIntakeView.vue` 主要职责是：
  - 场景入口导航
  - 根据 menu/scene registry 定位 action target
  - 路由跳转到标准创建页或快速创建页

### 观察

- 未发现：
  - 前端推导业务状态
  - 前端拼 `next_action`
  - 前端拼 block
- 存在但可接受：
  - `menu_xmlid / scene_key / action_id` 级导航定位逻辑

## 驾驶舱页审计

### 结果

- 判断：`B. 主链已收口，仅剩 P2 展示 fallback`

### 已满足部分

- 页面入口依赖 contract/runtime hint：
  - `PROJECT_DASHBOARD_ENTRY_INTENT`
  - `entry.blocks`
  - `entry.runtime_fetch_hints.blocks`

### 发现的问题

#### 已收口项 1：block 说明文案

- 位置：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:263`
- 表现：
  - `blockCaption()` 已改为优先消费 contract `caption`
  - 缺失时仅返回通用 fallback `区块按需加载。`
- 判断：
  - 原先的业务语义重建已移除

#### 已收口项 2：任务状态标签

- 位置：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:323`
- 表现：
  - `taskRows()` 现已优先消费 `state_label/state_tone`
  - 缺失时仅回退到原始 `state`
- 判断：
  - 原先的状态语义映射已移除

#### 已收口项 3：原因码中文文案

- 位置：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- 表现：
  - `humanReason()` 已删除
- 判断：
  - 原先的业务语义翻译已移除

#### 已收口项 4：next action 展示语义

- 位置：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:357`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:393`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:419`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:434`
- 表现：
  - `actionHint()` 直接消费 `hint/message`
  - `stateLabel/stateTone/buttonLabel` 直接优先消费 contract 字段
  - `currentStateText/nextStepText` 直接消费 summary labels
- 判断：
  - 原先的主链语义重建已移除

### 本轮处理原则

- 本轮已对首发主链做最小必要收口。
- 不继续扩成驾驶舱页整体重构。

### 剩余库存

#### P2-1 展示 fallback 仍在页面

- 位置：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:267`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:348`
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:447`
- 表现：
  - 当 contract 未提供 caption/empty_hint/next_step_label 时，页面仍有通用 fallback 文案
- 判断：
  - 这是通用展示 fallback，不再属于业务推导
  - 记为 `P2`

## 最终判断

- 创建页：接近“前端只消费 contract”
- 驾驶舱页：主链已达到 contract-first 消费，剩余为 `P2` 展示 fallback
- 因此总体结论是：
  - `首发链前端 boundary 已不再阻断冻结`
  - `剩余问题可纳入后续 P2 清理`
