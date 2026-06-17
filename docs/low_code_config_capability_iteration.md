# 低代码配置能力专题迭代计划

## 目标

低代码配置能力的目标是让业务配置管理员在不改代码的前提下，稳定配置菜单、列表、搜索、表单、字段和动作，并且每一次配置都能被契约追踪、预览、发布、回滚和验收。

这不是前端兜底能力，也不是个人用户偏好。正式业务配置必须进入平台配置编排体系，由后端契约统一承载和解析，前端只负责展示配置入口、收集用户操作、消费契约结果。

## 分层边界

| 层级 | 职责 | 可以做 | 不可以做 |
| --- | --- | --- | --- |
| 平台核心 `smart_core` | 配置机制、契约模型、作用域、版本、权限、运行时解析 | 定义 `ui.business.config.contract`、配置 handler、契约合成、来源追踪、验收工具 | 写行业专属默认数据、写特定客户偏好 |
| 行业模块 `smart_construction_core` | 行业默认配置、行业配置入口、行业发布视图 | 发布行业默认契约、暴露配置菜单和管理视图 | 承载特定客户的喜好数据 |
| 用户模块 `smart_construction_custom` | 特定客户发布数据、客户偏好配置 | 写客户要求的菜单拆分、表单布局、字段隐藏等可交付配置 | 修改平台机制、绕过契约直接改前端 |
| 前端 `frontend/apps/web` | 配置交互、预览、契约消费 | 展示配置入口、提交配置 intent、按契约渲染页面 | 保存业务规则、用本地逻辑覆盖正式契约 |
| 用户个人偏好 `sc.user.view.preference` | 当前用户个人 UI 体验 | 列宽、个人可见列、个人排序等 UI-only 偏好 | 改变业务表单结构、字段顺序、业务默认配置 |

## 当前事实

### 正式业务配置契约

- 模型：`ui.business.config.contract`
- 版本：`ui.business.config.contract.version`
- 支持作用域：`model`、`view_type`、`action_id`、`view_id`、`role_key`、`company_id`、`status`、`priority`
- 运行时入口：`ViewOrchestrator` 根据 `view_orchestration` 合成 form/list/search/pivot/graph 等视图配置
- 已有发布和回滚 handler：`ui.business_config.contract.save/get/list/publish/rollback`

### 表单字段配置

- 模型：`ui.form.field.policy`
- 当前定位：表单字段显示、隐藏、标签、顺序的兼容配置输入
- 当前写入：低代码表单配置会写 `ui.form.field.policy`，并镜像到 `ui.business.config.contract`
- 已补齐：字段策略支持 `role_group_ids`，运行时按当前用户组筛选
- 已开始收敛：正式保存结果以 `view_orchestration` 为准，legacy `objects/layout/rules` 下沉到 `legacy_lowcode_draft` 作为兼容草稿
- 已开始收敛：运行时正式契约声明过的字段优先于 legacy `ui.form.field.policy` overlay，旧 policy 不能反向覆盖正式契约字段
- 已开始收敛：新增 `ui.business_config.form.audit` 读取正式契约字段、legacy policy 字段、冲突字段和仍生效的 legacy 字段，为全量验收提供后端基础
- 已开始收敛：表单设置界面接入“生效检查”，管理员可直接查看契约字段数、legacy policy 字段数、冲突字段和仍生效字段
- 主要风险：双写机制仍可能出现未声明字段的 policy 与 contract 不一致，后续应继续补生效报告和差异扫描

### 菜单配置

- 模型：`ui.menu.config.policy`
- handler：`ui.menu_config.panel.get/set`
- 支持：菜单改名、排序、显隐、移动父级、用户组范围
- 已开始收敛：新增 `ui.menu_config.audit` 只读审计入口，输出当前公司/用户组下配置总数、实际命中数、隐藏/改名/排序/移动数量和未命中 policy，作为全量验收基础
- 已开始收敛：菜单保存时同步生成并发布 `ui.business.config.contract`，模型为 `ir.ui.menu`，契约节点为 `menu_orchestration.v1`，用于版本追踪和后续发布/回滚治理
- 已开始收敛：新增 `ui.menu_config.rollback`，可从 `menu_orchestration.v1` 历史版本恢复 `ui.menu.config.policy`，并停用目标版本不存在的多余 policy
- 已开始收敛：菜单配置页面接入“生效检查”和“回滚上一版”，管理员可直接查看当前命中统计并触发回滚
- 已开始收敛：新增 `ui.menu_config.versions` 和页面版本面板，管理员可查看版本摘要并指定版本回滚
- 主要风险：菜单运行时目前仍由 `ui.menu.config.policy` 生效，正式契约已能追踪和回滚；后续应进入统一配置工作台而不是继续扩散单页按钮

