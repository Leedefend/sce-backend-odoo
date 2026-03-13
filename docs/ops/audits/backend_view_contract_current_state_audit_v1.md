# Backend View Contract Current-State Audit v1

## Audit Scope
- Handlers: `load_view`, `load_contract`, `ui_contract`, `api.data`
- Parsers: `view/form_parser.py`, `view/universal_parser.py`, `view/view_dispatcher.py`, `app_config_engine/services/view_Parser/*`
- Assembler: `app_config_engine/services/assemblers/page_assembler.py`

## Key Findings

### 1) 双解析栈并存（能力分裂）
- 栈 A：`load_view -> UniversalViewSemanticParser -> ViewDispatcher`
  - `ViewDispatcher` 当前仅注册 `form`（`addons/smart_core/view/view_dispatcher.py`）
  - 结果：`load_view` 对 tree/kanban/search 无完整统一能力。
- 栈 B：`load_contract -> app.contract.service -> app.view.config -> app.view.parser`
  - 支持 `form/tree/kanban/search/pivot/graph/calendar/gantt/activity/dashboard`
  - 结果：能力更全，但契约 shape 与栈 A 不一致。

### 2) `load_contract` 路径能力相对完整
- `PageAssembler` 能聚合 `fields/views/search/permissions/buttons/toolbar/workflow/reports`
- `app.view.config.get_contract_api` 对 `view_type` 输出分支较完整（含 form/tree/kanban/search 相关）

### 3) 语义层仍不统一
- `load_view` 输出偏 `layout + fields + menus + actions`
- `load_contract` 输出偏 `head/views/fields/search/permissions/buttons`
- 尚未统一到 repo 新规范中的 `native_view + semantic_page + actions + permissions` 形态。

### 4) 前端依赖仍偏向 action contract，而非单一 native semantic contract
- `frontend/apps/web/src/views/ActionView.vue` 仍包含多个 fallback 与推断逻辑。

## Current-State Verdict
- 后端“可用”但“未统一闭环”：
  - `load_contract` 可承载主要页面。
  - `load_view` 仍属于能力短板入口。
  - 缺少统一 semantic page contract 作为单一事实源。

## Immediate Recommendation
1. 保留 `load_contract` 作为主线契约入口。
2. 将 `load_view` 标记为 legacy/diagnostic 或补齐到同一 contract shape。
3. 把 `page/zone/block` 语义层输出提升为通用标准，而非页面特例。
