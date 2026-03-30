# Native Truth 对剩余页面需求的覆盖审计（临时）

日期：2026-03-30  
范围：列表页优先，兼顾通用页面编排  
前提：后端已补齐四层 native truth

- `search_surface`
- `list_surface`
- `action_surface.batch_capabilities`
- `form_surface`

目标：明确剩余页面需求中，哪些已经能由后端原生 truth 表达，哪些只能部分表达，哪些本质上不属于 Odoo 原生事实，后续才需要补 optimization composition contract。

## 一、结论摘要

当前不应再笼统说“页面编排都缺后端 contract”。

更准确的结论是：

1. **页面基础结构与能力面**
   - 现在已经基本具备后端原生 truth 表达能力
   - 前端后续应逐步回收本地推导，只消费后端 surface

2. **页面层级优先级与产品引导**
   - 仍不能仅从 Odoo 原生信息完整推出
   - 这部分才是真正的 optimization composition 范围

一句话：

> 剩余工作不再是“继续补原生能力面”，而是先把前端还在自己组织的部分收回到已存在 native truths；  
> 只有原生 truths 实质不表达的页面优先级、引导与动作分组，才需要后端新增 optimization composition。

## 二、审计口径

本审计按三类判定：

- **A. 已可由 native truth 表达**
  - 不应再让前端自行决定
- **B. 仅可部分由 native truth 表达**
  - 原生能给能力事实，但不能给最终页面组织优先级
- **C. 原生实质不能表达**
  - 后续必须由后端 optimization composition contract 补

## 三、当前可用的 backend native truths

### 1. `search_surface`

当前已具备：

- `filters`
- `group_by`
- `searchpanel`
- `default_state`

可表达：

- 当前 action 提供了哪些筛选
- 哪些是默认激活状态
- searchpanel 是单选还是多选
- 默认分组和默认筛选

### 2. `list_surface`

当前已具备：

- `columns`
- `hidden_columns`
- `default_sort.raw`
- `default_sort.field`
- `default_sort.direction`
- `default_sort.display_label`
- `available_view_modes`
- `default_mode`

可表达：

- 列表有哪些列
- 哪些列默认隐藏
- 默认排序是什么
- 默认显示模式是什么
- 同一 action 能否切 tree/kanban/form

### 3. `action_surface.batch_capabilities`

当前已具备：

- `can_delete`
- `can_archive`
- `can_activate`
- `selection_required`
- `native_basis`

可表达：

- 批量删除/归档/激活是否在能力上可行
- 是否要求 selection
- 这些能力的原生依据

### 4. `form_surface`

当前已具备：

- `layout`
- `header_actions`
- `stat_actions`
- `relation_fields`
- `field_behavior_map`
- `flags`

可表达：

- form/header/notebook/page/group/field 结构
- stat/button box 能力
- relation field 与字段行为事实
- native form flags

## 四、剩余页面需求覆盖矩阵

### 1. 搜索区

判定：**A. 已可由 native truth 表达**

理由：

- 搜索能力来源已可由 `search_surface` 表达
- searchable/searchpanel/filter/group_by/default_state 的能力事实已具备
- 前端不应继续自己拼“哪些是搜索材料”

后续动作：

- 前端改为只消费 `search_surface`
- 不再从零散字段、preset、旧 fallback 推导搜索层

### 2. 当前筛选条件区

判定：**B. 仅可部分由 native truth 表达**

native truth 已能表达：

- 当前默认筛选状态
- 当前 route preset
- 当前 group by
- 当前默认排序

native truth 还不能直接表达：

- 页面是否要单独存在一个“当前条件区”
- 当前条件项按什么视觉优先级展示
- 哪些条件应合并、哪些条件应单独保留

结论：

- 条件事实本身已足够由后端给出
- “当前条件区”作为独立页面层级，属于 optimization composition

### 3. 快速筛选

判定：**B. 仅可部分由 native truth 表达**

native truth 已能表达：

- 所有 filters
- 默认 filters
- searchpanel 单选/多选

native truth 不能稳定表达：

- 哪些 filter 属于高频
- 页面上应只保留哪 5 个
- 哪些 filter 应提升为快速筛选

结论：

- filter 集合是 native truth
- “快速筛选”是 optimization composition

### 4. 高级筛选（折叠）

判定：**C. 原生实质不能表达**

理由：

- 原生能给完整 filters/searchpanel/group_by 集合
- 但“其余全部折叠到高级筛选”是页面组织决策
- 是否折叠、默认开合、折叠层里的分组方式，都不是原生事实

