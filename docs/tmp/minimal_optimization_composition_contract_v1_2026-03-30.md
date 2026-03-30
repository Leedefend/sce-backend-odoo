# 最小 Optimization Composition Contract v1（临时）

日期：2026-03-30  
范围：列表页优先，兼顾通用页面编排  
前提：backend native truths 已完整存在

- `search_surface`
- `list_surface`
- `action_surface.batch_capabilities`
- `form_surface`

目标：定义一层**最小** optimization composition contract，只覆盖 Odoo 原生 truth 实质不能完整表达的页面层级与产品编排，不重复 native truths，不把前端临时占位长期固化。

## 一、设计原则

### 1. native truth 优先

optimization composition 不能重复承载以下事实：

- search rows
- list columns
- default sort raw facts
- available view modes
- batch capability truth
- form layout truth

这些继续来自 native truths。

### 2. optimization 只补“组织方式”，不补“能力事实”

它只回答：

- 页面上这些能力如何分区
- 哪些属于高频
- 哪些需要折叠
- 哪些动作应作为主入口
- 是否需要 guidance

它不回答：

- filter 本身是什么
- column 本身是什么
- batch action 能力是否存在

### 3. contract 以最小字段集起步

只允许覆盖 6 类缺口：

- `toolbar_sections`
- `active_conditions`
- `high_frequency_filters`
- `advanced_filters`
- `batch_actions`
- `guidance`

不补更宽泛的 page schema，不补新的 UI DSL。

## 二、整体模型

建议新增一个顶层 additive contract：

```yaml
optimization_composition:
  toolbar_sections: []
  active_conditions: {}
  high_frequency_filters: []
  advanced_filters: {}
  batch_actions: []
  guidance: {}
```

这层是页面编排层，不替代 native truth。

## 三、字段定义

### 1. `toolbar_sections`

作用：

- 定义列表工具栏的 section 顺序与层级

最小字段：

```yaml
toolbar_sections:
  - key: search
    kind: search
    priority: 10
    visible: true
  - key: active_conditions
    kind: active_conditions
    priority: 20
    visible: true
  - key: quick_filters
    kind: filter_collection
    priority: 30
    visible: true
  - key: advanced_filters
    kind: filter_collection
    priority: 40
    visible: true
    collapsible: true
    default_open: false
  - key: grouping
    kind: grouping
    priority: 50
    visible: true
  - key: secondary_metadata
    kind: metadata
    priority: 60
    visible: true
```

说明：

- 这里只定义 section 结构，不重复塞 filters 内容
- section 内容仍引用 native truths 或下方 optimization fields

### 2. `active_conditions`

作用：

- 定义“当前条件区”是否存在，以及哪些条件项允许进入该区

最小字段：

```yaml
active_conditions:
  visible: true
  include:
    - route_preset
    - search_term
    - quick_filter
    - saved_filter
    - group_by
    - sort
  merge_rules:
    route_preset_overrides_search_term: true
```

说明：

- 条件事实仍来自 native truth 和 runtime state
- optimization composition 只决定：
  - 该区是否存在
  - 包含哪些条件种类
  - 是否允许某些条件合并

### 3. `high_frequency_filters`

作用：

- 从 native `filters/searchpanel/default_state` 中挑出高频筛选

最小字段：

```yaml
high_frequency_filters:
  - key: activities_today
  - key: my_projects
  - key: unassigned
  - key: paused
```

说明：

- 这里只给 key，不重复 label/domain/context
- 这些仍从 native `search_surface` 里取

### 4. `advanced_filters`

作用：

- 定义“高级筛选”折叠区

最小字段：

```yaml
advanced_filters:
  visible: true
  collapsible: true
  default_open: false
  source:
    include_remaining_filters: true
    include_searchpanel: true
    include_saved_filters: false
```

说明：

- 高级筛选区是页面组织概念，不是原生事实
- 这里不重复列出所有项
- 只定义剩余材料如何从 native truths 汇入

### 5. `batch_actions`

作用：

- 在 `action_surface.batch_capabilities` 之上，定义页面上应显示哪些批量动作、顺序如何

最小字段：

```yaml
batch_actions:
  - key: archive
    priority: 10
    placement: primary
    requires_selection: true
  - key: activate
    priority: 20
    placement: secondary
    requires_selection: true
  - key: delete
    priority: 30
    placement: secondary
    requires_selection: true
```

说明：

- `can_archive/can_activate/can_delete` 仍来自 native truth
- optimization composition 只决定：
  - 页面上是否暴露
  - 排序
  - 主次落位

### 6. `guidance`

作用：

- 定义列表页顶部的默认引导

最小字段：

```yaml
guidance:
  visible: true
  mode: cards
  entries:
    - key: create_project
      kind: action
      priority: 10
    - key: activities_today
      kind: preset
      priority: 20
    - key: my_projects
      kind: preset
      priority: 30
    - key: unassigned
      kind: preset
      priority: 40
```

说明：

- 这是明确非 native 的产品级引导层
- 应由后端显式给出，而不是前端长期猜

## 四、与 native truths 的边界映射

### native truths 继续负责

- `search_surface`
  - filters
  - group_by
  - searchpanel
  - default_state
- `list_surface`
  - columns
  - hidden_columns
  - default_sort
  - available_view_modes
  - default_mode
- `action_surface.batch_capabilities`
  - can_delete
  - can_archive
  - can_activate
  - selection_required
  - native_basis
- `form_surface`
  - layout
  - header/stat/relation/flags

### optimization composition 只负责

- section hierarchy
- active condition composition
- filter prioritization
- batch action presentation
- user guidance

## 五、前端消费原则

### 1. 先消费 native truths，再消费 optimization composition

顺序应固定为：

1. 读取 native truths
2. 读取 optimization composition
3. 用 optimization composition 组织 native truth 的展示

### 2. optimization composition 缺失时的 fallback

短期允许 fallback，但必须最小化：

- 无 `toolbar_sections`
  - 沿用现有工具栏模板
- 无 `batch_actions`
  - 保持现状，但标记为待回收
- 无 `guidance`
  - 不展示 guidance 区

### 3. 禁止再次前端发明新页面语义

前端不得自己再新增：

- 新的 section key
- 新的 action 分组规则
- 高频筛选推断规则
- guidance 推断规则

## 六、实施顺序建议

### 第一步：后端只补 `toolbar_sections + active_conditions + high_frequency_filters + advanced_filters`

原因：

- 先解决“信息层级混乱”
- 不涉及 batch/guidance，风险最小

### 第二步：前端按新 contract 收回 `PageToolbar` 固定模板

### 第三步：后端补 `batch_actions`

### 第四步：前端回收 `批量归档 / 激活 / 删除` 硬编码

### 第五步：后端补 `guidance`

### 第六步：前端接入 guidance 区并移除旧占位逻辑

## 七、明确不做的事

本版最小 optimization composition contract 不做：

- 新 UI DSL
- 新 page/block/zone 抽象
- 重新定义 list/form/kanban native truths
- 把所有 toolbar 文案下沉成后端完全控制
- 前端视觉细节 contract 化

## 八、结论

后端下一步不该继续“补更多 native truth”，也不该直接上一个很大的页面编排 DSL。

正确做法是：

1. 保持 native truths 作为能力事实基础
2. 只新增最小 optimization composition contract
3. 用这层 contract 回收前端当前的页面层级与批量动作编排

一句话：

> native truth 提供“页面有什么”，optimization composition 提供“页面怎么组织”；  
> 两层都在后端，前端最终只消费。
