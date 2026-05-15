# 表单视图动作投影事实审计

## 审计目标

表单结构必须先落在 Odoo 原生事实上，再进入低代码 overlay。用户实际打开的是菜单动作，所以动作入口、动作选中的 form view、`app.view.config.projection_scope` 必须是同一件事。

## 事实链路

1. 用户菜单解析到 `ir.actions.act_window`。
2. 动作的 `views` 决定 action-scoped form view 身份。
3. `app.view.config._projection_identity()` 生成 `action:{action_id}:{model}:form:view:{view_id}`。
4. 只读投影 `_generate_from_fields_view_get(..., contract_projection_readonly=True)` 必须返回同一个 action/view scope。
5. `ui.form.field.policy` 只能作为字段级 overlay 叠加在 `model/action_id/view_id/company_id` 上，不能重新定义页面结构。

## 层级边界

| 层 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| Odoo 原生视图 | XML arch、继承合并、groups 裁剪、动作选 view | 低代码字段标签、企业字段顺序策略 |
| `app.view.config` | 原生视图到契约结构的可复建投影身份 | 用户专用结构、业务事实回填 |
| `ui.form.field.policy` | 字段显示、标签、顺序、落位上下文 | notebook/page/group 的用户可见结构 |
| 前端 | 渲染后端契约，提交当前 action/view 上下文 | 自行发明结构或字段 scope |

## 新门禁

```bash
make verify.form_view.scope.action_projection_audit DB_NAME=sc_demo
```

门禁抽取业务用户可见菜单动作样本，并逐条检查：

- 动作 form view 推导出的 scope 必须是 `action:{action_id}:{model}:form:view:{view_id}`。
- `_projection_identity()` 的 action/view/scope 必须与动作一致。
- 只读生成的 `app.view.config` transient 记录必须与动作一致。
- 审计报告写入 `docs/audit/native/form_view_scope_action_projection/`，包含 `README.md`、`summary.json`、`rows.csv`。

这条门禁补齐了“动作专用、模型基本视图、用户专用偏好”边界的运行态证据，避免后续低代码入口把某个动作页面误写成模型全局结构。
