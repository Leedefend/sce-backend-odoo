# Domain 字段一致性审计（TP-07 A1）

审计范围：`smart_construction_core` + `smart_construction_seed`

结论：`sc.dictionary` 与 `project.dictionary` 的真实字段为 `type`，当前项目中相关 domain 使用 `type`，无需调整。

核对点（抽样）：
- `project_core.py`：`project_type_id` / `project_category_id` domain 使用 `type`
- `document_center.py`：`doc_type` / `doc_subtype` domain 使用 `type`
- `dictionary_views.xml`：domain 使用 `type`

本轮未进行 domain 字段修改（仅审计）。
