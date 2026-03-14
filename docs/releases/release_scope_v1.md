# SCEMS v1.0 发布范围冻结（Release Scope Freeze）

## 1. 文档信息
- 版本：`v1.0`
- 状态：`Draft`（进入冻结评审）
- 关联主文档：`docs/releases/construction_system_v1_release_plan.md`

## 2. 发布范围（In Scope）

### 2.1 业务域
- 项目管理
- 合同管理
- 成本控制
- 资金管理
- 任务协同
- 风险提醒

### 2.2 主导航（冻结）
- 我的工作
- 项目台账
- 项目管理
- 合同管理
- 成本控制
- 资金管理
- 风险提醒

### 2.3 核心 Scene（冻结）
- `my_work.workspace`
- `projects.ledger`
- `project.management`
- `contracts.workspace`
- `cost.analysis`
- `finance.workspace`
- `risk.center`

### 2.4 Project Management 控制台（冻结）
必须包含 7 个区块：
- Header（项目基本信息）
- Metrics（关键指标）
- Progress（项目进度）
- Contract（合同执行）
- Cost（成本控制）
- Finance（资金情况）
- Risk（风险提醒）

## 3. 不在范围（Out of Scope）
- 配置中心进入主导航
- 数据中心进入主导航
- 系统治理进入主导航
- 新增外部依赖/新模块（未过变更评审）

## 4. 入口与投放策略
- 产品面：`construction_pm_v1`
- 主导航投放 allowlist：
  - `project.management`
  - `projects.ledger`
  - `my_work.workspace`
  - `contracts.workspace`
  - `cost.analysis`
  - `finance.workspace`
  - `risk.center`
- 隐藏模式：`config.*`、`data.*`、`internal.*`

## 5. 验收冻结标准
- 范围文档、资产盘点、缺口分析三件套齐全
- 主导航与 Scene 清单与交付策略一致
- 核心路径可走通：登录→我的工作→项目台账→项目驾驶舱→合同/成本/资金/风险

## 6. 变更控制
- 任何新增范围必须提交变更单并经发布负责人确认
- 范围冻结后仅允许修复阻断发布的缺陷
