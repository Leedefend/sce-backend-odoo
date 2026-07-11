# 产品化系统收口专题 v1

## 分支与目标

专题分支：`topic/productization-system-closure`。

本专题目标不是继续证明“底层数据基本可用”，而是把系统推进到可以面向真实用户交付的产品基线。收口结论必须同时覆盖用户体验、后端契约边界、低代码配置边界、业务办理闭环、附件闭环、发布链路和可重复验收证据。

## 产品化定义

产品化系统必须满足以下条件：

1. 用户从登录后能清楚理解当前企业、当前项目、当前角色和下一步任务。
2. 主导航、配置中心、菜单配置、页面标题和面包屑使用同一套后端发布菜单口径。
3. 前端只消费后端契约和正式产品配置，不合成业务菜单、不推断低代码生效规则、不写回 Odoo 分组菜单。
4. 列表、搜索、表单、详情、附件、上传、保存、返回、刷新、错误和空态都有用户可理解的交互。
5. 业务办理页面和低代码配置页面共享统一页面结构、间距、反馈区、主动作和产品语言。
6. 日常开发服务器和生产服务器只能从仓库主线或明确专题发布分支升级，发布后必须保留结构化验收证据。

## 边界锁定

### 后端权威边界

- Odoo 原生结构解析只输出原生视图、动作、菜单、字段和权限事实。
- `smart_core` 负责通用契约管线、意图入口、运行时装配和平台级边界守卫。
- `smart_construction_core` 负责行业产品菜单、行业业务模型、行业配置扩展和项目级业务上下文。
- 项目隔离契约由后端输出；前端只渲染 `project_context`，不能把“当前项目”降级成通用记录上下文。

### 低代码边界

- 菜单配置展示口径必须与主导航展示口径一致。
- 分组菜单是导航组织能力，真实可配置对象必须由后端契约明确给出。
- 表单、列表、搜索的产品化配置必须进入正式业务配置契约，不能由前端临时逻辑决定。
- 用户配置的是产品发布口径，不是 Odoo 底层全部菜单、隐藏菜单或技术菜单。

### 前端边界

- AppShell 负责系统壳层、导航、项目上下文、角色入口和通用页面容器。
- 页面组件负责契约渲染和用户交互，不拥有业务事实来源。
- 前端允许做通用布局、状态展示、空态、错误提示和响应式适配，不允许写业务模型决策。
- 所有用户可见页面必须使用产品页面结构：Header、Toolbar、Summary、Main Surface、Primary Actions、Feedback Layer。

## 覆盖面

本专题收口至少覆盖：

- 登录与初始化：账号、数据库、角色、企业、项目上下文。
- 主导航：产品菜单、配置中心、项目隔离、角色入口、搜索菜单。
- 业务列表：项目台账、收入合同台账、财务台账、物资与分包台账。
- 业务表单：支付申请、材料入库、施工日志、分包申请、合同相关办理。
- 详情阅读：主对象身份、状态、金额、关联对象、附件和历史信息。
- 低代码配置：菜单配置、配置工作台、表单配置、列表搜索配置、发布反馈。
- 用户可见面视图验收：所有主导航可进入页面必须进入浏览器扫描，生成截图、横向溢出检查、渲染错误检查和控制台错误检查。
- 附件闭环：生产附件可打开/下载，业务办理附件可上传，且使用生产自身附件系统。
- 运维发布：本地、日常开发服务器、生产服务器升级链路和只读生产验收。

## 阶段推进

### P0 基线与门禁

- 固化本专题文档和总控 guard。
- 跑通已有用户体验、页面结构、菜单边界、项目上下文、低代码和生产发布门禁。
- 输出当前可交付缺口清单，禁止只给“通过”结论。

### P1 用户操作走查

- 用浏览器逐一覆盖高频用户任务。
- 每个任务记录首屏、主动作、保存/返回、错误/空态、加载性能和用户语言。
- 问题按信息架构、任务流、页面结构、语言、数据理解、性能、移动端、权限分类。

### P2 批量产品化优化

- 同类问题批量修复，避免一页一页零散调整。
- 页面结构和交互模式优先抽象到统一产品样式体系。
- 后端契约缺口优先补后端，前端只做通用消费。

### P3 环境闭环

- 本地通过后升级日常开发服务器，执行同口径浏览器验收。
- 生产部署只从权威 Git 主线或明确发布分支升级。
- 生产环境仅执行只读验证，写入类验证必须在本地或日常开发服务器完成。

## 收口门禁

本专题最低收口命令：

```bash
make verify.productization.system_closure.topic_guard
make verify.system_user_experience.quick
make verify.business_config.unit
make verify.business_config.config_workbench_operation_quick
make verify.business_config.full_acceptance
make verify.system_user_experience.visible_surface_visual_coverage
make verify.system_user_experience.full_browser
make verify.formal_business.release_gate
make verify.business_capability.productization_p1
make verify.business_system.usability_readiness
```

生产发布后追加：

```bash
make verify.production_git.authority.guard
make verify.project_context.selector_product_boundary.guard.prod
make verify.formal_menu.runtime_no_legacy_carrier_guard.prod
make verify.formal_list_surface.no_test_placeholder_guard.prod
make verify.business_system.usability_readiness.prod
make history.attachment.custody.probe.prod
make verify.legacy_online_attachment.custody.evidence.prod
make verify.legacy_attachment.frontend_browser.sample_manifest.prod
make verify.attachment_upload.surface_manifest.prod
```

## 收口结论格式

最终结论必须同时给出：

- 分支、提交、部署环境和版本。
- 覆盖的用户角色、页面类型、业务任务和低代码任务。
- 浏览器验收结果与结构化报告路径。
- 已修复的问题类型和仍保留的 backlog。
- 本地、日常开发服务器、生产服务器的验证结论。
- 是否具备交付用户使用的条件。
