# 平台内核边界冻结 v1

状态：Boundary Freeze Baseline  
适用对象：平台内核对齐批次、后续代码层收敛、Codex 连续迭代约束

---

## 1. 文档目的

本文件用于冻结当前阶段的平台内核边界，明确：

- 哪些能力属于平台内核
- 哪些能力不属于平台内核
- 哪些能力暂缓判定
- 哪些高风险资产本轮明确禁止迁移

这份冻结文档的目标不是马上触发模块重组，而是先阻止“边做边漂移”。

---

## 2. 属于平台内核

当前阶段，以下能力明确属于平台内核：

### 2.1 gateway / auth / audit

- intent / frontend api 等统一入口
- 认证、鉴权、审计、trace、异常包裹
- request/response contract 的通用门面

当前主要承载位置：

- `addons/smart_core`

### 2.2 metadata

- contract / metadata / view schema 读取与组装
- 前端通用消费所需的结构化元信息
- 通用字段、视图、surface 语义加工

当前主要承载位置：

- `addons/smart_core`

### 2.3 intent engine

- intent 路由
- intent handler 主链
- action/contract 分发与最小运行时入口

当前主要承载位置：

- `addons/smart_core`

### 2.4 contract governance

- contract freeze
- request normalization
- response envelope 规范
- verify / snapshot / compatibility policy

当前主要承载位置：

- `addons/smart_core`
- `scripts/verify`
- `docs/architecture`

### 2.5 orchestration runtime

- scene-ready contract 的平台级编排机制
- resolver / mapper / orchestrator / scene engine
- 平台侧 provider locator 与 runtime mechanism

当前主要承载位置：

- `addons/smart_scene`

### 2.6 event bus / runtime utility / common adapter

- 通用 adapter
- runtime helper
- read model / utility / policy loader
- 不携带行业语义的 common helper

当前主要承载位置：

- `addons/smart_core`
- `addons/smart_scene`

### 2.7 agent governance

- 任务合同
- 队列
- 风险扫描
- 分类
- 报告
- 停机规则

当前主要承载位置：

- `agent_ops`

---

## 3. 不属于平台内核

以下能力当前明确不属于平台内核：

### 3.1 construction-specific business models

- construction contract
- progress / cost / finance / treasury specific models
- industry-specific workflow state

当前主要承载位置：

- `addons/smart_construction_core`

### 3.2 payment / settlement / account 语义域

这些属于高风险业务语义，不允许自动迁入 kernel：

- payment request
- settlement order
- account / ledger / treasury semantics

当前主要承载位置：

- `addons/smart_construction_core`

### 3.3 scenario-specific dashboard business blocks

- construction-specific dashboard cards
- 行业场景下的 cockpit block 业务语义
- 依赖行业事实的业务组件

当前主要承载位置：

- `addons/smart_construction_core`
- `addons/smart_construction_scene`
- `frontend/apps/web`

### 3.4 industry workflow specifics

- construction-specific approval flow
- settlement/payment/cost-specific orchestration
- 依赖行业角色与业务制度的流程编排

当前主要承载位置：

- `addons/smart_construction_core`
- `addons/smart_construction_scene`

---

## 4. 暂缓判定

以下能力当前不立即归入或排除，保留到下一轮再做判断：

### 4.1 通用项目管理能力

例如：

- project / task / stage / milestone 的通用能力
- 通用项目工作台能力
- 不带 construction-specific 语义的 dashboard capability

当前判断：

- 很可能属于“通用项目应用层”
- 本轮不直接归入平台内核

### 4.2 前端通用承接层与场景组件层的切分

当前 `frontend/apps/web` 既有：

- 通用 shell / route / contract consumer
- 场景特化页面与组件

当前判断：

- 需要 execution baseline 单独说明
- 本轮不做代码层切分

### 4.3 多租户相关能力

当前判断：

- 属于目标架构中的平台能力候选
- 但本仓库当前并无可安全收敛的真实实现入口
- 本轮只保留为目标项，不进入代码层对齐

---

## 5. 当前禁止迁移的高风险资产

本轮平台内核对齐中，以下资产明确禁止自动迁移：

- `security/**`
- `record_rules/**`
- `ir.model.access.csv`
- `addons/**/models/**/*payment*`
- `addons/**/models/**/*settlement*`
- `addons/**/models/**/*account*`
- `migrations/**`
- `__manifest__.py`

理由：

- 这些路径要么涉及安全与权限，要么涉及高风险财务语义，要么会触发模块生命周期变化

---

## 6. 当前阶段的边界判定规则

后续任何“平台内核对齐”任务，都必须先回答：

1. 该能力是平台机制，还是行业语义？
2. 该能力是否被多个场景复用？
3. 该能力是否要求依赖 construction-specific 业务事实才能成立？
4. 该能力迁入平台后，是否会让 kernel 承担 payment / settlement / account 等高风险语义？

判定原则：

- 平台机制可收敛
- 行业语义不得上卷
- 暂不确定的能力进入“暂缓判定”

---

## 7. 本轮结论

本轮边界冻结的核心结论是：

- `smart_core` + `smart_scene` 构成当前平台内核主候选
- `smart_construction_core` + `smart_construction_scene` 仍以行业能力为主
- 通用项目应用层尚未完全显式化，但不能因此把行业语义直接卷入 kernel
- 高风险财务与安全资产本轮明确禁止自动迁移

---

## 8. 下一步建议

下一张应进入：

1. 命名对齐策略
2. execution baseline
3. AGENTS / prompt 绑定

只有这些完成后，平台内核代码层对齐才具备合法入口。
