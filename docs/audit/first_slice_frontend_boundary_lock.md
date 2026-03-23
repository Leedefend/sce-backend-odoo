# First Slice Frontend Boundary Lock

## 范围

- `frontend/apps/web/src/views/ProjectsIntakeView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

## 冻结结论

- 结论：`首发链前端已满足冻结要求`

## 检查结果

### 创建入口

- `ProjectsIntakeView.vue`
- 判断：
  - 不推导业务状态
  - 不拼 `next_action`
  - 不拼 block
  - 只承担入口导航与路由

### 创建页

- `ContractFormPage.vue`
- 判断：
  - 表单消费 contract / field descriptor
  - 创建成功后固定跳转 `project.dashboard`
  - 未发现首发链内 block 拼装

### 驾驶舱页

- `ProjectManagementDashboardView.vue`
- 判断：
  - 主链语义重建已收口
  - 当前优先消费 contract 的：
    - `caption`
    - `hint`
    - `state_label`
    - `state_tone`
    - `button_label`
    - `current_state_label`
    - `next_step_label`
  - 剩余 only `P2` 通用展示 fallback

## 冻结规则

- 首发链前端不得新增业务状态推导
- 首发链前端不得拼装 `next_action`
- 首发链前端不得扩写 dashboard block
- 首发链前端只允许消费 contract

## 已接受残留

- `P2` 通用展示 fallback：
  - caption 缺失 fallback
  - empty_hint 缺失 fallback
  - next_step_label 缺失 fallback

## 最终判断

- 是否满足“前端只消费 contract”：`YES`
- 是否允许进入首发冻结：`YES`
