# Dashboard Block Whitelist

## 范围

- 页面：`project.dashboard`
- 目的：冻结首发驾驶舱 block 白名单，禁止继续膨胀

## 当前扫描结果

### A. 首发必须

- `progress`
  - 标题：`项目进度`
  - block_type：`progress_summary`
- `risks`
  - 标题：`风险提醒`
  - block_type：`alert_panel`
- `next_actions`
  - 标题：`下一步动作`
  - block_type：`action_list`

证据：
- `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
- `addons/smart_construction_core/services/project_dashboard_service.py`
- `scripts/verify/product_project_dashboard_entry_contract_guard.py`
- `scripts/verify/product_project_dashboard_block_contract_guard.py`

### B. 非首发

- 无额外 block 进入当前驾驶舱 entry 白名单。
- 任何成本、合同、结算、项目门户式扩展块均属于非首发。

### C. 可接受但不扩展

- entry summary：
  - `project_code`
  - `manager_name`
  - `partner_name`
  - `stage_name`
  - `health_state`

## 最终白名单

### 允许展示

- 项目摘要
- 状态摘要
- 下一步动作

### 固化到 contract 的 block key

- `progress`
- `risks`
- `next_actions`

## 冻结规则

- 禁止新增 block
- 禁止展示扩展信息块
- 禁止把驾驶舱扩展为项目门户

## 冻结结论

- 首发驾驶舱只允许三块：
  - `项目进度`
  - `风险提醒`
  - `下一步动作`