### 列表列偏好

- 模型：`sc.user.view.preference`
- handler：`user.view.preference.get/set`
- 前端入口：`ActionView.vue`
- 当前定位：个人 UI-only 偏好
- 已开始收敛：新增 `ui.business_config.list_search.audit`，可输出业务级列表列、搜索筛选、搜索分组契约，并同时报告个人偏好数量和 `ui_only` 边界
- 已开始收敛：新增 `ui.business_config.list_search.set`，保存业务默认列表列、搜索筛选、搜索分组到 `ui.business.config.contract.view_orchestration`，不写 `sc.user.view.preference`
- 已开始收敛：统一配置工作台已接入列表/搜索编辑区，按模型/action/view/role_key 写入正式业务契约，不写个人偏好
- 主要风险：列表/搜索运行时消费面仍需全量扫描确认，避免只有配置端可写、业务页面未消费

### 前端低代码页面

- 主入口：`ContractFormPage.vue`
- 当前能力：当前表单字段顺序、显示隐藏、字段标签、添加字段、低代码契约保存/发布/回滚
- 主要风险：
  - 低代码草稿同时读取 legacy `objects/layout/rules` 和正式 `view_orchestration`
  - 保存表单设置时同时调用 `ui.business_config.lowcode.apply` 和 `ui.business_config.contract.save`
  - 前端有较多组装逻辑，后续应改为提交最小操作，由后端统一形成契约

## 系统性缺口

1. 配置能力没有统一工作台  
   菜单、表单、列表、搜索配置入口分散，用户不知道“在哪里配置、配置后影响哪里”。

2. 配置对象没有统一契约  
   表单进入 `ui.business.config.contract`，菜单仍是 `ui.menu.config.policy`，列表列仍是个人偏好，搜索配置能力不完整。

3. 作用域规则不一致  
   正式契约使用 `role_key`，菜单和字段 policy 使用 `role_group_ids`，列表偏好使用用户维度。后续需要统一成可解释的作用域模型。

4. 输入来源不稳定  
   用户能配置的输入必须来自运行时契约，而不是 XML 主视图或前端猜测。新建态、编辑态、动作视图必须使用同一作用域。

5. 配置结果缺少可验收报告  
   当前更多依赖浏览器抽查。后续必须有全量扫描：菜单、列表、搜索、表单、新建/编辑、角色、公司、开发服务器差异。

6. 发布链路不闭环  
   需要固定“保存草稿 -> 预览 -> 发布 -> 生效验证 -> 回滚”的流程，并区分代码发布、行业默认数据、用户配置数据。

## 专题迭代步骤

### P0 审计与规则冻结

- 固化本文件的分层边界。
- 补齐低代码配置能力矩阵。
- 输出现有 handler、模型、前端入口、契约入口清单。
- 明确每一类配置的正式归属。

验收：
- 新增或修改低代码功能前，必须能回答：写入哪里、读取哪里、作用域是什么、是否可发布回滚、是否影响用户偏好。

### P1 表单配置收敛

- 将表单字段顺序、显示隐藏、标签、分组统一以 `view_orchestration.views.form` 为正式结果。
- `ui.form.field.policy` 只作为快捷配置输入和兼容层，所有写入必须镜像契约，并有一致性校验。
- 运行时若 `view_orchestration.views.form.fields` 已声明字段，legacy field policy 不能覆盖该字段。
- 提供后端审计接口，输出正式契约字段、legacy policy 字段、被跳过字段、仍生效字段，作为浏览器验收和全量扫描的共同依据。
- 新建态、编辑态、指定 action/view 统一生效。
- 低代码表单输入只来自运行时契约，不直接使用 XML 主视图。
- legacy `objects/layout/rules` 只能作为兼容草稿保存在 `legacy_lowcode_draft`，不能作为当前表单渲染和生效判断的主依据。
- 已补自动固化入口：`ui.business_config.form.bootstrap` 可从当前后端运行态 form view contract 生成并发布正式表单业务契约，不写 legacy policy。

