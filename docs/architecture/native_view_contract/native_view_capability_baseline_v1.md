# Native View Capability Baseline v1

## Scope
- Layer Target: `Page Orchestration Layer`
- Module: `addons/smart_core`, `addons/smart_construction_core`
- Reason: 定义“后端契约完整解析”目标基线，作为后续缺口审计标准。

## Baseline Definition
“完整解析”指后端可将 Odoo 原生视图（form/tree/kanban/search）稳定输出为可执行契约，且前端无需猜测结构和行为。

## Baseline Checklist

### A. Form
- Header（object/action buttons）
- Button box / stat buttons
- Sheet / group / subgroup
- Notebook / pages
- Field attributes（string/widget/help/placeholder/options）
- Modifiers（readonly/required/invisible）
- Domain/context
- x2many subview contract
- Chatter（followers/activity/messages）
- Ribbon
- Statusbar
- Permission/state gating（可见/可编辑/可执行 + reason）

### B. Tree
- Column order（与原生一致）
- Column modifiers
- Widget/decorations
- Editable mode
- Row actions
- Batch actions
- Toolbar actions

### C. Kanban
- Card semantic fields
- Grouping field
- Quick actions
- Badge/tag/progress hints
- Drag/drop capability hints

### D. Search
- Filters
- Group-by
- Search panel
- Search fields
- Domain/context mapping
- Favorites boundary（能力边界说明）

## Contract Shape Baseline (target)
```json
{
  "meta": {},
  "native_view": {},
  "semantic_page": {
    "layout": "two_column",
    "header": {},
    "zones": [{"key": "detail_zone", "blocks": []}]
  },
  "record": {},
  "permissions": {},
  "actions": {}
}
```

## Completion Criteria
1. 四类视图均有稳定契约输出。
2. 同一能力在不同入口（`load_view`/`load_contract`/`ui.contract`）无冲突。
3. 前端不需要对标题字段、按钮类型、zone 分区做特判猜测。
