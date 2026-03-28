# 平台内核现状映射基线 v1

状态：Execution Baseline Artifact  
适用对象：平台内核对齐批次、模块边界冻结、连续迭代调度

---

## 1. 文档目的

本文档把当前仓库中的核心模块、运行时资产和治理资产，映射到目标平台架构中的对应层级。

它回答的不是“最终 `paas_*` 结构应该长什么样”，而是：

1. 当前哪些模块已经承担平台内核职责。
2. 当前哪些模块仍属于行业层或场景层。
3. 前端哪些能力属于通用承接层，哪些属于业务场景承接层。
4. 哪些资产已经对齐，哪些仍未对齐，哪些本轮不处理。

---

## 2. 当前模块清单与目标层映射

| 当前资产 | 当前主要职责 | 目标架构归属 | 当前判断 |
| --- | --- | --- | --- |
| `addons/smart_core` | gateway-like handlers、intent/contract/runtime、permission/delivery、通用 runtime helper | 平台内核候选 | 已对齐主入口 |
| `addons/smart_scene` | scene orchestrator、layout/structure mapper、scene-ready contract 生成 | 编排/场景运行时层 | 已对齐主运行时 |
| `addons/smart_construction_core` | 行业领域模型、行业服务、行业 dashboard/business handler | 行业场景产品层 | 混入少量通用能力，需要后续剥离 |
| `addons/smart_construction_scene` | construction-specific scene 内容、registry content、industry provider | 行业场景资产层 | 基本对齐 |
| `frontend/apps/web` | portal shell、route、contract consumption、通用页面承接 | 前端承接层 | 通用承接与场景组件混合 |
| `scripts/verify` | 守卫、smoke、contract/risk/architecture verify | 治理与审计层 | 已对齐 |
| `agent_ops` | 任务合同、队列、风险扫描、报告、停机规则 | 治理与自动执行层 | 已对齐 |
| `docs/architecture` | 架构蓝图、实施基线、boundary/freeze | 架构治理层 | 已对齐 |
| `docs/product` | 产品能力、场景闭环、交付与迭代基线 | 产品治理层 | 已对齐 |

---

## 3. 平台内核现状判断

### 3.1 `smart_core`

当前已经承担的平台内核职责包括：

- handler / intent / contract 主入口
- runtime helper 与 request normalization
- delivery / audit / permission 等通用平台能力
- 启动链关键节点：`system.init`、`load_contract`、`ui.contract`

当前未完全收敛的问题：

- 仍残留一部分 transitional compatibility 路径
- 局部 helper 还和历史 handler 内联逻辑混在一起
- 少量 dashboard/runtime 支撑能力与行业语义存在边界模糊

结论：

- `smart_core` 是当前平台内核主候选，不应被视为普通行业模块
- 当前阶段优先做边界收敛，不做物理模块重命名

### 3.2 `smart_scene`

当前已经承担的职责：

- scene identity / resolver
- layout orchestration
- scene-ready contract assembly
- provider / content location mechanism

结论：

- `smart_scene` 当前更接近“平台编排运行时层”
- 后续应继续增强其对 scene-ready output 的唯一性，而不是把页面真相退回前端或行业模块

---

## 4. 行业层与场景层现状判断

### 4.1 `smart_construction_core`

当前属于行业层的内容：

- construction-specific business models
- cost / contract / progress / finance-oriented domain services
- 行业 dashboard 业务语义

当前存在的未对齐点：

- 少量通用 orchestration / runtime 辅助逻辑仍可能残留在行业层
- 某些通用项目管理能力与 construction-specific 语义尚未完全拆开

当前策略：

- 本轮不做大规模代码剥离
- 只在文档中明确这部分属于“通用项目应用 + 行业能力混合体”

### 4.2 `smart_construction_scene`

当前主要承担：

- construction-specific scene registry content
- industry provider content
- construction-specific scene asset composition

结论：

- 当前应归入行业场景资产层，而不是平台内核
- 后续只能把机制迁回平台，不能把行业内容误收进 kernel

---

## 5. 前端现状映射

### 5.1 通用承接层

`frontend/apps/web` 当前已承担：

- shell / route / app chrome
- contract consumer
- page/scene 渲染承接
- 通用 portal 视图基座

### 5.2 场景组件层

当前仍混在前端仓中的内容：

- 某些面向具体业务场景的页面组件
- 局部场景特化交互承接

当前判断：

- 前端并非“纯通用内核”或“纯业务页面”二选一，而是两者混合
- 当前阶段应继续坚持双轨策略：
  - 常规页面优先契约/元数据驱动
  - 复杂工作台允许受控特化组件承接

---

## 6. 已对齐项

- `smart_core` 已明确是平台内核主候选
- `smart_scene` 已明确是 scene/orchestration runtime 主候选
- `agent_ops` 已形成可连续运行的治理控制平面
- `scripts/verify` 已形成架构与回归守卫基础
- 目标蓝图与实施映射文档已经分层存在

---

## 7. 未对齐项

- `smart_construction_core` 中通用项目能力与行业能力仍有混合
- `frontend/apps/web` 的通用承接层与场景组件层仍未显式冻结
- 平台内核命名仍是 `smart_*` 体系，尚未与逻辑 `paas_*` 名称完全对齐
- AGENTS / prompts / guard 尚未统一绑定新的 execution baseline

---

## 8. 风险项

- 若在未冻结边界前直接做模块重命名，极易造成“看似平台化、实则把行业逻辑搬进内核”
- 若在未定义 execution baseline 前继续自动迭代，Codex 可能继续沿局部代码便利性推进，而不是沿架构目标推进
- 若把 `smart_construction_core` 中的 cost / payment / settlement / account 语义直接纳入 kernel 对齐，会触发高风险域越界

---

## 9. 暂不处理项

本轮明确暂不处理：

- payment / settlement / account 领域重构
- ACL / record rule / security 迁移
- physical module rename
- 多租户真实实现
- 大规模行业模块拆分

---

## 10. 下一步建议

下一张任务应进入：

1. 平台内核边界冻结
2. 命名对齐策略
3. execution baseline

只有完成这三项后，后续代码层平台内核对齐才具备合法入口。
