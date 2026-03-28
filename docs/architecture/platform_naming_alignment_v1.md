# 平台命名对齐策略 v1

状态：Naming Alignment Baseline  
适用对象：平台内核对齐批次、后续模块演进、文档与任务命名统一

---

## 1. 文档目的

本文档用于解决一个现实问题：

- 目标架构叙事使用 `paas_*` / platform kernel / scenario package 等逻辑命名；
- 当前代码库实际模块名仍然是 `smart_*`。

当前阶段的目标不是立即物理重命名，而是先建立：

1. 逻辑命名体系
2. 当前模块到逻辑命名的映射
3. 未来是否需要 alias / facade / package rename 的判断规则

---

## 2. 当前阶段总策略

### 2.1 结论

当前阶段不做模块物理重命名。

采用两阶段策略：

1. 逻辑命名先对齐
2. 物理模块名后迁移

理由：

- 当前仓库已经有大量 `smart_*` 模块、文档、verify、任务合同和连续迭代资产；
- 直接重命名会把“命名动作”与“能力边界收敛”混在一起，风险高于收益；
- 在平台内核边界尚未冻结完成前，物理重命名会制造伪进展。

---

## 3. 逻辑命名与物理命名区分

### 3.1 逻辑命名

逻辑命名用于：

- 架构文档
- execution baseline
- queue / task 的层级归属
- 长期平台产品化表达

### 3.2 物理模块名

物理模块名用于：

- 现有 Odoo addon 目录
- import path
- manifest / dependency / deployment reality
- 当前 verify 和 automation 入口

规则：

- 当前阶段允许逻辑命名先于物理命名
- 文档必须明确区分“逻辑归属”与“现有模块名”

---

## 4. 当前映射关系

| 当前物理模块 | 当前逻辑归属 |
| --- | --- |
| `smart_core` | 平台内核候选 |
| `smart_scene` | 平台编排/scene runtime 候选 |
| `smart_construction_core` | 通用项目应用 + 行业能力混合体 |
| `smart_construction_scene` | 行业场景资产层候选 |
| `frontend/apps/web` | 前端承接层 |
| `agent_ops` | 自动执行与治理控制平面 |

---

## 5. 当前阶段的命名规则

### 5.1 文档层

允许写法：

- “`smart_core` 当前逻辑归属为平台内核候选”
- “`smart_construction_core` 当前逻辑上是通用项目应用与行业能力混合体”

不允许写法：

- 把当前物理模块直接假装成已经完成的 `paas_*` 新体系

### 5.2 任务层

任务必须写明：

- 当前操作对象的物理模块名
- 当前操作对象的逻辑归属

例如：

- Module: `smart_core`
- Kernel or Scenario: `kernel`

### 5.3 验证层

guard / verify 仍然按当前物理路径执行，不引入虚假 alias 路径。

---

## 6. 是否需要 alias / facade / rename

当前阶段结论：

- 不需要立即物理 rename
- 不需要先做大规模 facade
- 允许在文档和治理层使用逻辑命名做对齐

后续只有在以下条件全部满足时，才允许进入物理 rename 讨论：

1. 平台内核边界已冻结
2. execution baseline 已绑定到 AGENTS / prompts / guard
3. 通用项目应用层边界已明确
4. public contract 与 verify 入口已有 alias 策略

---

## 7. 本轮结论

本轮命名对齐的正式结论是：

- 当前阶段不做模块物理重命名
- 采用“逻辑命名先对齐、代码命名后迁移”的两阶段策略
- 文档、任务、guard 应统一显式区分逻辑归属和物理模块名

---

## 8. 下一步建议

下一张应进入 execution baseline 文档，把这套命名策略和平台边界一起绑定到可执行开发规则中。
