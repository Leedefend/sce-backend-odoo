# UI Base Contract Schema v1

## 标准输入结构（Orchestrator Input）

```json
{
  "scene_key": "projects.list",
  "model": "project.project",
  "view_fact": {},
  "field_fact": {},
  "search_fact": {},
  "action_fact": {},
  "permission_fact": {},
  "workflow_fact": {},
  "validation_fact": {}
}
```

## 子契约字段

### `view_fact`

- `model`: 模型名。
- `view_modes`: 可用视图模式（`tree/form/kanban/search`）。
- `views`: 视图原始语义块。

### `field_fact`

- `model`: 模型名。
- `fields`: 字段元信息映射。

### `search_fact`

- `default_sort`: 默认排序。
- `filters`: 过滤器列表。
- `group_by`: 分组字段列表。
- `fields`: 可搜索字段列表。

### `action_fact`

- `items`: 动作候选列表（从 `actions/toolbar/buttons` 归一化）。

### `permission_fact`

- 权限语义块（有效读写删、可见性、原因码等）。

### `workflow_fact`

- 工作流语义块（`state_field/states/transitions`）。

### `validation_fact`

- 校验语义块（`required_fields/field_rules/record_rules`）。

## 当前代码映射

- 适配器：`addons/smart_core/core/ui_base_contract_adapter.py`
- 运行时挂载：`addons/smart_core/core/scene_ready_contract_builder.py` -> `meta.ui_base_orchestrator_input`

## 约束

- 禁止用整块 `ui.contract` 直接作为“黑箱输入”。
- Scene 编排层只接收上述 7 类 fact。

