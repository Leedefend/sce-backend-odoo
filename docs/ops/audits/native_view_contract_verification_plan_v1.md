# Native View Contract Verification Plan v1

## Verification Objectives
- 防止“支持能力退化”
- 防止“契约 shape 漂移”
- 防止“前端猜测责任回流”

## Verification Items

### V1 Snapshot Suite
- 样本页面 contract 快照（form/tree/kanban/search 各至少 2 个）。
- 存放：`artifacts/contract/native_view_audit/sample_cases/`。

### V2 Semantic Shape Guard
- 校验字段：
  - `semantic_page.layout`
  - `semantic_page.zones[].key`
  - `semantic_page.zones[].blocks[].type`
  - `actions`
  - `permissions`

### V3 Button Semantics Guard
- object/action/stat/smart button shape 必须一致。
- 必须有可执行 verdict 与 reason_code。
- 若存在 `semantic_page.action_gating`，必须包含 `record_state/policy/verdict`。

### V4 Relation/X2many Guard
- relation contract 必须包含：model、view hints、action hints、permission verdict。

### V5 Search/Kanban Coverage Guard
- search filters/group_by 必须存在。
- kanban card fields/grouping hints 必须存在。
- search view 需包含 `semantic_page.search_semantics`（含 quick_filters<=4）。
- search view 需包含 `semantic_page.search_semantics.favorites`（enabled/items 边界）。
- kanban view 需包含 `semantic_page.kanban_semantics`（含 title/card_fields/metric_fields）。

## Recommended Verify Chain
1. `make verify.project.dashboard.contract`
2. `make verify.native_view.semantic_page.shape`
3. `make verify.native_view.semantic_page.schema`
4. `make verify.native_view.semantic_page`
5. 新增：`make verify.native_view.coverage.report`

## Implemented in this branch
- Guard script: `scripts/verify/native_view_semantic_page_shape_guard.py`
- Schema guard: `scripts/verify/native_view_semantic_page_schema_guard.py`
- Snapshot seeds:
  - `docs/contract/snapshots/native_view/semantic_page_project_form_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_tree_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_kanban_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_search_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_form_relation_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_form_x2many_editable_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_form_x2many_readonly_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_form_collab_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_actions_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_tree_kanban_actions_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_permissions_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_search_semantics_v1.json`
  - `docs/contract/snapshots/native_view/semantic_page_project_kanban_semantics_v1.json`

## Reporting
每次迭代输出：
- 覆盖率变化
- 退化项列表
- 阻断级问题（P0）
