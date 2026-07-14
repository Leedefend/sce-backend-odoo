# 自定义前端成熟产品全量审计 v1

## 执行摘要

当前审计基于 FE-B02R 基线 `origin/main@803453c965`、固定验收数据库 `sc_frontend_acceptance`、独立验收前端和 Odoo runtime。权威导航分母已冻结为 70；历史 115 个表面和 FE-B02 后的临时 74 个表面只作为问题演进背景，不再参与当前通过率计算。

已有真实证据确认：四个固定账号可登录；finance 公司 A/B 数据隔离；project member 仅可见项目 A；B/C 敏感业务记录访问被拒绝；付款列表基础旅程通过。

Page Identity 修正版按权威导航递归展开容器和业务叶节点，并记录 menu/action XML ID、实际 route、组件、heading、浏览器标题、面包屑、identity source、HTTP、console/pageerror 与技术回退。四角色 70 个叶节点均完成 1440×900 只读巡检；另有 16 个列表、详情、表单、状态和上下文切换深度场景。

## 覆盖统计

| 项目 | 结果 |
| --- | --- |
| 角色登录检查 | 4/4 |
| 全表面机器记录 | 70 条权威可导航叶节点 |
| 角色叶节点 | finance 42；project member 9；PM 14；owner 5 |
| 叶节点可达率 | 4/4 角色均 100%（70/70） |
| 页面身份通过率 | 70/70；通用“业务动作”、技术模型名、裸 ID、undefined/null 均为 0 |
| 1440×900 | 全部叶节点已巡检并截图 |
| 1280×800 | 独立核心旅程证据未在本轮表面脚本执行，标记 N/A |
| 390×844 | 独立代表页面证据未在本轮表面脚本执行，标记 N/A |
| J01–J08 | 8/8 有独立结论；表面脚本不执行写操作，深度旅程状态见 journeys.json |

## 架构事实

- `/a/:actionId` → `ActionViewShell` → `ActionView` → `ListPage`。
- `/r/:model/:id`、`/f/:model/:id` → `ContractFormPage`。
- 页面标题、字段 label、关系字段和权限状态应来自 contract/native descriptor/access policy。
- 通用渲染器不应根据业务模型复制页面。
- 普通用户不应看到 model、action、record id、contract、trace 等技术信息。

## 成熟度评分（仅计入已测样本）

| 维度 | 当前分数 | 依据 |
| --- | ---: | --- |
| 信息架构 | 3 | 70 个当前权威叶节点可解析、可达且具备稳定页面身份 |
| 视觉层级 | 3 | FE-P00/P01 已建立 token 与壳层基线，跨 surface 仍有漂移 |
| 一致性 | 2 | 列表、详情、表单 contract surface 尚未完成统一证据 |
| 信息密度 | 3 | 桌面列表可用，完整业务域未验证 |
| 文案 | 3 | 70 个导航表面和 16 个深度场景均使用契约驱动业务标题，技术回退为 0 |
| 状态反馈 | 3 | 加载/空/错/权限已有基础分支，统一度需审计 |
| 操作安全 | 3 | 权限隔离有证据，写操作全量审计未完成 |
| 导航 | 3 | 递归导航和动态 action/menu route 已有全量表面证据 |
| 响应式 | N/A | 本轮未执行 1280/390 全量样本，不纳入综合分 |
| 可访问性 | N/A | 本轮未引入可访问性工具，不纳入综合分 |
| 性能感知 | N/A | 仅保存页面加载耗时样本，不纳入综合分 |
| 专业可信度 | 2 | 已有产品化基础，但尚不足以宣称全量成熟 |

## P0/P1/P2/P3

- P0：0 个已确认。
- P1：1 个已确认产品问题；2 个为审计工具/证据阻塞，不计入产品 P1。
- P2：3 个体验和后续证据问题。
- P3：待 1280/390、可访问性和性能专项样本后评估。

## 最严重问题

1. 结算、付款和合同之间的业务关系链仍缺少完整用户操作闭环。
2. 1280/390、可访问性和性能尚未达到全量证据门槛。
3. 全量可访问性没有证据。
4. 全量性能没有基线。

## 证据索引

