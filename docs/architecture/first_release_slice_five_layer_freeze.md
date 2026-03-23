# First Release Slice Five-Layer Freeze

## 冻结对象

- 切片：`项目创建 -> 驾驶舱`
- 原则：五层职责固定，不允许跨层合并

## L1 Model Layer

### 冻结对象

- `project.project`

### 最小字段集合

- `name`
- `manager_id`
- `partner_id`
- `date_start`
- `date_end`

### 关键文件

- `addons/smart_construction_core/handlers/project_initiation_enter.py`
- `addons/smart_construction_core/services/project_creation_service.py`

### 冻结状态

- `已冻结`

### 修改策略

- 默认不允许修改
- 只有在首发切片被直接阻断时才允许调整

## L2 Domain Capability Layer

### 冻结对象

- `create_project`
  - 真源：`project.initiation.enter`
- `initialize_project`
  - 真源：`ProjectCreationService.post_create_bootstrap`

### 职责边界

- `create_project`：
  - 接收输入
  - 业务校验
  - 创建 `project.project`
  - 返回后续契约入口
- `initialize_project`：
  - 建立轻量项目骨架
  - 不返回页面结构

### 关键文件

- `addons/smart_construction_core/handlers/project_initiation_enter.py`
- `addons/smart_construction_core/services/project_creation_service.py`

### 冻结状态

- `已冻结`

### 修改策略

- 不允许合并为单一职责块
- 不允许把初始化逻辑塞回前端或 Scene

## L3 Scene Layer

### 冻结对象

- `projects.intake`
- `project.dashboard`

### 关键文件

- `frontend/apps/web/src/app/projectCreationBaseline.ts`
- `addons/smart_construction_core/handlers/project_dashboard_enter.py`
- `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`

### 冻结状态

- `已冻结`

### 修改策略

- 流转固定为：
  - `project.initiation -> project.dashboard`
- 不允许多出口
- 不允许引入新首发 scene

## L4 Contract Layer

### 冻结对象

- 创建输入 contract
- 创建输出 contract
- dashboard entry contract
- dashboard block contract

### 关键文件

- `addons/smart_construction_core/handlers/project_initiation_enter.py`
- `addons/smart_construction_core/handlers/project_dashboard_enter.py`
- `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
- `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py`
- `scripts/verify/product_project_creation_mainline_guard.py`
- `scripts/verify/product_project_dashboard_entry_contract_guard.py`
- `scripts/verify/product_project_dashboard_block_contract_guard.py`

### 冻结状态

- `已冻结`

### 修改策略

- 默认不允许修改 shape
- 如需调整，必须同步 guard 与 release 文档

## L5 Frontend Layer

### 冻结对象

- 创建页
- 驾驶舱页

### 关键文件

- `frontend/apps/web/src/views/ProjectsIntakeView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

### 冻结要求

- 创建页：
  - 只做入口与表单消费
- 驾驶舱页：
  - 只消费 entry / block contract
  - 不推导业务语义

### 冻结状态

- `已冻结`

### 修改策略

- 默认不允许修改
- 只允许首发链阻断修复

## 冻结结论

- 五层承载关系已经固定。
- 任何首发切片改动，都不得跨出以上边界。
