# 低代码配置能力矩阵

本矩阵只定义低代码配置产品的能力状态。正式产品归属必须先按 `docs/product/formal_product_boundary_v1.md` 判断：低代码是运行时编辑面和配置承载，不是所有配置的最终产品归属。

## 使用者定位

低代码配置默认面向客户管理员、实施管理员和平台运营管理员。研发人员可以使用低代码做候选配置验证、运行时合同调试和配置生成，但结果必须通过代码、数据、迁移、产品策略或发布合同沉淀后才算正式产品基线。普通业务用户不直接使用全局低代码配置；普通用户只使用个人偏好能力，个人偏好不得影响他人、不得进入产品发布基线。

| 使用者 | 允许使用 | 输出状态 | 不允许 |
| --- | --- | --- | --- |
| 研发人员 | 本地/测试环境试配、生成候选配置、调试合同和覆盖顺序 | `developer_draft` | 直接把手工低代码结果当 P0/P1/P2 正式发布事实 |
| 实施/客户管理员 | 当前租户菜单、字段、列表、搜索、审批运行时配置 | `tenant_runtime` | 修改业务事实；隐藏系统配置恢复入口；绕过版本审计 |
| 产品发布流程 | 读取已确认配置并生成正式发布基线 | `product_release` | 依赖无法重放的数据库手工状态 |
| 普通业务用户 | 个人筛选、列宽、收藏、快捷入口等个人偏好 | `ui_only` / personal preference | 修改全局菜单、字段、审批、权限和发布合同 |

## 菜单配置对象边界

| 菜单对象 | 典型入口 | 低代码显隐 | 低代码命名/排序/移动 | 正式归属 |
| --- | --- | --- | --- | --- |
| 系统配置入口 | 配置中心、菜单配置、字段配置、权限/角色/策略配置、发布/合同治理入口 | 禁止彻底隐藏；必须保留恢复路径和原菜单权限校验 | 允许有限调整，但不得移动到不可达位置 | P0 平台治理能力 |
| 产品发布菜单 | 项目、合同、结算、付款、材料、劳务等正式业务办理入口 | 允许按租户/角色覆盖，必须有版本和来源 | 允许按租户/角色覆盖，不能反向污染行业发布基线 | P1/P2/P3 视确认状态分流 |
| 用户/租户配置菜单 | 客户确认的菜单拆分、标签、分组、角色可见性 | 允许，需版本、审计、回滚 | 允许，长期生效需沉淀到用户模块或保留 P3 版本 | P2 用户产品或 P3 运行时配置 |

菜单配置的生效链路必须锁定为：原生菜单/产品发布基线 -> `menu_orchestration` 低代码覆盖 -> `/api/menu/navigation` 最终低代码导航。主导航和菜单配置默认左侧树均以产品发布菜单 `release_navigation_v1` 为权威，保证管理员看到和配置的是同一套产品菜单；`/api/menu/navigation` 只服务预览、审计和低代码运行时对齐验收，不得反向覆盖产品发布主导航，也不得作为默认配置目录来源。`verify.product.navigation_boundary` 必须验证主导航与菜单配置默认树一致；`verify.business_config.low_code_menu_navigation_alignment` 必须验证低代码最终出口与已发布菜单配置合同的可见性、标签和父级一致。

## 低代码到正式产品的分流规则

| 用户动作/配置结果 | 运行时承载 | 最终归属 | 后续动作 |
| --- | --- | --- | --- |
| 研发试配或调试生成的菜单、字段、列表、审批候选配置 | 低代码草稿或临时合同 | `developer_draft` | 转成代码、数据 XML、迁移脚本、产品策略或发布合同后才可发布 |
| 管理员试调菜单、字段、列表、搜索、审批 | 低代码运行时配置 | P3 低代码配置产品 | 保留版本、审计、回滚，不写入模块 |
| 当前客户确认长期生效的看面和初始化偏好 | 低代码运行时配置先承载 | P2 用户产品 | 沉淀到 `smart_construction_custom` 或独立客户模块，升级可重放 |
| 当前客户确认长期生效的数据整理结果 | 迁移/修复脚本先承载 | P2 用户数据基线 | 和功能偏好分开沉淀到 `smart_construction_custom/data`、客户数据模块或幂等初始化 |
| 多客户复用后确认的施工行业默认 | 低代码可作为试配来源 | P1 行业标准产品 | 沉淀到 `smart_construction_core` / 行业场景模块 |
| 配置引擎缺少通用机制 | 低代码无法稳定表达 | P0 平台产品 | 在 `smart_core` 增加通用机制，不写行业/客户语义 |
| 数据错位、历史补数、跨库修复 | 脚本或迁移临时承载 | P4 运维交付工具 | 修复后把长期事实沉淀到 P1/P2/P3 |

