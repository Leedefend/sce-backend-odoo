# 平台内核对齐实施基线 v1

状态：Execution Baseline  
适用对象：Codex 连续迭代、开发执行、平台内核对齐批次

---

## 1. 文档定位

本文档不是目标蓝图，也不是概念宣言。

它回答的是：

- 当前系统真实可执行的架构基线是什么
- 当前阶段允许做什么，不允许做什么
- Codex 自动迭代应服从哪些边界
- 平台内核对齐批次该如何推进

关联文档：

- `docs/architecture/enterprise_pm_paas_target_architecture_v1.md`
- `docs/architecture/enterprise_pm_paas_implementation_mapping_v1.md`
- `docs/architecture/platform_kernel_current_mapping_v1.md`
- `docs/architecture/platform_kernel_boundary_freeze_v1.md`
- `docs/architecture/platform_naming_alignment_v1.md`

---

## 2. 当前系统架构

当前仓库的真实结构不是一个从零设计的 `paas_*` 平台，而是：

- `smart_core` 作为平台内核主候选
- `smart_scene` 作为编排/runtime 主候选
- `smart_construction_core` 与 `smart_construction_scene` 作为行业层承接
- `frontend/apps/web` 作为前端承接层
- `scripts/verify`、`docs/*`、`agent_ops` 作为治理与审计层

当前主链事实：

```text
frontend
  -> handler / runtime entry
  -> smart_core
  -> smart_scene
  -> scene-ready / contract-ready output
  -> frontend render
```

---

## 3. 核心工程资产

当前阶段已经存在、必须继续复用的工程资产包括：

- contract / scene / runtime 架构文档
- verify / smoke / guard 脚本
- `agent_ops` 连续迭代治理体系
- scene orchestration 与 runtime helper 的逐步收敛链
- 双文档结构：
  - 目标蓝图
  - 实施映射

这些资产优先级高于“为了看起来更平台化而立即重命名或大拆模块”。

---

## 4. 当前阶段边界冻结

### 4.1 平台内核边界

遵守：

- `smart_core` / `smart_scene` 是当前平台内核主候选
- 行业语义不得自动上卷进入 kernel

### 4.2 高风险域冻结

当前阶段不得自动迁移或重写：

- payment
- settlement
- account
- ACL / record rule / security
- manifest / migration

### 4.3 运行时主链冻结

当前阶段允许继续做：

- request normalization helper 化
- response envelope helper 化
- runtime/mainline 低风险收敛

当前阶段不允许做：

- 以“大平台重构”为名改写高风险业务模型
- 把行业 dashboard / workflow 直接卷入 kernel

---

## 5. 开发策略

当前阶段的开发策略是：

1. 先治理基线
2. 再小步收敛
3. 每轮必须可验证
4. PASS 才进入下一轮

具体表现为：

- 文档基线先行
- 任务合同强约束
- 小切片 helper 化优先
- 不做大规模 rename / split

---

## 6. 双轨前端承接策略

当前阶段前端承接明确采用双轨策略：

### 6.1 通用承接优先

- 常规页面优先 contract / metadata 驱动
- 通用 shell / route / contract consumer 继续收敛

### 6.2 特化页面受控存在

- 复杂工作台允许受控场景特化组件
- 但不得把前端特化误写成后端 contract 缺口的长期补丁

---

## 7. Codex 自动迭代体系

Codex 后续连续迭代必须满足：

- 任务先于代码
- execution baseline 先于实现
- kernel/scenario 归属先声明
- PASS_WITH_RISK / FAIL 即停

每轮必须声明：

- Layer Target
- Module Ownership
- Kernel or Scenario
- Reason

---

## 8. 当前阶段产品闭环目标

当前阶段的产品闭环目标不是一次完成整个平台重构，而是：

- 先完成平台内核对齐治理批次
- 再进入代码层通用能力收敛批次
- 在每个批次中保持用户可见或团队可执行的闭环成果

---

## 9. 三阶段实施路线

### Stage 1：平台内核对齐治理

本轮重点：

- current mapping
- boundary freeze
- naming alignment
- execution baseline
- AGENTS / prompts baseline binding
- alignment guard
- status report

### Stage 2：代码层通用能力收敛

仅在 Stage 1 完成后才允许进入：

- metadata / contract utility 提取
- orchestration runtime common layer 提取
- intent / dispatcher common layer 收敛

### Stage 3：通用项目应用层显式化

在平台边界稳定后再进入：

- project/task/stage/milestone 通用层梳理
- industry capability 与 common project capability 分离

---

## 10. 本轮执行规则

当前这轮平台内核对齐批次只允许做：

- 文档
- 任务合同
- prompt / AGENTS / policy 绑定
- 低风险 guard / verify 增强

当前这轮禁止做：

- 核心业务模型重命名
- 大规模 public contract 改名
- 真实多租户实现
- 高风险行业语义迁入 kernel

---

## 11. 下一步建议

完成 execution baseline 后，下一张应把 baseline 正式绑定进 AGENTS / prompts / guard，确保后续连续迭代不再脱离这份实施基线。
