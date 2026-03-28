# Native View Parser Inventory v1

状态：Batch-2 Step 1 Artifact  
适用对象：`platform_core_view_parse_batch_2`

---

## 1. Purpose

本文档盘清当前 `Odoo native view -> structured data` 解析链的真实实现、职责混合点和下一步可收敛的子系统边界。

它服务于：

- `ITER-2026-03-28-080`
- `ITER-2026-03-28-081`
- `ITER-2026-03-28-082`

---

## 2. Current Entry Chain

当前相关入口链是：

```text
load_view
  -> load_contract mainline
  -> smart_core/view/*
  -> BaseViewParser / ViewDispatcher / UniversalViewSemanticParser
  -> structured payload
```

关键事实：

- `load_view` 已经是兼容入口，不应再成为 parser 架构真源。
- `smart_core/view/*` 仍然保留独立解析栈。
- 当前 parser 栈与 `load_contract / ui.contract` 的平台 contract 边界还不够清楚。

---

## 3. Current Components

### 3.1 `addons/smart_core/view/base.py`

当前职责：

- env 获取
- `model.get_view(...)` 调用
- `arch` XML 转换
- 字段名提取
- context 安全解析

问题：

- source loading 与 parsing base 混在一起
- `request/env` 获取逻辑放在 parser 基类中，导致 loader 与 parser 不分层

### 3.2 `addons/smart_core/view/view_dispatcher.py`

当前职责：

- `view_type -> parser class` 分发

问题：

- 只支持 `form`
- 还不是一个正式的 parser registry

### 3.3 `addons/smart_core/view/form_parser.py`

当前职责：

- 从 form XML 中提取 title/header/stat/ribbon/group/notebook/chatter

问题：

- 输出结构是历史定制 shape，不是正式冻结的平台 contract
- 条件表达式、字段节点、group/notebook 解析都只在 form parser 内部局部存在
- 无法共享给 tree/kanban 等类型

### 3.4 `addons/smart_core/view/universal_parser.py`

当前职责：

- 调 dispatcher
- 解析 model 权限
- 解析字段权限
- 合并字段标签
- 应用按钮/groups 可见性
- 枚举菜单与动作
- 动态覆盖合并

问题：

- 职责过宽
- parsing / permission / auxiliary metadata / override merge 混在一个对象里
- 不适合成为平台级稳定子系统

### 3.5 `addons/smart_core/handlers/load_view.py`

当前职责：

- 作为 compat alias，代理 `load_contract`

结论：

- 不是 parser 真源
- 应继续保持 compat 薄壳，不应再向其中回灌解析能力

---

## 4. Responsibility Split Problems

当前最主要的问题不是“缺少一个 parser 文件”，而是责任层次不清：

### A. Source Loading

- 负责 `get_view / fields_get / view_id / context` 的统一读取

现在位置：

- `BaseViewParser`
- `UniversalViewSemanticParser`

### B. Raw Parse

- 负责把 `arch` 变成结构化节点

现在位置：

- `FormViewParser`

### C. Permission Enrichment

- 负责 read/write/create/unlink
- 字段 groups
- 按钮 visible/editable

现在位置：

- `UniversalViewSemanticParser`

### D. Auxiliary Metadata

- menus
- actions
- dynamic overrides

现在位置：

- `UniversalViewSemanticParser`

问题在于：

> 当前系统把 A/B/C/D 四层揉成了一条 parser 链，导致任何能力升级都会变成大文件高风险改动。

---

## 5. Target Subsystem Split

batch-2 建议目标拆分如下：

### 5.1 `native_view_source_loader`

职责：

- 统一读取 `get_view / fields_get`
- 提供标准 source payload：
  - model
  - view_type
  - view_id
  - arch
  - fields

### 5.2 `native_view_parser_registry`

职责：

- `view_type -> parser`
- 显式支持：
  - form
  - tree
  - kanban
  - search

### 5.3 `native_view_raw_parser_form`

职责：

- 只负责 form raw parse
- 不做权限和动态覆盖

### 5.4 `native_view_permission_enricher`

职责：

- model 权限
- field/button groups 可见性
- readonly/editable enrichment

### 5.5 `native_view_contract_builder`

职责：

- 生成稳定 structured contract
- 让 frontend/native-view reuse 消费有统一出口

---

## 6. Batch-2 Implementation Order

### Step 1

冻结 inventory 和目标拆分。

### Step 2

引入 registry + loader + pipeline skeleton。

### Step 3

把现有 form parser 挂到新 pipeline 上，legacy 逻辑收窄。

---

## 7. Do Not Touch

此批次明确不做：

- frontend 页面消费改写
- industry scene payload 重写
- ACL/security/payment/account/settlement
- `load_view` compat 语义改写

---

## 8. Immediate Conclusion

下一张代码任务不该再抽 helper，而应直接建立：

- `native_view_parser_registry`
- `native_view_source_loader`

这是当前平台核心在“原生视图结构化解析”上最缺、也最值得先补的能力入口。
