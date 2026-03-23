# First Release Slice Definition

## 首发产品

- 施工企业项目管理系统（首发版）

## 首发切片

- `项目创建 -> 驾驶舱`

## 切片链路定义

### 入口

- `project.initiation`
- 前端承载：
  - `frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`

### 动作

- `create_project`
- 当前实现真源：
  - intent：`project.initiation.enter`
  - handler：`addons/smart_construction_core/handlers/project_initiation_enter.py`

### 副动作

- `initialize_project`
- 当前实现真源：
  - service：`ProjectCreationService.post_create_bootstrap`
  - initializer：`ProjectInitializationService.bootstrap`
  - 文件：`addons/smart_construction_core/services/project_creation_service.py`

### 跳转

- `project.dashboard`
- 当前实现真源：
  - suggested action：`project.dashboard.enter`
  - scene entry handler：`addons/smart_construction_core/handlers/project_dashboard_enter.py`
  - scene orchestrator：`addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`

## L1-L5 映射

### L1 Model

- `project.project`
- 最小字段：
  - `name`
  - `manager_id`
  - `partner_id`
  - `date_start`
  - `date_end`

### L2 Domain Action

- `project.initiation.enter`
  - 创建项目
- `ProjectCreationService.post_create_bootstrap`
  - 初始化项目骨架

### L3 Scene

- `projects.intake`
- `project.dashboard`

### L4 Contract / Orchestration

- 创建后续契约入口：
  - `contract_ref.intent = "ui.contract"`
  - `scene_key = "project.dashboard"`
- 驾驶舱 entry contract：
  - `ProjectDashboardSceneOrchestrator.build_entry`
- 驾驶舱 block contract：
  - `ProjectDashboardContractOrchestrator.build_dashboard_contract_v1`

### L5 Frontend

- 创建页：
  - `frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
- 驾驶舱页：
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

## 用户路径

1. 进入创建页。
2. 输入最小字段。
3. 提交创建。
4. 创建成功。
5. 自动初始化项目骨架。
6. 跳转到驾驶舱入口。
7. 驾驶舱展示 `block + next_action`。

## 必备页面结果

- 创建成功后必须返回：
  - `record.id`
  - `suggested_action_payload.intent = "project.dashboard.enter"`
  - `contract_ref.intent = "ui.contract"`
- 驾驶舱必须展示：
  - `progress`
  - `risks`
  - `next_actions`

## 明确不包含

- 成本闭环
- 合同付款
- 结算分析

## 对外承诺边界

- 首发只承诺：
  - 创建项目
  - 初始化项目骨架
  - 进入驾驶舱
  - 展示首批项目状态与下一步动作
- 不承诺：
  - 成本闭环
  - 合同付款闭环
  - 结算分析闭环
