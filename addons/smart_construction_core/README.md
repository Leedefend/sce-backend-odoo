# Smart Construction Core

## 兼容模型说明

- 由于早期版本使用过 `project.budget.line`，为了保证老数据库升级安全，在 `models/budget_compat.py` 中保留了一个兼容模型：
  - `_name = 'project.budget.line'`
  - `_table = 'project_budget_boq_line'`
- 该模型只用于 ORM 元数据兼容，**不要在新代码中引用**。新代码一律使用 `project.budget.boq.line`。
