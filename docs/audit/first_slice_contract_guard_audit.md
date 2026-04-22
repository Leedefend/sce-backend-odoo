# First Slice Contract & Guard Audit

## 审计对象

- 创建输入 contract
- 创建输出 contract
- dashboard entry contract
- next_action contract
- creation flow guard
- dashboard entry guard
- block render guard

## 审计结论

### A. 已存在且正确

#### 创建输出 contract

- 证据：
  - `addons/smart_construction_core/handlers/project_initiation_enter.py`
- 结构：
  - `data.record`
  - `data.suggested_action_payload`
  - `data.contract_ref`
- 判断：
  - 已形成创建成功后的最小输出 contract

#### dashboard entry contract

- 证据：
  - `addons/smart_construction_core/handlers/project_dashboard_enter.py`
  - `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
  - `scripts/verify/product_project_dashboard_entry_contract_guard.py`
- 判断：
  - 已有固定 entry key、summary key、block key 与 runtime hint guard

#### next_action contract

- 证据：
  - 创建后 suggested action：
    - `addons/smart_construction_core/handlers/project_initiation_enter.py`
  - 驾驶舱下一步动作 block：
    - `addons/smart_construction_core/services/project_dashboard_builders/project_next_actions_builder.py`
    - `scripts/verify/product_project_dashboard_block_contract_guard.py`
- 判断：
  - 已形成 `intent + params + state + reason_code` 的最小可执行 contract

#### creation flow guard

- 证据：
  - `scripts/verify/product_project_creation_mainline_guard.py`
  - `scripts/verify/product_project_flow_initiation_dashboard_smoke.py`
- 判断：
  - 已覆盖创建主链与 initiation -> dashboard handoff

#### dashboard entry guard

- 证据：
  - `scripts/verify/product_project_dashboard_entry_contract_guard.py`
- 判断：
  - 已覆盖 entry contract shape

#### block render guard

- 证据：
  - `scripts/verify/product_project_dashboard_block_contract_guard.py`
- 判断：
  - 已覆盖 `progress / risks / next_actions` 三个 block 的 contract shape

### B. 存在但不完整

#### 创建输入 contract

- 证据：
  - `addons/smart_construction_core/handlers/project_initiation_enter.py`
  - `_ALLOWED_FIELDS`
  - `name` 必填校验
- 判断：
  - 已有字段白名单与最小必填约束
  - 但缺少独立的“创建输入 contract guard”脚本

### C. 缺失，后续必须补

- 独立的 creation input contract guard
  - 当前只有 handler 内联校验，没有单独 verify 产物
- 前端 block render 的浏览器级 contract 守卫
  - 当前主要是 API/block guard，不是浏览器渲染 guard

## 结构结论

- 首发链已经具备 contract 化主干：
  - `create -> suggested_action -> dashboard.enter -> entry blocks -> runtime blocks`
- 当前短板不在“完全缺 contract”
- 当前短板在：
  - 创建输入 contract 的 guard 独立性不足
  - 浏览器级渲染证据仍弱于 API/shape 级证据
