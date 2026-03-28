# Odoo View Structured Parse Gap And Batch-2 Plan v1

状态：Next Capability Batch Plan  
适用对象：平台内核能力补齐批次 2

---

## 1. Why This Batch Exists

当前连续迭代已经把一批 `common provider/config residue` 清理掉，但平台核心能力仍有明显缺口：

- `Odoo native view -> structured contract` 解析链仍然老旧、分散、能力覆盖不足
- `load_view` 入口已经被代理到 `load_contract`，但底层 view parsing 能力没有同步现代化
- 当前 parser 主链仍以 `form` 为中心，`tree/kanban/search/...` 并未形成稳定统一的结构化出口

因此 batch-2 不再继续做 helper cleanup，而是转入：

> 平台核心视图解析能力补齐

---

## 2. Current Chain

当前仓库中的相关主链大致是：

```text
handler/load_view
  -> load_contract mainline
  -> smart_core/view/*
  -> BaseViewParser / ViewDispatcher / UniversalViewSemanticParser
  -> structured payload
```

当前事实：

- `ViewDispatcher` 只稳定支持 `form`
- `FormViewParser` 输出结构偏早期、自定义且不统一
- `UniversalViewSemanticParser` 混合了：
  - raw layout parsing
  - field permission shaping
  - menu/action enumeration
  - dynamic override merge
- `BaseViewParser.get_view_info()` 直接耦合 `model.get_view(...)`

---

## 3. Current Gaps

### 3.1 Coverage Gap

- `form` 之外的原生视图解析缺失或未主线化
- structured output schema 没有明确分层：
  - raw native layout
  - semantic layout
  - permission-enriched layout

### 3.2 Responsibility Gap

- parser、permission、menu/action 元数据、dynamic override 混在同一条链
- `UniversalViewSemanticParser` 职责过宽，不利于平台能力复用

### 3.3 Contract Gap

- 当前输出结构是“可用的自定义对象”，但还不是明确冻结的平台 contract
- 与 `load_contract / ui.contract / scene-ready contract` 的层级关系不够清楚

### 3.4 Upgrade Gap

- 当前链很难演进到：
  - multi-view structured parsing
  - parser registry
  - per-view semantic normalization
  - stable backend contract for frontend native-view reuse

---

## 4. Batch-2 Objective

本批次唯一目标：

> 把 `Odoo native view parsing` 从“单文件/单视图/混职责实现”推进成“可扩展、可注册、可验证的平台解析子系统”。

本批次不做：

- 前端消费改写
- 行业场景 contract 改名
- payment / settlement / account 相关改动
- ACL / security / manifest / migration 改动

---

## 5. Batch-2 Queue

### Step 1

`ITER-2026-03-28-080`

- 目标：产出 current parser inventory + target subsystem design
- 范围：`docs/architecture`, `docs/ops`, `agent_ops`
- 输出：parser inventory / responsibility split / target interfaces

### Step 2

`ITER-2026-03-28-081`

- 目标：实现 parser registry / parse pipeline skeleton
- 范围：`addons/smart_core/view/**`, `addons/smart_core/tests/**`
- 输出：稳定的 parser registry + stage split，不改高风险业务语义

### Step 3

`ITER-2026-03-28-082`

- 目标：把现有 `form` 主链迁移到新 parse pipeline
- 范围：`addons/smart_core/view/**`, `addons/smart_core/tests/**`
- 输出：form parsing 走统一 pipeline，legacy logic 收窄

---

## 6. Target Subsystem

batch-2 目标子系统建议拆成：

- `native_view_source_loader`
  - 负责 `get_view / fields_get` 读取
- `native_view_parser_registry`
  - 负责不同 view type 的 parser 注册
- `native_view_raw_parser_*`
  - 负责 `form/tree/kanban/...` 原始结构抽取
- `native_view_permission_enricher`
  - 负责字段/按钮权限与 groups 可见性
- `native_view_contract_builder`
  - 负责输出稳定 structured contract

重点：

- source loading
- parsing
- enriching
- contract shaping

必须分层，不再混在单个 parser 对象里。

---

## 7. Acceptance Standard

进入代码实现前，必须先能回答：

- parser 的平台真源是什么
- registry 的注册边界是什么
- form parser 迁移后 legacy 逻辑哪些保留、哪些退役
- structured contract 的稳定出口长什么样

任一问题无法回答，本批次不得进入 deeper refactor。

---

## 8. Conclusion

从 `ITER-2026-03-28-079` 开始：

- helper cleanup wave 结束
- 进入 platform core capability batch-2
- 第一焦点固定为：
  - `Odoo native view -> structured contract parsing`

这条线完成后，平台内核才算真正对“原生视图结构化解析”有了一次实质能力提升。