结论：

- 必须由后端 optimization composition contract 补：
  - `advanced_filters`
  - `section_collapsible`
  - `section_default_open`

### 5. 分组区

判定：**A/B 之间，偏 A**

native truth 已能表达：

- `search_surface.group_by`
- `list_surface.available_view_modes`
- `list_surface.default_mode`

还不能完整表达：

- 分组区在页面上是否独立成层
- 分组与筛选谁先谁后

结论：

- 分组能力面已是 native truth
- 分组区的位置和层级仍是 optimization composition

### 6. 推荐筛选

判定：**B. 仅可部分由 native truth 表达**

native truth 已能表达：

- route preset
- 默认筛选
- 默认进入状态

不能完整表达：

- 推荐筛选是否应单独成区
- 推荐筛选是否等于默认 preset
- 推荐筛选是否作为“用户建议入口”展示

结论：

- preset/default facts 可来自 native truth
- “推荐筛选区”本身是 optimization composition

### 7. 默认引导与“下一步做什么”

判定：**C. 原生实质不能表达**

理由：

- 原生 action/view/search 不会给：
  - “创建新项目”
  - “查看今日活动项目”
  - “处理未分派任务”
  这类产品任务引导

结论：

- 必须由后端新增 guidance / entry contract

### 8. 主操作区 / 次级操作区

判定：**C. 原生实质不能表达**

native truth 已能表达：

- action/button/toolbar 的动作集合
- batch capability facts

不能完整表达：

- 哪些动作是 primary
- 哪些动作应进入 secondary
- 导出/刷新/清空条件应如何分区

结论：

- 动作事实已具备
- 动作分组和页面落位必须由 optimization composition 补

### 9. 批量操作显示规则

判定：**B. 仅可部分由 native truth 表达**

native truth 已能表达：

- `can_delete`
- `can_archive`
- `can_activate`
- `selection_required`

不能完整表达：

- 批量区是否默认显示
- 批量动作的主次顺序
- 哪些动作在当前页面应暴露给用户

结论：

- 能力 truth 已具备
- batch action composition 仍需要后端 optimization contract

### 10. 列表重点视觉

判定：**B/C 之间，偏 C**

native truth 已能表达：

- 列
- semantic roles 的一部分候选
- 默认排序

不能完整表达：

- 哪一列必须成为主视觉
- 状态 badge 的色彩策略
- 哪些字段在列表行中应突出
- 整行点击 affordance 如何设计

结论：

- 这是前端展示层和优化编排的结合问题
- 不属于纯 native truth 的完整可提取范围

## 五、按优先级整理的后续责任边界

### 第一优先级：先回收前端对已存在 native truths 的重复推导

这部分不该再补后端新 contract，而应让前端改成只消费：

- `search_surface`
- `list_surface`
- `action_surface.batch_capabilities`
- `form_surface`

典型回收对象：

- 列表页自己推 searchable fields / default sort / view modes
- 列表页自己推 batch capability
- 详情页自己兜布局结构

### 第二优先级：仅为“原生不能完整表达”的部分新增 optimization composition

最小必要集合：

- `toolbar_sections`
- `active_conditions`
- `high_frequency_filters`
- `advanced_filters`
- `batch_actions`
- `primary_actions`
- `secondary_actions`
- `guidance`

### 第三优先级：前端只做展示，不承担长期页面编排

前端仍可做：

- 视觉布局
- 样式收口
- 交互触发

前端不应长期承担：

- 页面层级定义
- 动作主次编排
- filter 高频/高级分层
- guidance 语义决策

## 六、结论与下一步

当前最重要的结论不是“后端还要补很多”，而是：

- **基础原生事实已经足够支持大量页面能力**
- **现在真正需要后端新增 contract 的，只是原生无法完整表达的优化编排层**

因此下一步正确顺序应是：

1. 先做一轮前端消费边界收正审计
   - 识别哪些地方仍在重复推 native truths
2. 再定义最小 optimization composition contract
   - 只覆盖：
     - 工具栏层级
     - 高频/高级筛选分层
     - batch action composition
     - guidance
3. 最后前端切到“native truth + optimization composition”双输入消费

一句话：

> 后端下一步不该继续泛化补 contract，而应只补“原生 truth 无法表达”的最小优化编排层；  
> 前端下一步不该继续自己编排，而应开始回收对 native truths 的重复推导。