- `artifacts/frontend-page-identity/full-surface-report.json`
- `artifacts/frontend-page-identity/full-surface-report.csv`
- `artifacts/frontend-page-identity-deep/report.json`
- `artifacts/frontend-audit/journeys.json`
- `artifacts/frontend-audit/responsive-report.json`
- `artifacts/frontend-audit/accessibility-report.json`
- `artifacts/frontend-audit/performance-report.json`
- `docs/frontend_productization/frontend_surface_inventory_v1.csv`
- `docs/frontend_productization/frontend_maturity_backlog_v1.csv`
- `docs/frontend_productization/frontend_delivery_readiness_v1.md`
- `scripts/verify/frontend_productization_fixture_browser.mjs`

## 原始审计边界

原始 FE-AUDIT-01R 仅生成证据，没有修改产品页面、样式、后端、API、权限、fixture、数据库或 runtime；后续 FE-B02/FE-B02R/FE-B03 分支按 backlog 分别完成角色边界、导航可达性和页面身份收口。

## FE-B02 角色可信边界事实

深度旅程审计后确认，项目成员账号原先仅携带项目读取/业务发起能力，但角色解析将 `group_sc_cap_project_read` 误归为 `pm`，前端最终回退显示为 owner；同一错误还使敏感财务、税务、人事和付款菜单进入权威导航。

最终权威调用链如下：

1. fixture 用户 `demo_role_project_a_member` 由 `smart_construction_demo` 固定为内部用户，持有 `group_sc_cap_project_read`、`group_sc_cap_business_initiator`，并通过 `mail.followers` 只关联 FE Project A；finance/PM/owner 分别持有 `smart_construction_custom.group_sc_role_finance/pm/owner`。
2. `smart_construction_core.smart_core_identity_profile` 将角色组与能力组交给 `smart_core.identity.IdentityResolver`；显式 finance/PM/owner 先按正式角色组解析，仅无更高显式角色的 project-read 用户解析为 `project_member`，因此 PM 不会被降级为项目成员。
3. `IdentityResolver.build_role_surface` 产出角色标签、允许菜单根和基于 menu XML ID/action XML ID/model 的禁止标识；行业敏感模型事实保留在 `smart_construction_core`，`smart_core` 仅执行通用标识投影。
4. release navigation 由 `IdentityResolver.filter_nav_for_role_surface` 裁剪；delivery navigation 由 `DeliveryEngine -> MenuService.build_nav` 使用同一 role surface 再裁剪，二者共同进入 `system.init` 的 `release_navigation_v1.nav` 与 `delivery_engine_v1.nav`。
5. 前端 `session.loadAppInit` 优先消费 `release_navigation_v1.nav`，其次消费 `delivery_engine_v1.nav`，并在角色/公司初始化后替换 `menuTree`；退出登录清空 role/nav/activity/cache，公司切换重新执行 project-context 搜索与 `system.init`。
6. `/m/:menuId`、`/a/:actionId` 及带 action/menu 上下文的 record 路由在全局 router guard 中先对权威 `menuTree` 校验；未授权目标在业务组件挂载和 action/data 请求前进入公共“无权访问”状态并提供安全返回。无 action/menu 上下文的越权记录仍由后端 ACL/record rule 返回 403，由表单错误契约归一化，前端不把空数据当作成功。

本修复只收紧产品入口与直达导航权威，不修改 ACL、record rule、fixture 业务授权、金额、状态机或字段。项目成员在后端现行规则允许时仍可读取 Project A 下的部分项目/合同业务事实，但不会获得财务管理入口；Project B/C 记录继续由 record rule 拒绝。

验收结果：角色/导航定向 Odoo 测试 4 个方法通过；固定浏览器报告 18 项检查通过。J02 完成 FE Company A→B→A 且记录集合和 company_id 请求上下文同步切换；J03 完成角色标签、权威导航、项目 A/B/C、动态 action/menu/record 直达、HTTP 403、无敏感 payload、logout 后 PM/owner 角色缓存隔离。证据路径为 `artifacts/playwright/frontend-productization-fixture/report.json`，截图目录同级。

## FE-B02R 导航可达性与权限契约事实

