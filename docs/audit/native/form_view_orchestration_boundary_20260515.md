# 表单视图编排层边界审计

## 结论

当前矛盾不是“要不要借用 Odoo 原生视图”，而是“借用后谁有权决定最终业务视图”。Odoo 原生视图必须借用，解析也必须保留；但解析结果不能直接成为最终用户可见结构。缺失的是一个独立的表单业务编排层。

## 当前事实

| 层 | 当前事实 | 证据文件 | 判断 |
| --- | --- | --- | --- |
| Odoo 原生视图输入 | `get_view` / `fields_view_get` 提供合并后的 arch、fields、toolbar | `app_view_config.py`, `contract_Parser.py` | 必须保留，作为输入事实 |
| 解析层 | `app.view.parser.parse_odoo_view()` 与 fallback 都声明 `no_business_fact_authority=True` | `native_parse_service.py`, `parse_fallback_service.py`, `contract_Parser.py` | 职责声明正确 |
| 投影缓存层 | `_generate_from_fields_view_get()` 直接把 parser/fallback 结果写入 `arch_parsed` | `app_view_config.py` | 这里混入了“解析即契约”的旧路径 |
| 页面装配层 | `PageAssembler` 直接读取 `app.view.config.get_contract_api()` 填入 `views[vt]` | `page_assembler.py` | 编排层没有独立出现 |
| V2 契约层 | `unified_page_contract_v2_assembler` 把 native layout 归一化为容器树，并补语义注解 | `unified_page_contract_v2_assembler.py` | 应只做契约投影，不应成为业务布局决策层 |
| 低代码字段策略 | 当前只写 `model/action_id/view_id/company_id` 的字段级 overlay | `form_field_configuration.py`, `ui_form_field_policy.py` | 只能作为编排输入，不能代表完整视图定义 |
| 现有编排能力 | `page_orchestration_v1` 存在，但主要服务页面/场景，不是表单视图编排 | `page_contracts_builder.py`, `page_contract_semantic_orchestration_bridge.py` | 能借鉴机制，不能直接等同表单编排 |

## 新边界

1. **模型能力层**
   - 负责字段、类型、关系、权限、domain、onchange、button 能力。
   - 可以直接借用 Odoo。

2. **原生视图解析层**
   - 负责保真解析 Odoo 原生结构：sheet、group、notebook/page、field、button、modifiers、subviews、chatter。
   - 只能产出 `native_view_parse_snapshot`。
   - 不负责行业模板选择、客户视图 profile、业务分组命名、业务字段重排。

3. **表单业务编排层**
   - 唯一负责最终业务结构。
   - 输入包括：模型能力、原生解析快照、action/view scope、行业模板、客户 profile、公司 overlay、角色 profile、字段策略 overlay。
   - 输出包括：容器树、字段顺序、字段显隐、业务动作槽位、关系入口槽位、协作槽位、来源追踪。

4. **契约投影层**
   - 只把编排结果投影成前端契约。
   - 可以做 schema 归一化、组件映射、状态映射。
   - 不负责决定哪些字段属于哪个业务分组。

5. **用户偏好层**
   - 只能保存折叠状态、列宽、最近筛选等弱偏好。
   - 不能参与结构事实和字段策略。

## 当前主要缺口

1. 缺少 `FormViewOrchestrator` 运行时服务。
2. 缺少行业模板与客户表单 profile 的持久模型。
3. `app.view.config.arch_parsed` 当前命名和职责偏旧，实际上混合了 native parse 与最终契约输入。
4. 低代码入口当前编辑字段策略，未来应编辑“表单编排 profile 输入”。
5. V2 assembler 里仍有语义猜测逻辑，只能保留为内部 annotation，不能上升为业务结构事实。

## 调整改进方向

### P0：锁边界

- Parser 和 fallback 继续保真解析，不做业务命名和业务重排。
- `PageAssembler` 不再新增业务布局规则；新增规则必须进入表单编排层。
- 低代码字段策略保持字段级 overlay，不扩展成 page/group/notebook 决策。
- V2 assembler 的语义补充只能写 `semanticTitle/semanticAnchor/sourceAuthority`，不能写用户可见 `title/label/string`。

### P1：建立表单编排输入模型

- `ui.form.view.template`：行业模板，定义行业默认分组、字段区域、动作槽位。
- `ui.form.view.profile`：客户/公司/角色/动作/视图 profile，绑定 `model/action_id/view_id/company_id/role_key`。
- `ui.form.view.profile.line`：字段落位、顺序、显示名、显隐、必填、默认折叠等。

### P2：建立表单编排服务

- `FormViewOrchestrator.compose(...)` 接收模型能力、native parse snapshot、template/profile/policy。
- 输出 orchestrated contract，并保留每个节点的 `source_trace`。
- `app.view.config` 存储编排后的 projection，同时保留 native parse snapshot 指纹。

### P3：迁移低代码入口

- 当前“字段顺序/显示名称/新增字段/分组改名”都应写入 profile。
- `ui.form.field.policy` 降级为字段 overlay 兼容层，最终由 orchestrator 消费。
- 前端继续无脑渲染契约，不理解 Odoo 原生视图、不理解行业模板。

## 门禁

```bash
make verify.form_view.orchestration_boundary_guard
```

门禁先锁住方向：

- parser/fallback 必须声明无业务事实权威。
- 语义标准化不能写用户可见 `title/label/string`。
- 低代码字段策略不能新增用户结构 scope。
- 新增表单结构决策必须指向 `business_form_orchestration` 边界。
