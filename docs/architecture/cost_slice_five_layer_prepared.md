# Cost Slice Five-Layer Prepared

## 范围

- 切片：`项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 成本汇总`
- 阶段：`Prepared`

## L1 Model Layer

### 主载体

- `account.move`
- `project.project`

### 辅助载体

- `project.cost.code`

### 最小字段

- `account.move.project_id`
- `account.move.date`
- `account.move.ref`
- `account.move.line_ids`
- `account.move.line.project_id`
- `account.move.line.cost_code_id`

### 文件

- `addons/smart_construction_core/models/support/account_extend.py`
- `addons/smart_construction_core/views/support/account_extend_views.xml`

### 边界

- 本轮只复用 `account.move` 作为成本记录主载体
- 不新增大而全成本模型

## L2 Capability Layer

### 能力

- `create_cost_entry`
- `fetch_cost_list_block`
- `fetch_cost_summary_block`

### 文件

- `addons/smart_construction_core/services/cost_tracking_service.py`
- `addons/smart_construction_core/services/cost_tracking_native_adapter.py`
- `addons/smart_construction_core/services/cost_tracking_builders/*`
- `addons/smart_construction_core/services/cost_tracking_entry_service.py`

### 边界

- 只负责创建最小成本记录与读取项目成本事实
- 不在本层做预算/分析/审批

## L3 Scene / Orchestration Layer

### 场景

- `project.execution`
- `cost.tracking`

### 编排

- `project.execution -> cost.tracking.enter`
- `cost.tracking.block.fetch`
- `cost.tracking.record.create`

### 文件

- `addons/smart_construction_core/handlers/cost_tracking_enter.py`
- `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py`
- `addons/smart_construction_core/handlers/cost_tracking_record_create.py`
- `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py`

### 边界

- L3 只编排入口、block envelope 和写入 intent
- 不在 L3 拼复杂财务业务

## L4 Contract Layer

### 契约

- cost scene entry contract
- cost entry result contract
- cost list block contract
- cost summary block contract

### 文件

- `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py`
- `scripts/verify/product_cost_entry_contract_guard.py`
- `scripts/verify/product_cost_list_block_guard.py`
- `scripts/verify/product_cost_summary_block_guard.py`
- `scripts/verify/product_project_flow_execution_cost_smoke.py`

### 边界

- 统一由后端输出 contract
- 不允许前端自行构造列表/汇总语义

## L5 Frontend Layer

### 承载

- execution scene 的 cost 入口 action
- cost entry block
- cost list block
- cost summary block

### 文件

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- `scripts/verify/cost_slice_browser_smoke.mjs`

### 边界

- 前端只渲染 contract 与提交 intent
- 不允许前端自己 sum 金额
- 不允许前端自己按项目筛选成本

## Prepared 结论

- FR-3 的五层承载关系已定义。
- 后续实现必须严格落在上述边界内。