验收：
- 同一 action 的新建/编辑字段顺序一致。
- 只修改三栏布局时不改变字段顺序。
- 只修改字段顺序时不改变隐藏策略。
- 契约 governance 能显示命中的配置来源。

### P2 菜单配置契约化

- 保留 `ui.menu.config.policy` 管理视图，但补充正式契约/版本追踪。
- 已补第一步：菜单配置支持后端只读审计，能报告当前公司/用户组实际生效的菜单 policy。
- 已补第二步：菜单配置保存时镜像 `menu_orchestration.v1` 到 `ui.business.config.contract` 并发布版本。
- 已补第三步：菜单配置支持从历史契约版本恢复运行时 policy。
- 已补第四步：菜单配置页面接入生效检查和上一版回滚。
- 已补第五步：菜单配置页面接入版本列表和指定版本回滚。
- 菜单配置支持预览、发布、回滚。
- 菜单拆分、合并、隐藏、移动的用户模块数据进入用户模块边界。

验收：
- 菜单配置能输出当前公司/角色的生效报告。
- 合并入口/单独入口全量扫描可复现。

### P3 列表与搜索配置

- 新增业务级列表列配置契约，区别于 `sc.user.view.preference`。
- 新增业务级搜索筛选配置契约。
- 已补第一步：新增列表/搜索配置审计 intent，明确业务契约与个人偏好边界。
- 已补第二步：新增列表/搜索配置写入 intent，只写正式业务契约，不写个人偏好。
- 已补第三步：个人偏好只作为 UI-only 审计信号展示数量和明细，不参与业务契约覆盖是否通过的判定。
- 个人列宽、个人隐藏列继续留在用户偏好，不能影响业务默认配置。

验收：
- 管理员配置默认列表列后，所有目标用户默认一致。
- 普通用户个人列宽/隐藏不会覆盖业务默认结构。
- 搜索筛选项与业务分类契约一致。

### P4 配置工作台

- 统一入口：当前页面配置、菜单配置、列表配置、搜索配置、表单配置。
- 已补第一步：新增 `ui.business_config.surface.get`，输出当前模型/action 下表单、列表/搜索、菜单配置面及契约数量，作为统一工作台只读入口。
- 已补第二步：新增 `/admin/business-config` 页面，展示配置面摘要和边界，承载表单、列表/搜索、菜单配置入口，避免把业务配置按钮散落到普通业务页。
- 已补第三步：工作台接入列表/搜索编辑区，调用 `ui.business_config.list_search.audit/set`，只写正式业务契约，不写个人偏好。
- 已补第四步：工作台接入表单配置入口，通过 `config_mode=form_field_configuration` 打开当前模型/action 的表单配置模式。
- 已补第五步：工作台接入模型、action、view、role_key 作用域选择；摘要、列表/搜索保存和表单配置跳转统一使用当前作用域。
- 已补第六步：新增 `ui.business_config.contract.versions`，工作台默认路径可查看当前页面表单、列表、搜索配置版本摘要；工作台版本面板已接入 `ui.business_config.contract.rollback`，支持回滚上一版和回滚到指定版本，并在历史版本行显示相对当前版本的字段/列/筛选/分组差异摘要，不触碰个人偏好。作用域和业务契约解释只在高级设置中展示。
- 已补第七步：行业模块新增“业务配置工作台”菜单入口，前端动作服务识别该配置动作后进入 `/admin/business-config`；平台管理员侧栏也提供工作台快捷入口，确保配置工作台不是隐藏路由。
- 已补第八步：行业根菜单扫描范围由行业 action context 提供 `business_config_root_menu_xmlid`，平台前端壳不硬编码行业 XMLID。
- 已补第九步：工作台接入分析页面筛选和分析视图卡片，当前支持发现 pivot/graph/calendar/dashboard 页面、查看分析视图配置版本、显示分析项摘要和版本差异并预览页面；复杂编辑器后置，不向用户展示未接入编辑入口。
- 支持作用域选择：当前页面、当前动作、当前视图、当前公司、当前角色/用户组。
- 支持配置预检、冲突提示、生效预览、发布/回滚。

