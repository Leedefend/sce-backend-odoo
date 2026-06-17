# 低代码配置能力矩阵

| 能力 | 当前承载 | 当前入口 | 正式归属 | 当前状态 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 表单字段显示/隐藏 | `ui.form.field.policy` + `ui.business.config.contract.view_orchestration` | 当前表单“表单设置” | `ui.business.config.contract` | 可用但双写 | P1 收敛为契约为准 |
| 表单字段顺序 | `ui.form.field.policy.sequence` + `view_orchestration.views.form.fields` | 当前表单“保存表单设置” | `ui.business.config.contract` | 可用但易受输入源影响 | P1 统一运行时契约输入 |
| 表单字段标签 | `ui.form.field.policy.label` + `view_orchestration.views.form.fields[].label` | 当前表单内联修改 | `ui.business.config.contract` | 可用，写入已镜像契约，版本摘要和差异按业务标签对比 | P1 继续压缩 legacy policy 兼容层 |
| 表单字段新增 | `ui.form.custom.field.wizard` + `ir.model.fields` + field policy | 当前表单“添加字段” | 平台元数据 + `ui.business.config.contract` | 可用，intent 支持 dry-run 预检且正式执行后镜像契约 | P1 明确字段元数据回滚边界 |
| 表单布局/分组 | `view_orchestration.views.form.layout` + 前端草稿 | 当前表单低代码区域 | `ui.business.config.contract` | 部分可用，保存预检已约束正式 layout schema | P1 继续把编辑入口收敛到正式 layout |
| 菜单显隐 | `ui.menu.config.policy.visible` + `ui.business.config.contract.menu_orchestration` | 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、版本列表、指定版本回滚，运行时仍读 policy | P4 纳入统一配置工作台 |
| 菜单改名 | `ui.menu.config.policy.custom_label` + `ui.business.config.contract.menu_orchestration` | 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、版本列表、指定版本回滚，运行时仍读 policy | P4 纳入统一配置工作台 |
| 菜单排序/移动 | `ui.menu.config.policy.sequence_override/target_parent_menu_id` + `ui.business.config.contract.menu_orchestration` | 菜单配置面板 / `ui.menu_config.audit` / `ui.menu_config.versions` / `ui.menu_config.rollback` | `ui.business.config.contract` | 可用，有页面生效检查、版本列表、指定版本回滚，运行时仍读 policy | P4 纳入统一配置工作台 |
| 列表个人列偏好 | `sc.user.view.preference` | 列表选择列 | 用户个人偏好 | 可用 | 保持 UI-only |
| 业务默认列表列 | `view_orchestration.views.tree.columns` | `/admin/business-config` / `ui.business_config.list_search.audit/set` | `ui.business.config.contract` | 可用，工作台可按作用域查看/保存，已纳入覆盖扫描、批量补齐、升级迁移固化、运行页面跳转和 `make verify.business_config.full_acceptance` 浏览器批量验收证据 | P5 扩展配置差异分析 |
| 搜索筛选配置 | `view_orchestration.views.search.filters/group_by` | `/admin/business-config` / `ui.business_config.list_search.audit/set` | `ui.business.config.contract` | 可用，工作台可按作用域查看/保存，已纳入覆盖扫描、批量补齐、升级迁移固化、运行页面跳转和 `make verify.business_config.full_acceptance` 浏览器批量验收证据 | P5 扩展配置差异分析 |
| 分析视图配置 | `view_orchestration` pivot/graph/calendar/dashboard | `/admin/business-config` 分析视图卡片 / 版本面板 | `ui.business.config.contract` | 后端支持，工作台已可发现分析页面、查看分析视图配置版本、显示分析项摘要和版本差异并预览页面；复杂编辑器后置 | P5 扩展分析视图编辑器 |
| 配置发布/回滚 | `ui.business.config.contract.version` | 表单低代码契约按钮 / 菜单配置 / 工作台版本面板 | 平台核心 | 发布追踪可用，菜单支持指定版本回滚，工作台默认路径可查看当前页面配置版本、回滚上一版并回滚到指定版本，历史版本行显示相对当前版本的字段/列/筛选/分组差异摘要；作用域和业务契约解释只在高级设置中展示；覆盖扫描行可直接打开运行页面，完整验收会批量打开运行页面样本 | P5 扩展细粒度配置差异分析 |
| 配置工作台摘要 | `ui.business_config.surface.get` / `ui.business_config.contract.versions` | 业务配置中心“业务配置工作台” / 平台管理员侧栏 / `/admin/business-config` | 平台核心 + 行业入口 | 页面可用，已接表单、列表/搜索、分析视图、菜单入口、作用域选择、默认版本记录、全量扫描入口和可发现入口 | P5 补整改闭环 |
| 配置验收报告 | `ui.business_config.coverage.scan` / `ui.business_config.coverage.bootstrap_missing` / `make verify.business_config.unit` / `make verify.business_config.coverage` / `make verify.business_config.low_code_acceptance` / `make verify.business_config.full_acceptance` | `/admin/business-config` | 平台工具 | 默认按当前用户可见菜单 action 扫描表单/列表/搜索契约覆盖缺口、运行时有效发布契约缺口及分类原因、菜单入口缺口和个人偏好边界信号；扫描行输出运行页面路由并支持工作台直接打开；工作台支持表单/列表/搜索缺口批量补齐；升级迁移会按系统根菜单和代表角色自动固化缺口；门禁命令按代表角色验证运行态无缺口并落盘运行页面样本；后端单测覆盖表单/列表/搜索 intent 参数、字段有效性、个人偏好边界和工作台扫描；低代码用户路径验收会用浏览器验证业务配置管理员能搜索页面、选择页面、查看配置版本记录、预览页面、配置列表/搜索三类 tab、拖拽/点选表单字段、调整显示隐藏和顺序、新增字段、检查效果并返回配置上下文；默认路径不暴露治理/技术话术，高级设置显式打开后必须能展示作用域字段和高级治理视图；低代码验收报告会落盘关键截图，并在 390px 视口检查配置页无横向溢出、浏览器 error/warning 为空；完整验收命令会先跑后端低代码单测，再构建前端静态资源、跑覆盖门禁、运行页面浏览器样本和低代码用户路径验收。系统根菜单扫描只能覆盖标准 ORM 菜单 action，运行时可见菜单仍必须保留代表角色验收 | P5 扩展分析视图 |

