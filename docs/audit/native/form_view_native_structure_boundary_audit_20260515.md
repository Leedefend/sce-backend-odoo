# 表单视图结构与 Odoo 原生对齐专题审计

## 结论

本轮审计确认：表单结构链路已经具备原生 arch、Unified Page Contract v2、前端 NativeFormTreeRenderer、低代码字段策略四段能力，但旧门禁把“契约层补齐结构”当成成功口径，允许系统自动生成“主信息 / 业务明细 / 来源追溯 / 备注说明”等用户可见标题。这与 Odoo 原生表单不一致，也是低代码配置入口开始混乱的根因。

新的边界口径是：语义可以补到契约元数据，不能自动变成用户可见结构。用户可见的页签名称只能来自原生 `notebook/page` 或明确的业务视图设计；普通 `group` 名称不展示。

## 全链路边界

| 层 | 允许解决的问题 | 不允许做的事 | 门禁 |
| --- | --- | --- | --- |
| Odoo 原生 XML / 运行态 arch | 提供真实 `sheet/group/notebook/page/field/button/chatter` 结构；业务上确实需要页签时在 XML 或专门配置里定义 page 名称 | 让前端猜业务结构；把技术 group 名当用户文案 | 运行态结构审计 |
| 后端契约组装 | 保留原生结构；给无标题 group 添加 `semanticTitle/semanticAnchor/sourceAuthority` 作为机器可读元数据 | 自动生成“主信息 / 业务明细”等可见 notebook/page；把推断语义写入 `title/label/string` | `verify.form_view.native_structure.boundary_guard` |
| 字段策略 / 低代码 | 调整字段顺序、显隐、显示名；新增字段落到隐藏的原生上下文或明确用户操作上下文 | 暴露技术分组选择；通过字段策略发明页面结构 | `verify.form_view.native_structure.boundary_guard` |
| 前端 NativeFormTreeRenderer | 按原生结构渲染：page 显示为 tab，group 只负责布局；低代码控件就地出现 | 展示 group 标题；把 `semanticTitle` 当用户标题；在页面底部堆配置表单 | `verify.form_view.native_structure.boundary_guard` + 浏览器验收 |

## 已确认缺口

1. 后端 `business_form_default_tab_standardizer` 曾把没有 notebook 的业务表单自动包成“主信息 / 业务明细 / 来源追溯 / 备注说明”页签。该行为会把推断结构变成用户可见结构，已改为不再投影可见默认页签。
2. 后端 `business_form_semantic_label_standardizer` 曾把推断出的 group 语义写入 `title/label/string`。这会被前端误当可见标题，已改为只写 `semanticTitle/semanticAnchor/sourceAuthority`。
3. 前端已经按原生口径隐藏 group 标题，但仍需要保留隐藏 group 名作为低代码新增字段的落位上下文，因此门禁要求 `containerTitle(group) == ""` 且 `field-group-title` 使用 `containerPolicyTitle(node)`。
4. 低代码新增字段入口不应再出现“分组”选择，也不应在页面底部追加难以理解的配置表单；新增字段以当前字段后方的 `+` 触发明确弹窗。

## 处置规则

- 如果问题是“用户看到了不该看的结构标题”：优先查前端是否展示了 group 标题，其次查后端是否把推断语义写入了 `title/label/string`。
- 如果问题是“用户需要看到页签”：优先在原生 XML 或明确业务视图配置中定义 `notebook/page`，不要由契约层用通用名称猜。
- 如果问题是“新增字段落位不对”：由低代码字段策略处理 `group_title/sequence/afterFieldKey`，但 UI 不暴露技术分组。
- 如果问题是“业务字段缺失或标签不对”：由字段策略或业务模型/视图层处理，前端只消费契约。
- 如果问题是“前端显示结构与原生不同”：由 `NativeFormTreeRenderer` 修渲染规则，不允许后端为了前端问题改业务 XML。

## 新门禁

新增门禁：

```bash
make verify.form_view.native_structure.boundary_guard
make verify.form_view.scope.boundary_guard
```

并已挂入：

```bash
make verify.form_structure.contract
```

门禁覆盖：

- 后端不得投影通用可见 notebook/page。
- 后端自动语义不得写入 group 的 `title/label/string`。
- 视图事实身份只能是模型默认、显式原生 view、动作绑定 view；用户个性化不得进入结构 scope。
- 前端必须隐藏 Odoo group 标题。
- 前端必须保留隐藏 group 上下文用于低代码落位。
- 新增字段弹窗不得暴露“分组”配置项。

## 后续审计重点

- 对真实 prod-sim 登录路径补浏览器截图验收：原生 group 不显示标题，原生 page 显示 tab。
- 对字段策略产生的新增字段做数据清理/来源标记，避免测试字段直接进入用户表单。
- 将运行态审计报告里的 `contract_auto_with_default_tabs` 分类改名为“需显式页签设计”，避免再次鼓励契约层自动造可见页签。