低代码保存成功不等于正式交付完成。凡是用户确认“以后都要这样”的配置，都必须再次判断是否需要沉淀到用户模块或行业模块。

| 能力 | 当前承载 | 当前入口 | 正式归属 | 当前状态 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 表单字段显示/隐藏 | `ui.form.field.policy` + `ui.business.config.contract.view_orchestration` | 当前表单“表单设置” | `ui.business.config.contract` | 可用，正式归属为 `view_orchestration`，`ui.form.field.policy` 作为兼容写入并在返回值中标明边界 | P1 继续压缩 legacy policy 兼容层 |
| 表单字段顺序 | `ui.form.field.policy.sequence` + `view_orchestration.views.form.fields` | 当前表单“保存表单设置” | `ui.business.config.contract` | 可用，保存时写正式 `fields` 和 `layout`，兼容写入 policy 并返回正式归属边界 | P1 统一运行时契约输入 |
| 表单字段标签 | `ui.form.field.policy.label` + `view_orchestration.views.form.fields[].label` | 当前表单内联修改 | `ui.business.config.contract` | 可用，写入已镜像契约，版本摘要和差异按业务标签对比 | P1 继续压缩 legacy policy 兼容层 |
| 表单字段新增 | `ui.form.custom.field.wizard` + `ir.model.fields` + field policy | 当前表单“添加字段” | 平台元数据 + `ui.business.config.contract` | 可用，intent 支持 dry-run 预检且正式执行后镜像契约，返回字段元数据回滚边界：契约回滚不删除 `ir.model.fields` | P1 补字段元数据清理工具前置评估 |
| 表单布局/分组 | `view_orchestration.views.form.layout` + 前端草稿 | 当前表单低代码区域 | `ui.business.config.contract` | 可用，保存表单设置会写入正式 layout，预检约束正式 layout schema，表单检查会输出正式布局字段数和字段顺序是否对齐 | P1 继续压缩 legacy 草稿兼容展示 |
| 菜单显隐 | `ui.menu.config.policy.visible` + `ui.business.config.contract.menu_orchestration` | 统一配置工作台菜单卡片 / 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、运行来源提示、版本列表、指定版本回滚，工作台可进入并返回，运行时优先读 `menu_orchestration` 契约，policy 作为兼容回退；系统配置恢复入口不可被彻底隐藏，仍按原菜单权限校验 | P4 继续压缩 policy 回退层，并补系统配置保护矩阵门禁 |
| 菜单改名 | `ui.menu.config.policy.custom_label` + `ui.business.config.contract.menu_orchestration` | 统一配置工作台菜单卡片 / 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、运行来源提示、版本列表、指定版本回滚，工作台可进入并返回，运行时优先读 `menu_orchestration` 契约，policy 作为兼容回退 | P4 继续压缩 policy 回退层 |
| 菜单排序/移动 | `ui.menu.config.policy.sequence_override/target_parent_menu_id` + `ui.business.config.contract.menu_orchestration` | 统一配置工作台菜单卡片 / 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、运行来源提示、版本列表、指定版本回滚，工作台可进入并返回，运行时优先读 `menu_orchestration` 契约，policy 作为兼容回退 | P4 继续压缩 policy 回退层 |
| 菜单新增/复制入口 | `ir.ui.menu` + `ui.menu.config.policy` + `ui.business.config.contract.menu_orchestration` | 菜单配置面板“新增菜单 / 新增同级 / 新增下级 / 复制当前入口” / `ui.menu_config.menu.create` | 低代码运行时配置；长期交付归用户模块或行业模块 | 可用，支持创建分组菜单或复制已有菜单页面动作，创建后同步生成 policy 并发布菜单配置版本；默认提醒长期入口需沉淀到用户模块 | P4 扩展为从业务页面库选择 action |
| 审批规则配置 | `sc.approval.policy.approval_required/mode/manager_scope_key/step_ids` + `sc.approval.step` | 统一配置工作台“审批规则”卡片 / `sc.approval_policy.config.get/set` / `sc.approval_policy.steps.set` / 行业审批规则视图 | 行业模块业务规则，不归入页面契约 | 可用，工作台可按当前业务页面直接设置是否启用审批、审批方式、默认审批岗位，并用拖拽/上下移动编排审批步骤、岗位和金额区间；删除步骤在配置层移除、数据层停用，运行时由行业审批服务和 tier validation 消费；高级规则仍可进入行业审批规则视图处理系统字段；完整验收已串联 rollback-only 审批开关运行态门禁，专项财务审批流由 `verify.business.finance_document_tier_runtime_smoke` 覆盖 | P5 补审批流浏览器样本验收 |
| 列表个人列偏好 | `sc.user.view.preference` | 列表选择列 | 用户个人偏好 | 可用 | 保持 UI-only |
| 业务默认列表列 | `view_orchestration.views.tree.columns` | `/admin/business-config` / `ui.business_config.list_search.audit/set` | `ui.business.config.contract` | 可用，工作台可按作用域查看/保存，已纳入覆盖扫描、批量补齐、升级迁移固化、运行页面跳转和 `make verify.business_config.full_acceptance` 浏览器批量验收证据，版本差异显示具体新增/减少列摘要 | P5 继续扩展跨环境配置差异分析 |
| 搜索筛选配置 | `view_orchestration.views.search.filters/group_by` | `/admin/business-config` / `ui.business_config.list_search.audit/set` | `ui.business.config.contract` | 可用，工作台可按作用域查看/保存，已纳入覆盖扫描、批量补齐、升级迁移固化、运行页面跳转和 `make verify.business_config.full_acceptance` 浏览器批量验收证据，版本差异显示具体新增/减少筛选和分组摘要 | P5 继续扩展跨环境配置差异分析 |
| 分析视图配置 | `view_orchestration` pivot/graph/calendar/dashboard | `/admin/business-config` 分析视图卡片 / 版本面板 / `ui.business_config.analysis.audit/set` | `ui.business.config.contract` | 可用，工作台已可发现分析页面、查看分析视图配置版本、显示分析项明细和版本差异；默认编辑器支持透视/图表指标、维度和图表类型配置并发布正式业务配置；日历/看板复杂槽位后置 | P5 扩展日历/看板复杂槽位编辑器 |
| 客户确认配置沉淀 | `smart_construction_custom` 或对应客户模块 | 已验收的低代码配置结果 / 客户交付清单 / `make verify.lowcode_config.customer_module_asset.pipeline` / `make verify.lowcode_config.customer_module_asset.release_hardening.guard` | 用户模块 | 已补 `lowcode_customer_config_baseline_manifest.v1`，明确菜单偏好、表单偏好、用户数据基线的运行时来源、用户模块承载、安装/升级钩子、快照对比和守卫要求；已补 `lowcode_customer_config_baseline_candidate.v1` 候选包导出辅助，默认只提取 `tenant_runtime` 合同并按菜单、表单、列表/搜索、分析视图分类；已补 `lowcode_customer_config_module_asset_draft.v1` 草案生成器，把候选包转换为可复核的客户模块资产草案并保持 `review_required` / `not_applied_to_module`；已补 `lowcode_customer_config_acceptance_decisions.v1` 人工确认决策模板，所有草案记录默认 pending；已补决策应用 dry-run，只有显式 accepted 且带 reviewer/review_note、payload_hash 匹配、source_status 为 tenant_runtime 的记录才会进入候选正式资产，写模块资产必须显式 `LOWCODE_CUSTOMER_CONFIG_APPLY_ACCEPTANCE=1`；已补 `lowcode_customer_config_contracts.v1` 正式接受资产空基线、hooks 幂等回放入口和 replay guard；已补 `make verify.lowcode_config.customer_module_asset.pipeline` 聚合候选导出、草案、决策模板、dry-run 应用、安全测试和回放守卫；已补 `make verify.lowcode_config.customer_module_asset.release_hardening.guard` 锁定该管线持续接入正式发布硬化、v2.0.0 清单、证据 manifest 与客户 manifest；低代码保存仍只是运行时编辑面，用户模块才是可重放交付基线 | P5 继续补产品化页面/审批动作，驱动 accepted 决策生成 |
| 配置发布/回滚 | `ui.business.config.contract.version` | 表单配置按钮 / 菜单配置 / 工作台版本面板 | 平台核心 | 发布追踪可用，菜单支持指定版本回滚，工作台默认路径可查看当前页面配置版本、回滚上一版并回滚到指定版本，历史版本行显示相对当前版本的字段/列/筛选/分组/分析项具体新增和减少摘要；作用域和业务配置边界解释只在高级设置中展示；覆盖扫描行可直接打开运行页面，完整验收会批量打开运行页面样本；`make verify.business_config.snapshot` 可导出当前库配置快照并支持文件级跨环境差异对比；高级设置可下载当前库快照并粘贴快照 JSON 与当前库只读对比 | P5 继续扩展工作台跨环境差异操作 |
| 配置工作台摘要 | `ui.business_config.surface.get` / `ui.business_config.contract.versions` / `ui.business_config.snapshot.export` / `ui.business_config.snapshot.compare` | 业务配置中心“业务配置工作台” / 平台管理员侧栏 / `/admin/business-config` | 平台核心 + 行业入口 | 页面可用，已接表单、列表/搜索、分析视图、菜单入口、作用域选择、默认版本记录、全量扫描入口、可发现入口、高级配置快照摘要、当前快照下载、跨环境快照对比和整改清单下载；整改清单以 `business_config_snapshot_remediation_plan.v1` 输出新增、移除、变化合同及发布后复验要求 | P5 继续扩展跨环境整改执行自动化 |
| 配置验收报告 | `ui.business_config.coverage.scan` / `ui.business_config.coverage.bootstrap_missing` / `make verify.business_config.unit` / `make verify.business_config.coverage` / `make verify.business_config.approval_runtime` / `make verify.business_config.low_code_acceptance` / `make verify.business_config.full_acceptance` | `/admin/business-config` | 平台工具 | 默认按当前用户可见菜单 action 扫描表单/列表/搜索/分析视图配置覆盖缺口、运行时有效发布配置缺口及分类原因、菜单入口缺口和个人偏好边界信号；扫描行输出运行页面路由并支持工作台直接打开；工作台支持表单/列表/搜索缺口批量补齐，分析视图缺口进入分析配置面板手工配置；升级迁移会按系统根菜单和代表角色自动固化表单/列表/搜索缺口；门禁命令按代表角色验证运行态无缺口并按视图类型补齐运行页面样本，pivot/graph 样本会以 `view_mode` 打开并验证 `.advanced-view` 渲染成功；后端单测覆盖默认用户语言、表单/列表/搜索/分析 intent 参数、字段有效性、个人偏好边界、工作台扫描、菜单配置审计和审批规则配置；低代码用户路径验收会用浏览器验证业务配置管理员能搜索页面、选择页面、查看配置版本记录、预览页面、配置列表/搜索三类 tab、拖拽/点选表单字段、调整显示隐藏和顺序、新增字段、检查效果、配置审批开关和审批步骤区并返回配置上下文；审批步骤验收已对齐旧系统拖拽习惯，会用临时步骤名真实拖动前两行、确认顺序互换、确认保存按钮变可用并还原不落库；完整验收还会执行 rollback-only 审批开关运行态门禁，确认审批配置会被代表业务提交/确认链路消费；默认路径不暴露治理/技术话术，高级设置显式打开后必须能展示作用域字段和高级治理视图；低代码验收报告会落盘关键截图，检查前后端边界常量完全一致、边界常量无散落、390px 视口无横向溢出、浏览器 error/warning 为空；完整验收命令会先跑后端低代码单测，再构建前端静态资源、跑覆盖门禁、审批开关运行态门禁、运行页面浏览器样本和低代码用户路径验收。系统根菜单扫描只能覆盖标准 ORM 菜单 action，运行时可见菜单仍必须保留代表角色验收 | P5 继续扩展跨环境整改闭环 |

