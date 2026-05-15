# 视图编排层边界审计

## 结论

当前矛盾不是“要不要借用 Odoo 原生视图”，而是“借用后谁有权决定最终业务视图”。Odoo 原生视图必须借用，解析也必须保留；但解析结果不能直接成为最终用户可见结构。缺失的是一个独立的业务视图编排层，覆盖 `form/tree/list/kanban/search/pivot/graph/calendar/gantt/activity/dashboard` 等所有视图。

表单只是最容易暴露问题的视图类型，不是边界本身。边界必须定义在“业务视图”层，而不是“表单视图”层。

## 当前事实

| 层 | 当前事实 | 证据文件 | 判断 |
| --- | --- | --- | --- |
| Odoo 原生视图输入 | `get_view` / `fields_view_get` 提供合并后的 arch、fields、toolbar | `app_view_config.py`, `contract_Parser.py` | 必须保留，作为输入事实 |
| 解析层 | `app.view.parser.parse_odoo_view()` 与 fallback 都声明 `no_business_fact_authority=True` | `native_parse_service.py`, `parse_fallback_service.py`, `contract_Parser.py` | 职责声明正确 |
| 投影缓存层 | `_generate_from_fields_view_get()` 直接把 parser/fallback 结果写入 `arch_parsed` | `app_view_config.py` | 这里混入了“解析即契约”的旧路径 |
| 页面装配层 | `PageAssembler` 直接读取 `app.view.config.get_contract_api()` 填入 `views[vt]` | `page_assembler.py` | 编排层没有独立出现 |
| V2 契约层 | `unified_page_contract_v2_assembler` 把 layout/sections 归一化并补语义注解 | `unified_page_contract_v2_assembler.py` | 应只做契约投影，不应成为业务布局决策层 |
| 业务配置合同 | `ui.business.config.contract` 已经具备保存、发布、版本能力 | `ui_business_config_contract.py`, `form_field_configuration.py` | 应升级为视图编排配置入口，而不是另建 profile 概念 |
| 低代码字段策略 | 当前只写 `model/action_id/view_id/company_id` 的字段级 overlay | `form_field_configuration.py`, `ui_form_field_policy.py` | 只能作为视图编排输入的兼容层，最终被业务配置合同吸收 |
| 现有编排能力 | `page_orchestration_v1` 存在，但主要服务页面/场景，不是模型视图编排 | `page_contracts_builder.py`, `page_contract_semantic_orchestration_bridge.py` | 能借鉴机制，不能直接等同视图编排 |

## 新边界

1. **模型能力层**
   - 负责字段、类型、关系、权限、domain、onchange、button、聚合能力。
   - 可以直接借用 Odoo。

2. **原生视图解析层**
   - 负责保真解析 Odoo 原生结构：form 的 sheet/group/notebook，list/tree 的 columns，kanban 的 card template，search 的 filters/group_by，pivot/graph 的 measures/dimensions，calendar/gantt/activity 的原生槽位。
   - 只能产出 `native_view_parse_snapshot`。
   - 不负责业务配置选择、配置规则解释、业务分区命名、字段/列/筛选/指标重排。

3. **业务视图编排层**
   - 唯一负责最终业务视图结构。
   - 输入包括：模型能力、原生解析快照、view_type、action/view scope、业务配置合同、配置版本、配置规则、兼容字段策略 overlay。
   - 输出包括：layout slots、字段/列顺序、显隐策略、业务动作槽位、关系入口槽位、聚合槽位、筛选槽位、分组槽位、协作槽位、来源追踪。

4. **契约投影层**
   - 只把编排结果投影成前端契约。
   - 可以做 schema 归一化、组件映射、状态映射。
   - 不负责决定哪些字段、列、筛选、指标属于哪个业务区域。

5. **用户偏好层**
   - 只能保存折叠状态、列宽、最近筛选、排序偏好等弱偏好。
   - 不能参与结构事实和业务策略。

## 视图类型边界

| 视图类型 | 编排层负责 | 解析层只提供 |
| --- | --- | --- |
| form | 容器树、字段落位、动作槽位、关系入口、协作槽位 | sheet/group/page/field/button/subview/chatter |
| tree/list | 列顺序、列显隐、行操作、聚合槽位 | 原生 columns、modifiers、toolbar |
| kanban | 卡片区域、分组策略、快捷动作 | 原生 kanban template、field、progressbar |
| search | 筛选分区、默认筛选、group_by、收藏入口 | 原生 filter、field、separator、group |
| pivot/graph | 指标、维度、默认分析视角 | 原生 measure、row/col、graph 属性 |
| calendar/gantt/activity | 日期/资源/颜色/依赖/负责人槽位 | 原生日期字段、资源字段、活动字段 |
| dashboard | 指标、图表、导航槽位 | 原生或聚合投影输入 |

## 当前主要缺口

1. 缺少 `ViewOrchestrator` 运行时服务。
2. `ui.business.config.contract` 尚未明确升级为“视图编排配置”入口，缺少 view_type/action/view 的运行时 scope。
3. `app.view.config.arch_parsed` 当前命名和职责偏旧，实际上混合了 native parse 与最终契约输入。
4. 低代码入口当前编辑字段策略，未来应编辑“业务配置合同中的视图编排规则”；字段策略只能作为兼容 overlay。
5. V2 assembler 里仍有语义猜测逻辑，只能保留为内部 annotation，不能上升为业务结构事实。

## 调整改进方向

### P0：锁边界

- Parser 和 fallback 继续保真解析，不做业务命名和业务重排。
- `PageAssembler` 不再新增业务视图规则；新增规则必须进入业务视图编排层。
- 低代码字段策略保持兼容 overlay，不扩展成 form/list/search/pivot 等结构决策。
- V2 assembler 的语义补充只能写内部 annotation，不能写用户可见结构事实。

### P1：改造现有配置为视图编排配置

- `ui.business.config.contract`：作为统一业务配置合同，承载视图编排配置。
- 配置合同按 `model/view_type/action_id/view_id/company_id/role_key` 生效。
- `contract_json.view_orchestration`：定义字段、列、筛选、指标、动作、分组、容器槽位的落位、顺序、显示名、显隐、默认态。
- 直接复用保存、发布、版本能力，不再新增平行的 template/profile 模型。

### P2：建立通用视图编排服务

- `ViewOrchestrator.compose(...)` 接收模型能力、native parse snapshot、业务配置合同、兼容字段策略。
- 输出 orchestrated view contract，并保留每个节点的 `source_trace`。
- `app.view.config` 存储编排后的 projection，同时保留 native parse snapshot 指纹。

### P3：迁移低代码入口

- 当前“字段顺序/显示名称/新增字段/分组改名”只是 form 视图的配置编辑特例。
- list 的列配置、search 的筛选配置、pivot/graph 的指标维度配置，都必须进入同一套业务配置合同。
- 前端继续无脑渲染契约，不理解 Odoo 原生视图、不理解行业模板。

## 门禁

```bash
make verify.view.orchestration_boundary_guard
```

门禁先锁住方向：

- parser/fallback 必须声明无业务事实权威。
- 新边界必须覆盖所有主要 Odoo 视图类型。
- 新增结构决策必须指向 `business_view_orchestration` 边界，并由 `ui.business.config.contract` 承载配置事实。
- 不允许再把架构边界命名为 form 专用边界。
