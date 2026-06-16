# Odoo 表单视图事实与作用域规则

## 核心规则

视图事实必须先按 Odoo 原生机制锁定，再进入契约、低代码和前端。任何改动都必须先回答：这条配置属于模型默认事实、动作入口事实、显式原生视图事实、公司策略，还是用户偏好。

## 四类作用域

| 作用域 | 身份 | 解决的问题 | 不能解决的问题 |
| --- | --- | --- | --- |
| 模型基本视图 | `generic:{model}:{view_type}` | 没有动作上下文时，按 Odoo 默认 view 生成可复建契约 | 不能承载某个菜单/动作的专用字段顺序或结构 |
| 显式原生视图 | `view:{view_id}:{model}:{view_type}` | 调试、迁移、精确绑定某个 `ir.ui.view` | 不能替代动作入口；不能跨模型/跨 view_type |
| 动作专用视图 | `action:{action_id}:{model}:{view_type}:view:{view_id}` | 菜单/动作入口绑定的真实业务页面；字段策略默认应落在这里 | 不能污染模型基本视图；不能通过用户配置改变 |
| 公司字段策略 | `company_id` 过滤叠加 | 同一模型/动作/视图在公司维度的字段显示、隐藏、标签、顺序差异 | 不能改变原生 XML；不能创造页面结构 |

用户个性化不属于结构事实。`user_id` 只能用于偏好层，例如本地列宽、折叠状态、最近使用筛选、草稿输入；不能进入 `app.view.config.projection_scope`、`ui.form.field.policy` 或原生结构投影。

## Odoo 原生机制口径

1. `ir.actions.act_window` 决定业务入口。动作携带 `res_model`、`view_mode`、`views`，其中 `views` 可绑定具体 `ir.ui.view`。
2. `ir.ui.view` 是结构事实来源。Odoo 在运行态合并继承视图，并按用户 groups 裁剪节点。
3. 无动作时，Odoo 按模型和 view type 选择默认视图。
4. 同一个模型可以有多个表单视图；不能把某个动作绑定的 form 当成模型全局默认事实。
5. 用户身份影响权限裁剪和可见性结果，但不产生新的结构事实身份。

## 我们系统的落地规则

### app.view.config

- `projection_scope` 是契约缓存身份，只允许三种格式：
  - `generic:{model}:{view_type}`
  - `view:{view_id}:{model}:{view_type}`
  - `action:{action_id}:{model}:{view_type}:view:{view_id}`
- `source_view_id` 记录原生 view 来源。
- `action_id` 记录动作入口。
- 不允许增加 `user_id` 作为结构缓存维度。

### ui.form.field.policy

- 字段策略是 overlay，不是原生结构。
- 允许维度：`model + field_name + company_id + action_id + view_id`。
- 默认从当前动作入口写入 `action_id`，必要时写入 `view_id`。
- 不允许 `user_id`。用户级字段配置会导致同一业务页面多人看到不同结构，不能作为企业配置。
- 策略只能影响字段级：
  - `visible`
  - `label`
  - `sequence`
  - `group_title` 作为隐藏落位上下文
- 策略不能创建 notebook/page/group 的用户可见结构。

### ui.dynamic.config

- 这是用户/公司偏好 overlay，不能作为结构事实来源。
- 如果保留 `user_id`，只能用于偏好，不得接入表单结构契约主链路。

### 前端

- 路由必须携带动作上下文：`action_id`、必要时 `menu_id`、记录 id。
- 前端不能根据用户偏好发明结构。
- `NativeFormTreeRenderer` 只渲染后端契约给出的原生结构：page 是可见 tab，group 是布局容器。

### 用户偏好发布器

- 用户偏好只能承载已经被用户明确提出的体验差异，例如特定用户版客户/供应商表单三栏平铺、隐藏基础资料维护阶段不办理的字段。
- 用户偏好不能扩展为“所有表单默认三栏”“所有模型字段重排”或通用 `custom_user_default` 覆盖；未被用户明确点名的模型继续由平台/行业/产品线契约治理。
- 用户偏好不能改变产品线字段文案、业务字段顺序、业务状态机、数据口径或权限规则；这些分别归属产品线契约、行业功能、业务模型和权限体系。
- 特定用户版偏好必须绑定到明确业务入口，例如客户/供应商 `res.partner` action；不能以模型主视图、默认视图或全模型扫描作为输入。
- 历史通用用户偏好合同只能被停用清理，不能再次发布为有效合同。

## 冲突处理优先级

字段 overlay 合并时，后进入者覆盖前者：

1. 模型级全局策略。
2. 公司级模型策略。
3. 显式 view 策略。
4. 动作策略。
5. 动作 + view 策略。
6. 同一 scope 内按 `sequence, id` 稳定排序。

动作入口优先于单独 view，是因为用户实际打开的是业务动作；view 只是动作选择出来的原生结构来源。

## 新门禁

```bash
make verify.form_view.scope.boundary_guard
make verify.user_form.preference.boundary_guard
make verify.form_view.scope.action_projection_audit DB_NAME=sc_demo
```

门禁要求：

- `app.view.config` 只存在 generic/view/action 三类 projection scope。
- `app.view.config` 不存在 `user_id` 结构维度。
- `ui.form.field.policy` 不存在 `user_id`。
- 字段策略 source authority 不声明 `res.users`。
- 自定义字段创建只写 `action_id/view_id/company_id`，不写用户 scope。
- 旧 `ui.dynamic.config.user_id` 只能作为偏好 overlay 存在，不能接入结构主链路。
- 动作入口、动作选中的 form view、`app.view.config` 投影 identity、只读投影生成结果必须保持同一个 action/view scope。
- `smart_construction_custom` 用户表单偏好发布器只能发布客户/供应商 `res.partner` 表单偏好，以及用户确认的正式办理入口三栏平铺偏好；正式办理入口必须来自产品线发布的业务分类表单策略，缺失时才允许回退到动作绑定的合成表单结构，并且必须停用历史 `custom_user_default` 通用覆盖。
