# 通用项目应用层候选清单 v1

状态：Code Alignment Entry Baseline  
适用对象：平台内核代码层收敛批次、通用项目应用层显式化

---

## 1. 文档目的

在平台内核对齐治理批次完成后，下一步不能直接做“大拆模块”。

必须先回答：

- 当前哪些能力更像“通用项目应用层”
- 哪些能力仍然是行业语义
- 哪些能力适合先做低风险代码层收敛

本文档的作用，就是给下一轮代码层对齐提供一张明确的候选地图。

---

## 2. 候选能力

以下能力当前应优先视为“通用项目应用层候选”，而不是直接归入平台内核或继续埋在行业模块里：

### 2.1 project / task / stage / milestone 通用能力

候选原因：

- 这些能力并不天然依赖 construction-specific 财务语义
- 具备跨行业复用潜力
- 更适合作为“common project layer”，而不是 platform kernel 本体

### 2.2 project dashboard / workspace 通用骨架

候选原因：

- dashboard shell、workspace collection、通用 page contract 更偏向通用项目应用层
- 但 dashboard 上的行业块内容仍应留在 scenario 层

### 2.3 project context / role / stage read model utilities

候选原因：

- 这类能力常作为多个项目场景的共享基础
- 只要不携带 payment / settlement / account 语义，就适合先做低风险收敛

---

## 3. 暂不迁移

以下内容当前明确暂不进入通用项目应用层收敛：

- payment request
- settlement order
- cost / treasury / account specific semantics
- construction-specific approval policy
- 行业特有 dashboard block 业务语义

这些内容仍属于行业层或高风险语义域。

---

## 4. 低风险优先

下一轮代码层对齐，只允许优先处理：

- request normalization helper
- response envelope helper
- read model utility
- 通用 page / collection / workspace helper
- 不携带行业语义的 dashboard shell / runtime helper

不允许优先处理：

- 高风险业务模型
- 财务与权限语义
- 大规模模块迁移

---

## 5. 下一步建议

下一张任务应围绕以下方向之一展开：

1. 通用 project/workspace read-model utility inventory
2. project dashboard shell 与行业 block 的边界识别
3. common project layer 的低风险 helper 候选抽取

结论：

- 先识别 common project candidate
- 再做低风险代码层收敛
- 不直接跳入大规模平台/行业拆分