FE-B02 合并后的初始权威导航为 74 个叶节点（finance 44、project member 10、PM 14、owner 6）。其中四个节点能进入 release/delivery projection，但 action 首屏的 `api.data.list` 在 `/api/v1/intent` 首次返回 403；这不是合法空列表。失败层级和裁决如下：

| 角色/入口 | menu XML ID | action XML ID / 类型 / 模型 / 视图 | 导航与后端证据 | 产品应保留？ | 处理 |
| --- | --- | --- | --- | --- | --- |
| finance / 计划管理 | `smart_construction_core.menu_sc_plan` | `smart_construction_core.action_sc_plan` / `ir.actions.act_window` / `sc.plan` / `tree,form` | menu/action 的 broad group 是 `group_sc_internal_user`，模型有 `access_sc_plan_read`；但正式 capability `construction.plan.manage` 只授权 `pm/executive`，finance 无职责与 capability 证据，403 属 action capability/role-scope 拒绝 | 否 | 以稳定 menu/action XML ID 从 finance role surface 移除 |
| finance / 计划汇报 | `smart_construction_core.menu_sc_plan_report` | `smart_construction_core.action_sc_plan_report` / `ir.actions.act_window` / `sc.plan.report` / `tree,form` | menu/action 的 broad group 是 `group_sc_internal_user`，模型有 `access_sc_plan_report_read`；但正式 capability `construction.plan.report` 只授权 `pm/executive`，finance 无职责与 capability 证据，403 属 action capability/role-scope 拒绝 | 否 | 以稳定 menu/action XML ID 从 finance role surface 移除 |
| project member / 投标报名管理 | `smart_construction_core.menu_sc_tender_registration` | `smart_construction_core.action_sc_tender_registration` / `ir.actions.act_window` / `tender.bid` / `tree,form` | menu/action 标注 `group_sc_cap_project_read`，但 `tender.bid` ACL 只有 project manager、project user、config admin，没有 project-read ACL；capability registry 也没有项目成员投标职责证据，首次在模型访问层拒绝 | 否 | 从 project member role surface 移除，模型 ACL 保持不变 |
| owner / 投标报名管理 | `smart_construction_core.menu_sc_tender_registration` | `smart_construction_core.action_sc_tender_registration` / `ir.actions.act_window` / `tender.bid` / `tree,form` | owner 的产品 project surface 继承了 broad menu group，但没有 `tender.bid` 模型 ACL或专门投标 capability；角色名称和当前菜单可见均不构成扩权依据，首次在模型访问层拒绝 | 否 | 从 owner role surface 移除，模型 ACL 保持不变 |

投影链保持单一：`core_extension_policy_maps.ROLE_SURFACE_OVERRIDES` 提供行业角色的 menu/action XML ID blocklist，`IdentityResolver.filter_nav_for_role_surface` 生成 release navigation，`MenuService._filter_role_surface_nodes` 生成 delivery navigation，二者继续由同一 `system.init` 契约交付。未新增前端隐藏、中文关键词过滤、fixture 账号判断或第二套权限推断，也未修改 ACL、record rule、fixture 授权或数据范围。

运行时守卫 `verify.frontend.navigation.access` 递归读取四角色权威导航并逐叶验证 route 解析、action 初始化、首屏契约、HTTP、结构化错误 payload、console 和 pageerror；合法 200 空列表可通过，权限页、403、伪空列表和初始化错误均失败。最终动态结果为：

```text
initial_authoritative_leaf_count = 74
removed_as_unauthorized = 4
retained_after_authorized_fix = 0
final_authoritative_leaf_count = 70
reachable = 70
forbidden = 0
unresolved = 0
role_leaf_counts = finance:42, project_member:9, pm:14, owner:5
```

四个被移除节点的 action 与 menu 直达均进入统一“无权访问”状态并提供“返回已授权的工作区”，没有业务记录数组、非零金额或 fixture 记录标识泄露。FE-B02 回归再次通过 18 项浏览器检查：finance 付款/结算保留，公司 A→B→A 列表和 `company_id` 同步刷新；project member 仍显示“项目成员”、只见 Project A、敏感入口无回升，action 876/menu 606/越权记录继续拒绝；logout 后 PM/owner 导航未复用前一角色缓存。证据为 `artifacts/playwright/frontend-navigation-access/report.json` 与 `artifacts/playwright/frontend-productization-fixture/report.json`。后续 FE-B03 的权威巡检分母冻结为 70，不再使用历史 115。

