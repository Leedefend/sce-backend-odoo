# app_config_engine Boundary

`addons/smart_core/app_config_engine` 是 Smart Core 的运行时契约管线，不是行业业务事实层，也不是产品化表单/列表/搜索的决策层。

它的核心职责是把一次 `/api/contract/get` 请求转换成前端可消费的页面契约：解析请求、解析 Odoo 原生元数据、装配页面契约、注入运行态摘要、应用权限和治理过滤，然后返回统一响应。

## Runtime Contract Plumbing

当前链路按职责拆分如下：

1. `controllers/contract_api.py`
   - HTTP 入口，只接收请求、创建 `ContractService`、透传响应。
   - 不做业务判断，不做产品布局，不直接决定字段显隐。

2. `services/contract_service.py`
   - `/api/contract/get` 的服务入口。
   - 负责 payload 读取、subject 分发、ETag、meta、统一后处理和治理过滤。
   - 它是契约管线的调度器，不是业务规则来源。

3. `services/dispatchers` and `services/resolvers`
   - 根据 `nav/menu/action/model/operation` 找到运行对象。
   - 可以解析 Odoo 菜单、动作、模型上下文。
   - 不定义行业模块的业务含义。

4. `services/native_parse_service.py` and `services/view_Parser`
   - Native Odoo Parse Boundary。
   - 只做 Odoo 原生视图的保真解析和降级解析。
   - 输出应表达 Odoo 原生结构，不应表达产品化后的业务入口设计。

5. `models/app_view_config.py`
   - 旧版 `app.view.config` 视图契约模型和兼容入口。
   - 可以调用 `ViewOrchestrator` 把原生契约和业务视图编排合成运行时视图契约。
   - 它不拥有 `ui.business.config.contract` 中的产品化配置事实。

6. `services/assemblers/page_assembler.py`
   - 页面契约装配和投影层。
   - 聚合 fields/views/search/permissions/actions/reports/workflow/validator 等运行态结构。
   - 可以注入 `view_orchestration` 摘要，便于前端和诊断知道编排是否生效。
   - 不应手写某个 P1 业务表单的产品布局。

7. `services/contract_governance_filter.py`
   - 对已经解析/装配好的契约做运行态治理过滤。
   - 不生产业务事实。

## No Business Fact Authority

`app_config_engine` 的所有核心入口都必须保持 `NO_BUSINESS_FACT_AUTHORITY = True`。

这句话的含义是：

- 它可以读取 Odoo 元数据、配置模型和当前用户上下文。
- 它可以把已有事实投影成前端契约。
- 它可以做权限裁剪、结构归一化和兼容补齐。
- 它不能成为行业业务事实的权威来源。
- 它不能把某个行业模块的产品化表单布局硬编码进平台层。

如果需要表达“某个业务入口应该显示哪些字段、分成哪些业务区块、使用什么语义表单”，权威来源必须是 `ui.business.config.contract` 的 `view_orchestration` 配置，或明确归属到行业模块的数据文件。

## View Orchestration Boundary

视图产品化的职责边界是：

- Odoo native parser: 负责保真解析原生模型、动作、视图、字段结构。
- `ui.business.config.contract`: 负责声明入口级、动作级、角色级的业务视图编排配置。
- `ViewOrchestrator`: 负责把原生契约和 `view_orchestration` 合成为运行态视图契约。
- `app_config_engine`: 负责承载和投影合成后的运行时契约。
- `UiContractV2Handler`: 负责对外提供 V2 统一页面契约门面，并把运行时结构转换成前端消费形态。

因此，P1 产品发布级表单不应该在 `app_config_engine` 内新增手写 layout。正确做法是：

1. 行业模块通过 `ui.business.config.contract` 声明 `view_orchestration`。
2. 表单使用 `fields + sections + composition_mode=entry_semantic_surface` 表达产品化意图。
3. 后端 `ViewOrchestrator` 生成稳定、可验证的运行态表单结构。
4. `app_config_engine` 只把结果装配进页面契约并暴露摘要。

## Compatibility Models

`app.model.config`、`app.view.config`、`app.search.config`、`app.permission.config`、`app.action.config`、`app.report.config`、`app.workflow.config`、`app.validator.config` 是历史契约模型和兼容载体。

它们仍然参与运行时页面契约装配，但不能被误解为新的产品化配置权威。后续新增的业务入口产品化规则，应优先落在 `ui.business.config.contract.view_orchestration`，除非有正式架构决策重新定义这些模型的权威范围。

## No Industry Defaults

`app_config_engine` 不保存行业模块 XMLID、行业管理员组、行业菜单、行业动作或行业产品默认值。

当页面装配需要业务配置入口、表单配置入口、审批策略入口或行业菜单根节点时，只能读取：

- extension hook；
- `ir.config_parameter`；
- `ui.business.config.contract`；
- Odoo 原生菜单/动作/视图记录。

没有这些来源时，`app_config_engine` 只返回平台中立契约，不在自身代码里补行业默认值。

## Verification

边界守卫：

- `make verify.app_config_engine.boundary_guard`

该守卫验证：

- 本文档保留运行时契约管线、原生解析边界、视图编排边界、兼容模型和 No Business Fact Authority 说明。
- HTTP 控制器仍是薄入口，并委托 `ContractService`。
- `ContractService`、`NativeParseService`、`PageAssembler` 保持无业务事实权威声明。
- `PageAssembler` 只注入编排摘要，不成为 P1 产品布局定义层。
- `app_config_engine` 内不允许新增行业模块引用。