## 作用域对齐目标

| 作用域 | 正式契约字段 | 兼容字段 | 说明 |
| --- | --- | --- | --- |
| 模型 | `model` | `model` | 必填 |
| 视图类型 | `view_type` | `view_type` | `list` 归一为 `tree` |
| 动作 | `action_id` | `action_id` | 当前页面配置必须带 action |
| 视图 | `view_id` | `view_id` | 有明确视图时必须保留 |
| 公司 | `company_id` | `company_id` | 默认当前公司，可为空表示全局 |
| 角色 | `role_key` | `role_group_ids` | 业务配置接口拒绝旧 `role_group_ids`，必须使用 `role_key`；旧字段只保留在 legacy policy 审计输出 |
| 用户 | 不进入业务配置 | `sc.user.view.preference.user_id` | 只用于个人 UI 偏好 |

## 优先修复缺口

0. 低代码定位边界必须落成代码和门禁。下一步收口必须实现：系统配置入口保护矩阵、`developer_draft` / `tenant_runtime` / `product_release` 来源标识、普通业务用户与管理员配置入口隔离、产品发布菜单不得依赖不可重放手工数据库状态的发布门禁。
1. 表单配置写入时统一处理 `role_group_ids` 与正式 `role_key` 的边界。已收敛：业务配置保存、查询、版本、回滚等统一作用域入口拒绝 `role_group_ids`，避免旧角色组输入被误认为正式配置作用域；低代码表单批量保存返回 `business_config_boundary`，明确正式归属、兼容写入和非用户偏好边界。
2. 表单低代码草稿输入统一从当前运行时契约读取，不再混用 legacy `objects/layout/rules` 作为主输入。已开始收敛：字段顺序/可见性优先使用 `view_orchestration.views.form.fields`，保存时同步写入 `view_orchestration.views.form.layout`；legacy `objects` 只做兜底和历史草稿兼容；新保存的兼容草稿下沉到 `legacy_lowcode_draft`。
3. 保存表单设置时，避免无变化字段被重写，防止“只改布局导致字段顺序变化”。已开始收敛：前端只提交变化项，后端支持 visibility-only 保存。
4. 运行时配置差异需要可追踪。已开始收敛：page governance 会透传正式契约字段数和被正式契约跳过的 legacy policy 字段，前端 HUD 可直接显示。
5. 表单配置需要后端审计接口。已开始收敛：`ui.business_config.form.audit` 输出正式契约字段、正式 layout 字段、字段顺序对齐状态、legacy policy 字段、跳过字段和仍生效字段。
6. 菜单配置补版本和生效报告。已开始收敛：`ui.menu_config.audit` 可输出当前公司/用户组实际命中的菜单 policy 和统计；菜单保存会镜像 `menu_orchestration.v1` 到正式契约并发布版本；`ui.menu_config.versions` 可读取版本摘要；`ui.menu_config.rollback` 可从指定历史版本恢复 policy；运行时 overlay 优先从已发布 `ui.business.config.contract.menu_orchestration` 读取，缺失时回退 policy。
7. 列表/搜索配置新增业务级配置入口，严格区别个人偏好。
   已开始收敛：`ui.business_config.list_search.audit` 可报告业务列表列、搜索筛选、搜索分组配置，并明确个人偏好是 `ui_only`；`ui.business_config.list_search.set` 可写入业务默认列表/搜索配置。