## FE-B03 页面身份契约事实

原页面身份链在 router 和 AppShell 中按路由类型拼接通用标题；action 列表没有把 menu/action 的正式中文名称提升为统一页面身份，详情异步读取前只能看到技术 model 与数据库 ID，多个页面组件又分别计算 heading、breadcrumb 与浏览器标题，因此直接刷新、异步完成、KeepAlive 快速切换、公司切换和 logout 后都可能出现通用“业务动作”、`model #id` 或上一上下文残留。

最终权威数据链如下：

1. Odoo menu/action metadata 由 `system.init` 的 release/delivery navigation 交付；menu 正式中文名称来自节点 `label/name/title`，action 场景名称按 `ui_title -> scene_title -> menu_title -> name` 读取，model 业务名称来自 action contract 的 `model_label`。
2. record 详情契约在 `api.data.get`/form load 中显式读取 `display_name`；若缺失，resolver 只按 contract 声明的主标识字段和通用业务标识字段取值，不建立模型名称到中文标题的前端字典。
3. `resolveRoutePageIdentity` 在全局路由 guard 完成后用 menu tree、action metadata 和 route state 建立初始 identity；详情页此时先得到带业务上下文的 loading identity。
4. `ActionView`、`RecordView` 和通用 `ContractFormPage` 在 action/record contract 异步到达后只向同一个 runtime 发布权威输入；`PageIdentityCoordinator` 以 `route.fullPath` 拒绝旧 route 的迟到结果，避免快速切换记录、公司或角色时复用旧标题。
5. `resolveProductPageIdentity` 是唯一最终解析器，输出 `title/subtitle/documentTitle/breadcrumbs/source`；AppShell、通用页面和 PermissionDenied/NotFound 只消费该结果。仓库业务页面仅由 `App.vue` 一个 watcher 同步 `document.title`，logout 清空 runtime 并恢复登录标题。

标题优先级为：列表 `action -> menu -> model_label -> 业务列表`；详情 `record.display_name -> contract 主标识 -> action/menu + 详情 -> model_label + 详情 -> 记录详情`；新建为 `新建 + action/menu/model`；编辑为 `编辑 + record display_name`，否则 `编辑 + 业务对象`。loading/empty/error 保留已授权业务上下文；denied 和 not-found 丢弃 record identity，分别使用安全的无权状态和“记录不存在”，从而不泄露目标记录名称。最终浏览器标签统一为 `{页面标题} - 智能施工企业管理平台`。

面包屑由当前 menu 的权威祖先路径、action 和 record identity 归一化生成。只有节点本身存在真实 route/action/scene target 才带链接；纯分组节点为文本；当前节点永不链接自身。归一化会删除重复节点以及技术模型名、裸数字 ID、action/menu/record ID 和空值；无权限页不会加入目标 record 名称，无法证明祖先时允许缩短而不伪造层级。

最终机器巡检结果：finance 42、project member 9、PM 14、owner 5，共 `authoritative_leaf_count=70`、`scanned=70`、`reachable=70`、`identity_pass=70`；menu/action XML ID 缺失为 0，通用“业务动作”标题、技术模型标题、裸 ID、undefined/null、403、unresolved 均为 0，70 个导航表面的 identity source 均为 action。证据为 `artifacts/frontend-page-identity/full-surface-report.json` 和同步生成的 `docs/frontend_productization/frontend_surface_inventory_v1.csv`。

16 个深度场景全部 PASS：项目列表/Project A 详情、合同列表/详情由具备正式访问职责的 PM 验证；finance 验证结算、付款申请、付款执行的列表/详情以及合法新建、编辑、404 和公司 A→B→A；project member 验证 logout 后不残留 finance identity 以及敏感 action 的安全拒绝。每个常规页面均检查 heading、`document.title`、breadcrumb、identity source、刷新稳定性、console/pageerror 和 HTTP；权限拒绝报告同时确认响应不包含目标记录名称。项目成员详情附属请求仍受既有权限边界约束，本分支没有为深度场景修改 ACL、record rule、role policy、fixture 或导航。
