# 原生契约驱动的场景编排层消费边界与行业编排落地设计 v1

日期：2026-03-15  
范围：`Scene Orchestrator / UI Base Contract / 行业自定义编排`

---

## 1. 文档目标

本文档用于明确以下关键问题：

1. 场景编排层拿到原生契约（`UI Base Contract`）后应如何消费。
2. 场景编排层对原生契约应使用到什么程度。
3. 哪些内容属于平台层，哪些属于行业自定义编排层。
4. 行业编排如何接入现有链路并形成稳定运行模式。

---

## 2. 当前问题定义

### 2.1 现状

系统已有平台原生契约能力、场景注册与治理能力、前端壳层与渲染能力，但运行时主链仍存在断层：

**`UI Base Contract` 尚未被统一定义为 Scene 编排层的正式输入边界。**

### 2.2 风险

若不钉死边界，容易出现：

- 场景编排层退化为“原生契约搬运层”。
- 前端继续绕过编排层直接消费原生契约字段。
- 行业定制跨层渗透，平台层与行业层再次耦合。

---

## 3. 核心结论

### 3.1 定位

`UI Base Contract` 是编排输入，不是前端最终页面契约。

- 原生契约回答：系统原生能表达什么。
- 编排输出回答：当前用户在当前场景最终应该看到什么。

### 3.2 消费原则

1. 消费原生能力事实，不搬运原生结构。
2. 输出页面可执行语义，不让前端猜。
3. 使用到“足够生成场景”的程度，不追求复刻 Odoo 原生前端所有运行时行为。
4. 行业层可重组/增强/裁剪，但不能篡改原生能力事实。

---

## 4. 编排层对原生契约的输入拆分

编排层应按子契约消费：

- `View Fact`：`views.tree/form/kanban`
- `Field Fact`：`fields`
- `Search Fact`：`search`
- `Action Fact`：`buttons/toolbar`
- `Permission Fact`：`permissions`
- `Workflow Fact`：`workflow`
- `Validation Fact`：`validator`

---

## 5. 按场景类型选吃能力（而非全量透传）

- 列表场景：`tree + search + permissions + actions (+workflow)`
- 表单场景：`form + fields + validator + permissions + workflow + actions`
- 看板场景：`kanban + search + actions + permissions`
- 工作台/驾驶舱：`actions/permissions/search` 子集 + provider 动态聚合数据

编排目标是“选取足够能力形成产品页面”，不是“全量原生透传”。

---

## 6. 编排层输出职责

编排层必须输出标准 `Scene-ready Contract`，而非原生契约裁剪副本。

最小输出：

- `scene`
- `page`
- `zones`
- `blocks`
- `actions`
- `search_surface`
- `workflow_surface`
- `permission_surface`
- `meta`

---

## 7. 行业自定义编排落位

行业层定位：

**基于平台原生能力事实做行业语义重组与产品化增强。**

行业层可做：

- `Scene Profile`（页面结构目标）
- `Block Strategy`（区块策略）
- `Action Policy`（动作策略）
- `Search Policy`（搜索策略）
- `Workflow Policy`（流程策略）
- `Navigation/Workspace/Role Product Policy`

行业层禁止：

- 重新定义底层字段真相。
- 绕过平台权限机制。
- 输出平台外的独立 schema。
- 直接把前端组件名写进契约。

---

## 8. 推荐接入形态：Profile + Policy + Provider

### 8.1 三件套

- `Profile`：场景主结构
- `Policy`：动作/搜索/流程/导航策略
- `Provider`：行业动态聚合数据

### 8.2 运行接线

输入：`scene_key + UI Base Contract + role surface + delivery policy`  
加载：行业 `profile/policy/provider`  
编排：平台 orchestrator 统一 parse/validate/bind/compile  
输出：统一 `Scene-ready Contract`

---

## 9. 编排成熟度分级

- `L0 Registry-only`
- `L1 Seeded Scene`
- `L2 Profiled Scene`
- `L3 Productized Scene`

建议按分级推进，不要求一次性把 100+ scenes 全部做到 L3。

---

## 10. 优先样板场景

建议优先打通 1~2 条完整链路样板：

- `projects.intake`（表单能力主链）
- `projects.list`（列表+搜索+批量动作主链）
- `workspace.home`（provider 编排主链）

---

## 11. 落地实施路线

1. 明确定义 `UI Base Contract` 子契约拆分。
2. 让 `Scene Orchestrator` 正式以子契约作为运行时输入。
3. 定义行业 `Profile + Policy + Provider` schema 与加载规则。
4. 前端仅消费 `Scene-ready Contract`。
5. 验证链增加“输入绑定、输出契约、前端禁直连原生契约”门禁。

---

## 12. 最终原则

**平台原生契约负责“原本能做什么”，场景编排层负责“当前页面最终如何组织能力”，行业编排负责“组织方式如何成为可交付的行业产品页面”。**

