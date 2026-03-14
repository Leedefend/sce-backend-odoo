# 原生视图复用驱动的前端页面设计规范 v1

## 1. 文档目标

本规范用于统一自定义前端页面设计方法：以 Odoo 原生视图作为基础结构来源，后端负责语义解释，前端负责通用渲染，场景层负责产品化增强。

适用范围：
- Odoo 后端视图解析层
- 通用前端渲染层
- 页面场景编排层
- 产品化增强层

## 2. 核心设计思想

页面主路径固定为：

`Odoo 原生视图定义结构 -> 后端解析与语义提升 -> 前端按统一契约渲染 -> 场景层增强编排`

要求：
- 基础页面骨架定义权优先归属原生视图
- 前端禁止“再造一套页面结构”

## 3. 总体原则

### 3.1 原生结构优先
原生已定义结构，前端不得重复定义，包括：字段顺序、group/notebook、header/button box、chatter、modifiers、x2many、tree/form/kanban基础结构。

### 3.2 后端解释优先
前端不解析 XML，不推理业务语义。后端必须输出结构标准化、权限与状态解释、按钮行为、页面推荐布局。

### 3.3 通用渲染优先
优先补通用渲染器能力，不优先写页面特例：List/Form/Kanban/Search/Header/Relation/Block 渲染器。

### 3.4 产品增强外挂
AI 建议、风险预警、下一步动作等增强能力必须通过 zone/block 扩展注入，不得侵入基础渲染器。

### 3.5 一致性优先
同一业务对象在 Odoo 与自定义前端必须语义一致：字段顺序、按钮语义、状态口径、权限结果不得冲突。

## 4. 页面四层模型

### 4.1 原生定义层（Native View Layer）
来源：Odoo view arch + fields + modifiers + inheritance 合并结果。

### 4.2 结构标准化层（Normalized Structure Layer）
后端统一输出：`view_type/fields/header/button_box/notebook/relations/chatter/search_panel/toolbar_actions`。

### 4.3 页面语义层（Semantic Page Layer）
后端语义提升输出：`zone + block`。

建议 zone：
- `header_zone`
- `summary_zone`
- `detail_zone`
- `relation_zone`
- `action_zone`
- `collaboration_zone`
- `insight_zone`
- `attachment_zone`

建议 block：
- `title_block`
- `status_block`
- `action_bar_block`
- `field_group_block`
- `notebook_block`
- `relation_table_block`
- `stat_button_block`
- `chatter_block`
- `attachment_block`
- `risk_alert_block`
- `ai_recommendation_block`
- `next_action_block`

### 4.4 产品编排层（Product Orchestration Layer）
场景层按角色/场景做展示编排，不修改基础结构语义。

## 5. 页面设计流程

1) 先审原生视图是否可承载基础结构；可承载则禁止重画基础页面。

2) 前端“做不出来”时优先补后端解析输出：语义、modifiers、x2many、按钮行为、分区映射。

3) 前端唯一输入为语义契约：`page/zones/blocks/fields/actions/permissions/ui_hints`。

4) 仅高价值页面做编排增强，普通页面优先通用渲染。

## 6. 后端职责与禁令

### 后端必须输出
- 视图基础定义
- 结构化页面定义
- 字段行为修饰（readonly/required/invisible/domain/context/widget）
- 行为定义（object/action/stat/smart/button）
- 权限与状态解释（可见/可编辑/可执行/不可执行原因）

### 后端禁止
- 将原始 XML 直接下发给前端并要求前端解释业务语义
- 仅返回字段列表并把页面结构责任推给前端
- 同一页面出现多套冲突结构来源

## 7. 前端职责与禁令

### 前端核心职责
- 骨架渲染
- 通用组件映射
- 交互反馈
- 输入管理
- 提交刷新
- 状态展示
- 增强区插槽渲染

### 前端禁止
- 解析 Odoo XML
- 推断权限与按钮可执行性
- 推断业务分区
- 手工改写与原生冲突的字段顺序
- 复刻后端业务规则

## 8. 页面类型规范

### 列表页
复用 tree/search 结构；支持列顺序、过滤、分组、批量操作、分页、状态面板。除产品编排明确要求外，不得手工重排基础列语义。

### 表单页
以 form 为结构源；支持 header/stat/group/notebook/x2many/chatter/modifiers。可美化布局，不得破坏业务结构顺序。

### 看板页
复用 kanban 语义（标题/状态/摘要/动作）。产品增强需基于原始卡片语义，不得重造卡片定义。

### 搜索区
以 search view 为过滤结构来源，前端不得构造与后端不一致的筛选逻辑。

## 9. 产品增强规范

增强能力通过扩展配置注入（scene orchestration / page extension / capability injection），不侵入基础渲染器。

增强层边界：
- 不改写原生字段业务含义
- 不越过后端权限判断
- 只能加语义，不可篡改地基

## 10. 开发治理

### 新页面检查单
1. 原生视图是否可承载基础结构？
2. 后端解析是否输出完整语义？
3. 当前需求属于通用能力还是产品增强？
4. 是否必须做页面特例？
5. 是否破坏通用渲染体系？

### 实施优先级
1. 后端结构解析
2. 前端通用渲染器
3. 语义编排层
4. 产品增强层
5. 页面特例

### 特例准入条件
- 通用渲染不能覆盖核心表达
- 页面高频高价值
- 不破坏通用契约
- 可抽象为可复用模式

## 11. 建议契约输出方向

```json
{
  "meta": {},
  "native_view": {},
  "semantic_page": {
    "layout": "two_column",
    "header": {},
    "zones": [
      {"key": "summary_zone", "blocks": []}
    ]
  },
  "record": {},
  "permissions": {},
  "actions": {}
}
```

必须同时具备：
- 原始来源可追溯
- 语义层可渲染
- 行为层可执行
- 权限层可解释

## 12. 当前阶段执行要求（强制）

从本规范落库起，后续迭代默认遵守以下硬约束：

1. 新页面先做“原生可承载性检查”，再做前端开发。
2. 页面结构问题优先补后端语义输出，不先写前端特判。
3. 前端页面以语义契约为唯一结构输入。
4. 页面特例必须在迭代说明中写明准入理由与退出条件。

## 13. 一句话口径

基础页面由 Odoo 原生视图定义，后端解释为统一语义结构，前端通用渲染，高价值场景再做产品增强。

