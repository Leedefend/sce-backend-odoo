# 自定义前端成熟产品全量审计 v1

## 执行摘要

本审计修正版基于 `origin/main@7c21f9e1d8bec136812081d6c7a3cce9f2f71c50`、固定验收数据库 `sc_frontend_acceptance`、独立验收前端和 Odoo runtime。审计只读，不执行创建、编辑、提交、审批、删除、导入、发布或付款操作。付款菜单、列表和详情属于可安全巡检的导航表面；仅页面内写操作被标记，不以“付款”文字过滤导航。

已有真实证据确认：四个固定账号可登录；finance 公司 A/B 数据隔离；project member 仅可见项目 A；B/C 敏感业务记录访问被拒绝；付款列表基础旅程通过。

修正版按权威导航递归展开容器、可导航叶节点和无法解析叶节点，并记录实际 route 与组件。四角色叶节点均完成 1440×900 只读巡检；J01–J08 生成独立结论文件，未由表面巡检冒充深度旅程通过。

## 覆盖统计

| 项目 | 结果 |
| --- | --- |
| 角色登录检查 | 4/4 |
| 全表面机器记录 | 115 条可导航叶节点 |
| 角色叶节点 | finance 44；project member 51；PM 14；owner 6 |
| 叶节点可达率 | 4/4 角色均 100%（115/115） |
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
| 信息架构 | 3 | 115 个权威叶节点可解析并可达 |
| 视觉层级 | 3 | FE-P00/P01 已建立 token 与壳层基线，跨 surface 仍有漂移 |
| 一致性 | 2 | 列表、详情、表单 contract surface 尚未完成统一证据 |
| 信息密度 | 3 | 桌面列表可用，完整业务域未验证 |
| 文案 | 2 | 已发现 record 技术标题回退风险 |
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

1. record 路由技术标题回退。
2. 深度旅程（J01–J08）仍需独立浏览器步骤证据。
3. 1280/390、可访问性和性能尚未达到全量证据门槛。
4. 结算/付款详情关系链缺少完整浏览器证据。
5. 全量可访问性没有证据。
6. 全量性能没有基线。

## 证据索引

- `artifacts/frontend-audit/full-surface-report.json`
- `artifacts/frontend-audit/full-surface-report.csv`
- `artifacts/frontend-audit/journeys.json`
- `artifacts/frontend-audit/responsive-report.json`
- `artifacts/frontend-audit/accessibility-report.json`
- `artifacts/frontend-audit/performance-report.json`
- `docs/frontend_productization/frontend_surface_inventory_v1.csv`
- `docs/frontend_productization/frontend_maturity_backlog_v1.csv`
- `docs/frontend_productization/frontend_delivery_readiness_v1.md`
- `scripts/verify/frontend_productization_fixture_browser.mjs`

## 审计边界

本任务未修改产品页面、样式、后端、API、权限、fixture、数据库或 runtime；后续修复分支必须由本审计 backlog 重新编排。

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
