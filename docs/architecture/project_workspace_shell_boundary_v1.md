# Project Workspace Shell Boundary v1

状态：Code Alignment Boundary Freeze  
适用对象：workspace/dashboard 主线、runtime helper 收敛、scenario block 归属判定

---

## 1. 文档目的

在 common project candidate map 已经建立后，下一步必须回答：

- 哪些 dashboard/workspace 能力属于 common shell
- 哪些能力仍然属于 scenario block
- 哪些区域虽然看起来通用，但当前仍然暂缓收敛

如果这个边界不先冻结，后续代码层 helper 抽取很容易把行业语义误吸进平台或 common project 层。

---

## 2. Common Shell

以下能力当前应视为 `common shell`，允许进入后续低风险收敛目标：

- workspace collection container
- dashboard shell layout orchestration
- page contract to workspace/runtime adapter glue
- generic empty/loading/error surface handling
- request normalization and response envelope helpers
- generic collection sorting/filtering helper that does not carry industry semantics

判定原则：

- 不直接携带 construction-specific business meaning
- 不决定 financial / approval / settlement semantics
- 主要负责 contract-to-runtime surface assembly

---

## 3. Scenario Block

以下能力当前明确属于 `scenario block`，不得吸收进入 common shell 或 platform kernel：

- construction dashboard business block semantics
- scenario-specific KPI assembly
- industry approval/exception widgets
- cost/payment/settlement/account related block content
- industry-specific action recommendations

判定原则：

- 一旦能力带有行业解释权、领域指标、行业动作建议，它就不再是 common shell
- 即使其最终显示在 dashboard/workspace 中，也仍归 scenario layer 所有

---

## 4. 暂缓收敛

以下区域当前允许继续观察，但不进入 wave-1：

- mixed shell/block files where runtime assembly and scenario semantics are still tightly interleaved
- dashboard descriptors that still carry both generic collection metadata and industry block payload
- block composition utilities without clear ownership split

这些区域的处理顺序必须晚于：

1. request/response helper 收敛
2. generic workspace collection helper 收敛
3. read-model utility inventory 收敛

---

## 5. 对后续代码层的直接约束

后续 wave-1 只允许动以下方向：

- common shell helper extraction
- runtime adapter glue normalization
- generic workspace collection/read-model utility convergence

后续 wave-1 明确不允许：

- scenario block payload restructuring
- dashboard business meaning redefinition
- industry KPI rule consolidation
- payment / settlement / account / approval semantics migration

---

## 6. 结论

- dashboard/workspace 的“壳”可以逐步 commonize
- dashboard/workspace 的“业务块”仍必须留在 scenario layer
- mixed files 先不硬拆，优先抽纯 helper
- 任何不确定 ownership 的区域，一律按 `暂缓收敛` 处理
