# First Release Product Contract

## 定位

- 产品：`施工企业项目管理系统（首发版）`
- 冻结切片：`项目创建 -> 驾驶舱`
- 本文性质：`发布口径文档`

## 用户入口

- 用户必须从项目创建入口进入：
  - `frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
- 首发允许两种进入方式：
  - 快速创建
  - 标准立项

## 最小输入

### 冻结口径

- 最小必填集合固定为：
  - `name`
  - `manager_id`

### 证据

- 前端快速创建约束：
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - `quickRequiredReady`
- 后端创建白名单与必填校验：
  - `addons/smart_construction_core/handlers/project_initiation_enter.py`
  - `_ALLOWED_FIELDS`
  - `name` 缺失即失败

### 允许但非必填

- `partner_id`
- `date_start`
- `date_end`
- `description`

## 系统行为

### 创建动作

- 创建动作固定为：
  - `project.initiation.enter`

### 自动初始化

- 创建成功后系统自动执行：
  - `ProjectCreationService.post_create_bootstrap`
  - `ProjectInitializationService.bootstrap`

### 初始化内容

- 建立 `project.project`
- 若不存在任务根节点，则建立 `project.task` 根任务
- 写入项目初始化消息
- 成本 / 资金 / 风险只做承载准备，不在首发切片内继续展开

## 场景跳转

- 冻结流转固定为：
  - `project.initiation -> project.dashboard`
- 不允许多出口。
- 创建成功后的后续动作固定为：
  - `suggested_action_payload.intent = "project.dashboard.enter"`

## 驾驶舱范围

### 只允许

- 项目摘要
- 状态摘要
- 下一步动作

### 当前承载

- entry summary：
  - `project_code`
  - `manager_name`
  - `partner_name`
  - `stage_name`
  - `health_state`
- entry blocks：
  - `progress`
  - `risks`
  - `next_actions`

## 明确不包含

- 成本闭环
- 合同付款
- 结算分析

## 用户路径

1. 进入创建页。
2. 输入最小字段。
3. 点击创建。
4. 创建成功。
5. 系统自动初始化项目骨架。
6. 系统跳转驾驶舱。
7. 驾驶舱显示 block 与 next_action。

## 对内对外统一口径

- 可以说：
  - 首发版已覆盖项目创建到驾驶舱。
  - 创建成功后系统自动初始化项目骨架并进入驾驶舱。
- 不可以说：
  - 已完成成本、合同付款、结算全链路。
  - 已完成施工企业全业务闭环。

## 冻结结论

- 本文定义的是首发切片唯一产品口径。
- 后续任何首发表述必须与本文一致。