8. 配置覆盖需要系统扫描入口。
   已开始收敛：`ui.business_config.coverage.scan` 可按 action/模型扫描表单、列表、搜索业务配置覆盖缺口、运行时有效发布配置缺口及分类原因、菜单入口缺口和个人偏好边界信号；工作台提供全量扫描入口，扫描行输出配置/发布/运行时证据、运行页面路由、严重级别和结构化 `code/target/priority` 整改动作，摘要输出单一验收结论、严重级别与整改动作统计；`ui.business_config.coverage.bootstrap_missing` 可批量固化表单/列表/搜索缺口；`smart_construction_core` 升级迁移会执行系统根菜单和代表角色补齐；`make verify.business_config.unit` 覆盖默认用户语言、低代码后端 handler、工作台扫描和菜单配置审计；`make verify.business_config.coverage` 作为本地/开发服务器升级后的强验收门禁；`make verify.business_config.low_code_acceptance` 验证业务配置管理员默认路径的页面搜索、页面选择、预览、列表/搜索三类 tab、列表/搜索草稿编辑、表单字段点选/拖拽/显示隐藏/新增字段、检查效果和返回上下文，并落盘桌面/移动截图、检查默认路径不暴露治理/技术话术、高级设置可显式打开治理工具、390px 视口无横向溢出、浏览器 error/warning 为空；`make verify.business_config.full_acceptance` 先跑后端低代码单测，再用浏览器批量打开运行页面样本，并串联低代码用户路径验收，补页面级和配置级证据。系统根菜单扫描只能覆盖标准 ORM 菜单 action，运行时可见菜单仍必须保留代表角色验收。