## 作用域对齐目标

| 作用域 | 正式契约字段 | 兼容字段 | 说明 |
| --- | --- | --- | --- |
| 模型 | `model` | `model` | 必填 |
| 视图类型 | `view_type` | `view_type` | `list` 归一为 `tree` |
| 动作 | `action_id` | `action_id` | 当前页面配置必须带 action |
| 视图 | `view_id` | `view_id` | 有明确视图时必须保留 |
| 公司 | `company_id` | `company_id` | 默认当前公司，可为空表示全局 |
| 角色 | `role_key` | `role_group_ids` | 业务配置契约接口拒绝旧 `role_group_ids`，必须使用 `role_key`；旧字段只保留在 legacy policy 审计输出 |
| 用户 | 不进入业务契约 | `sc.user.view.preference.user_id` | 只用于个人 UI 偏好 |

## 优先修复缺口

1. 表单配置写入时统一处理 `role_group_ids` 与正式契约 `role_key` 的边界。已收敛：业务配置契约保存、查询、版本、回滚等统一作用域入口拒绝 `role_group_ids`，避免旧角色组输入被误认为正式契约作用域。
2. 表单低代码草稿输入统一从当前运行时契约读取，不再混用 legacy `objects/layout/rules` 作为主输入。已开始收敛：字段顺序/可见性优先使用 `view_orchestration.views.form.fields`，legacy `objects` 只做兜底和历史草稿兼容；新保存的兼容草稿下沉到 `legacy_lowcode_draft`。
3. 保存表单设置时，避免无变化字段被重写，防止“只改布局导致字段顺序变化”。已开始收敛：前端只提交变化项，后端支持 visibility-only 保存。
4. 运行时配置差异需要可追踪。已开始收敛：page governance 会透传正式契约字段数和被正式契约跳过的 legacy policy 字段，前端 HUD 可直接显示。
5. 表单配置需要后端审计接口。已开始收敛：`ui.business_config.form.audit` 输出正式契约字段、legacy policy 字段、跳过字段和仍生效字段。
6. 菜单配置补版本和生效报告。已开始收敛：`ui.menu_config.audit` 可输出当前公司/用户组实际命中的菜单 policy 和统计；菜单保存会镜像 `menu_orchestration.v1` 到正式契约并发布版本；`ui.menu_config.versions` 可读取版本摘要；`ui.menu_config.rollback` 可从指定历史版本恢复 policy。
7. 列表/搜索配置新增业务级配置入口，严格区别个人偏好。
   已开始收敛：`ui.business_config.list_search.audit` 可报告业务列表列、搜索筛选、搜索分组契约，并明确个人偏好是 `ui_only`；`ui.business_config.list_search.set` 可写入业务默认列表/搜索契约。
8. 配置覆盖需要系统扫描入口。
   已开始收敛：`ui.business_config.coverage.scan` 可按 action/模型扫描表单、列表、搜索业务契约覆盖缺口、运行时有效发布契约缺口及分类原因、菜单入口缺口和个人偏好边界信号；工作台提供全量扫描入口，扫描行输出配置/发布/运行时证据、运行页面路由、严重级别和结构化 `code/target/priority` 整改动作，摘要输出单一验收结论、严重级别与整改动作统计；`ui.business_config.coverage.bootstrap_missing` 可批量固化表单/列表/搜索缺口；`smart_construction_core` 升级迁移会执行系统根菜单和代表角色补齐；`make verify.business_config.unit` 覆盖低代码后端 handler 和工作台扫描单测；`make verify.business_config.coverage` 作为本地/开发服务器升级后的强验收门禁；`make verify.business_config.low_code_acceptance` 验证业务配置管理员默认路径的页面搜索、页面选择、预览、列表/搜索三类 tab、列表/搜索草稿编辑、表单字段点选/拖拽/显示隐藏/新增字段、检查效果和返回上下文，并落盘桌面/移动截图、检查默认路径不暴露治理/技术话术、高级设置可显式打开治理工具、390px 视口无横向溢出和浏览器 error/warning 为空；`make verify.business_config.full_acceptance` 先跑后端低代码单测，再用浏览器批量打开运行页面样本，并串联低代码用户路径验收，补页面级和配置级证据。系统根菜单扫描只能覆盖标准 ORM 菜单 action，运行时可见菜单仍必须保留代表角色验收。
