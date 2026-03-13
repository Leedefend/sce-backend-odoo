# Native View Sample Audit Cases v1

## Sampling Strategy
覆盖 8 类样本：simple form / notebook form / button_box form / chatter form / x2many form / tree / kanban / search。

## Sample Cases

### Case 1: `project.project` form (complex)
- Native traits: header, groups, notebook, x2many, chatter
- Backend path tested: `load_contract` + `app.view.parser`
- Result: Partial-pass
  - Header/group/notebook/chatter 可输出
  - `semantic_page` 仍未统一标准输出

### Case 2: `project.project` tree
- Native traits: columns/order/search binding
- Result: Pass (contract level)
  - `columns/order` 存在
  - list-level row semantics 需要统一 reason/permission 输出

### Case 3: `project.project` kanban
- Native traits: card fields/grouping/quick_create
- Result: Partial-pass
  - `kanban` block 输出存在
  - card semantic extraction 尚不稳定（仍需增强模板语义映射）

### Case 4: project search view
- Native traits: filters/group_by/context/domain
- Result: Partial-pass
  - filters/group_by 有输出
  - searchpanel/favorite 边界未形成统一契约说明

### Case 5: `load_view` form via `UniversalViewSemanticParser`
- Result: Pass (form only)

### Case 6: `load_view` tree/kanban/search
- Result: Fail
  - 根因：`ViewDispatcher` 仅支持 `form`

### Case 7: button execution semantics
- Path: `execute_button` + action contract
- Result: Partial-pass
  - 执行通路在
  - 按钮可执行性判定与 UI 契约仍有分散

### Case 8: relation/x2many in form
- Result: Partial-pass
  - 有 subviews 输出
  - relation zone/block 语义分区未统一

## Evidence Files
- `docs/ops/audits/native_view_audit_sample_cases/case_01_project_form.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_02_project_tree.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_03_project_kanban.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_04_project_search.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_05_load_view_form_only.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_06_load_view_non_form_gap.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_07_button_semantics.json`
- `docs/ops/audits/native_view_audit_sample_cases/case_08_relation_x2many.json`

注：运行时可同时落到 `artifacts/contract/native_view_audit/sample_cases/` 作为临时证据目录。