验收：
- 管理员不需要知道 XML、技术视图、模型主视图差异，也能完成常用配置。

### P5 全量验收工具

- 后端扫描菜单配置覆盖。
- 后端扫描 action/view 表单契约覆盖。
- 后端扫描列表列和搜索筛选契约覆盖。
- 输出本地与开发服务器配置差异。
- 已补第一步：新增 `ui.business_config.coverage.scan`，默认按当前用户可见菜单 action/模型扫描表单、列表、搜索正式契约覆盖缺口、运行时有效发布契约缺口及分类原因、菜单入口缺口和个人偏好边界信号；工作台顶部提供“全量扫描”和“扫当前模型”入口，扫描行输出配置/发布/运行时证据、严重级别和结构化 `code/target/priority` 整改动作，摘要输出单一验收结论、严重级别、整改动作统计和运行页面路径，并支持只看问题和复制验收摘要；无菜单 action 审计需要显式开启 `include_unreachable_actions`；个人偏好只作为 UI-only 审计信号，不让覆盖验收从通过降级为提示。
- 已补第二步：扫描行“补配置”可从运行态后端契约一次固化当前 action 的表单、列表、搜索缺口；全量按钮可批量固化表单、列表、搜索运行态缺口。
- 已补第三步：系统级迁移/验收可显式开启 `include_all_root_menu_actions`，按行业根菜单下全部 action 扫描，不受当前用户菜单可见性影响；工作台已区分“可见范围扫描”和系统级扫描，有行业根菜单参数时显示为“系统根菜单扫描”，无根菜单参数时显示为“全部菜单扫描”，普通扫描默认仍按当前用户可见范围执行。
- 已补第四步：新增 `make verify.business_config.coverage`，按系统根菜单和代表角色账号输出只读覆盖验收报告，用于本地和开发服务器升级后确认表单/列表/搜索运行态缺口为 0；报告同时落盘运行页面样本路径，便于升级后浏览器验收。
- 已补第五步：覆盖扫描行输出 `runtime_route` 和 `menu_ids`，工作台可从扫描结果直接打开对应运行页面，作为浏览器验收入口。
- 已补第六步：新增 `make verify.business_config.full_acceptance`，先跑低代码后端单测，再构建前端静态资源、跑覆盖门禁，最后用 Playwright 打开覆盖报告中的运行页面样本，生成截图和 JSON 报告，补齐配置契约到真实页面的闭环证据。
- 已补第七步：新增 `make verify.business_config.low_code_acceptance`，用业务配置管理员账号打开 `/admin/business-config`，验证默认用户路径不暴露治理/技术话术，并覆盖页面搜索/筛选、页面选择、配置版本记录、运行页面预览、列表与搜索三类 tab、列表与搜索草稿编辑和放弃调整、表单字段点选/拖拽/显示隐藏/顺序调整/新增字段、检查效果、返回配置上下文；验收报告落盘关键截图，并检查浏览器 error/warning 为空。
- 已补第八步：低代码用户路径验收补 390px 移动宽度检查，要求配置工作台无横向溢出，并落盘移动截图；`make verify.business_config.full_acceptance` 已串联该验收。
- 已补第九步：低代码用户路径验收补高级设置边界检查，默认路径不展示治理/技术话术，显式打开高级设置后必须出现作用域字段和高级治理视图。
- 已补第十步：新增 `make verify.business_config.unit`，串联表单/列表/搜索配置 handler 和业务配置工作台单测，并纳入 full acceptance。
- 已补第十一步：新增 `make verify.business_config.snapshot`，导出当前数据库 `ui.business.config.contract` 快照到 `artifacts/backend/business_config_contract_snapshot.json`；可通过 `BUSINESS_CONFIG_SNAPSHOT_COMPARE_PATH=/mnt/artifacts/backend/<baseline>.json` 对比另一个环境快照，输出新增、删除和 payload/status 变化摘要。

验收：
- 每次升级前后能生成覆盖报告，不能只靠样本浏览器验收。

## 本分支优先级

1. 完成 P0 审计文档和边界规则。
2. 先收敛表单配置作用域与输入来源。
3. 再补菜单/列表/搜索的正式契约化能力。
4. 最后做配置工作台和全量验收工具。
