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

## FE-B04 合同—结算—付款工作区实施前契约事实

验收库 `sc_frontend_acceptance` 的只读运行时探针确认，资金链权威事实来自既有 Odoo 模型字段、`sc.workflow.contract.service` 和付款申请专用 intent；页面不得从显示值反算金额或只凭状态字符串推断操作。固定公司 A 链的事实矩阵如下：

| 对象 | 模型 / fixture | 当前状态与主标识 | 权威金额事实（CNY） | 上下游关系 | 合法操作与角色证据 |
| --- | --- | --- | --- | --- | --- |
| 项目 | `project.project` / `fe_project_a` | `FE Project A` | 无资金金额字段 | 下游合同 1 条 | finance 对项目主表受现有“负责人或关注者”记录规则限制；PM/project member 可读 Project A |
| 合同 | `construction.contract` / `fe_contract_a` | 已生效；`CONOUT2600001` / `FE-A Contract` | 含税原始金额 1130；最终合同价 1130；累计实付 1000 | 上游 Project A；下游结算 1 条 | finance/PM/owner 可读；状态操作继续由原 workflow contract 与模型方法控制 |
| 结算 | `sc.settlement.order` / `fe_settlement_a` | 批准；`FE-A-SET-001` | 行合计 1000；扣款 0；调整后付款基数 1000；付款申请占额 1000；剩余可占额 0；台账实际已付当前为 0 | 上游合同；下游付款申请 2 条 | finance/PM 可读；本分支不新增结算状态操作 |
| 付款申请 | `payment.request` / `fe_request_a_001` | 已批准；`FE-A-PR-001` | 申请/占额 1000；台账实际已付 0 | 上游合同、结算；下游付款执行 1 条；当前无台账 | finance 可读；专用 `payment.request.available_actions` 联合状态、方法、前置条件和角色组投影，执行统一走 `payment.request.execute` |
| 付款执行 | `sc.payment.execution` / `fe_execution_a` | 已付款；`FE-A-PE-001` | 计划/执行金额 1000；实付 1000 | 上游付款申请、合同；台账经付款申请关联 | finance 可读；既有 `action_confirm/action_paid/action_cancel` 受模型状态、审批与财务组共同保护，本分支不绕过为通用 write |
| 付款台账 | `payment.ledger` / 固定链当前 0 条 | 无独立业务编号；由付款申请完成或付款执行登记付款自动生成 | `amount` 是唯一台账实付事实 | 上游付款申请，结算由付款申请反查 | 仅后端 `_ensure_payment_ledger` 的受控上下文可创建；前端不得直接 create/write |

关系字段的原始 page/form contract 形态为 many2one `[id, display_name]` 或 one2many ID/行集合：合同 `project_id`，结算 `contract_id/payment_request_ids`，付款申请 `contract_id/settlement_id/ledger_line_ids`，付款执行 `payment_request_id/contract_id`。项目到合同、合同到结算、付款申请到执行没有完整的双向前端关系契约，必须由只读工作区契约在用户现有 record rule 内投影；无权记录不得先读取名称再禁用链接。

金额语义已经由 `operating_metrics` 冻结：`settlement_reserved_amount_map` 汇总状态在 submit/approve/approved/done 的付款申请占额，`settlement_remaining_reservable_amount` 计算后端剩余可占额，`settlement_actual_paid_amount_map` 只以 `payment.ledger` 为实际已付事实，`contract_actual_paid_amount_map` 只汇总已付款执行。现有结算兼容字段 `paid_amount/amount_paid` 实际承载占额而非台账实付；因此工作区必须显式标注“已占额”和“实际已付”，并由后端补充非存储只读事实字段，不能把兼容字段改名冒充实付。

币种由各记录 `currency_id` 返回，货币字段的 `currency_field` 仍是唯一格式化依据；状态标签来自 Odoo Selection 描述和 workflow contract 的 statusbar。操作按钮由付款申请专用可用操作契约与现有 intent 共同决定，成功后至少重读当前付款申请、关联结算摘要、付款执行和付款台账；失败时不修改本地状态。

四角色现行边界为：finance 可读合同、结算、付款申请和付款执行，并可在公司 A/B 间切换；project member 只可读 Project A，当前 record rule 不允许读取该固定合同及任何财务对象；PM 可读 Project A、合同和结算但无付款申请/执行 ACL；owner 可读合同，但 Project A 主表及结算/付款对象受现有规则或 ACL 拒绝。上述事实不构成本分支修改 ACL、record rule 或 fixture 授权的依据。特别地，J04 文案中的 finance 直接打开 Project A 主表与当前记录规则不一致；实现只能把 Project A 作为财务链内的安全上下文文本/不可点击关系，正式项目详情入口仍由有权的 PM 验证，除非后续权限分支明确授权。

J04–J06 先前只能证明列表和通用详情可打开，根因是通用 form canvas 将所有字段同权平铺：没有声明式 L1–L5 资金工作区、没有安全的正反向关系投影、没有区分占额与台账实付，也没有验收专用且可复位的合法状态转换记录。固定 `fe_execution_a` 是 fixture 直接写入 `paid` 状态，并未调用业务方法，所以固定链没有付款台账；它不能被当作操作闭环证据。FE-B04 必须使用同一 acceptance fixture 框架增加可复位的 `FE Journey` 记录，并只通过正式 intent 完成一次真实转换。

## FE-B04 合同—结算—付款工作区交付事实

最终实现以 `financial_workspace_contract` 为唯一声明式详情投影：后端按模型声明 L2 事实、L3 关系、L4 明细和 L5 审计信息，前端 `FinancialRelationshipWorkspace`、统一货币格式化和关系链接只消费契约，不在 `ContractFormPage` 中新增逐模型分支。legacy 与 Unified Page Contract V2 均携带同一 `businessWorkspace/businessActions`；付款操作仍由 `payment.request.available_actions` 和 `payment.request.execute` 决定，前端不直接 write 状态或计算金额。

关系投影先以当前用户执行 `_safe_record`、ACL 和 record rule 检查，再读取标签和生成正式 record route；不可读关系不返回标题或链接。公司/经营范围切换会清空 activity page 标题和 KeepAlive cache epoch，随后重新执行 `system.init`，因此公司 A 的详情标题不会残留到公司 B。finance 对 Project A 主表和合同正式 action 的既有权限限制保持不变：J04 的项目入口、合同、结算由 PM 的合法权限完成；finance 负责 J05、J06 和公司隔离。未修改 ACL、record rule、角色策略、导航分母或金额/状态机。

金额展示直接使用后端字段与 `operating_metrics`：合同原始/最终/累计实付，结算原始/扣款/调整后基数/占额/台账实付/剩余可占额，付款申请申请额/占额/台账金额，以及执行计划额/实付结果分别展示；0 与 null 使用不同显示语义，币种随每个事实返回，混合币种风险由后端契约标记且不换算。固定链明确显示付款申请占额 1000 CNY、台账实付 0 CNY和“暂无实付 / 台账结果”，没有把已付款执行反算成台账金额。

J04 PASS：PM 打开 Project A，沿真实关系进入 `CONOUT2600001` 和 `FE-A-SET-001`，验证 1130/1000 CNY、刷新后关系恢复并从结算反向返回合同。J05 PASS：finance 从结算进入 `FE-A-PR-001`、`FE-A-PE-001` 和显式空台账，逐级返回时编号、状态、币种和占额/实付口径一致。J06 PASS：专用 `FE-JOURNEY-PAYMENT-001` 从 draft 经确认对话框调用 `payment.request.execute` 转为 submit；详情权威重载后提交按钮消失，关联结算占额从 0 变为 100、剩余从 100 变为 0，台账实付仍为 0。相同 request ID、新 request ID 重放、无权限角色和非法状态均未产生第二次状态/金额/台账变更。

浏览器报告 `artifacts/frontend-financial-workspace/report.json` 记录 J04/J05/J06、公司 A→B→A、project member 无泄露拒绝和 1440×900、1280×800、390×844 三种尺寸全部 PASS；console error、pageerror 与非预期 HTTP 错误均为 0。窄屏下详情容器显式允许 grid item 收缩，宽明细表只在自身容器内滚动，页面根节点无横向滚动。对话框 Enter 提交、初始焦点和返回焦点均由公共确认组件处理，提交期间禁用并防止重复触发。

## FE-B05 我的工作、业务表单与审批实施前事实

现有入口为 `/my-work` 与 scene `my_work.workspace`，前端 `MyWorkView` 调用正式 intent `my.work.summary`。旧契约聚合 `mail.activity`、`tier.review`、历史 `sc.workflow.workitem`、项目任务/风险、负责项目、消息和关注记录，分区为“待我处理/我负责/@我的/我关注的”；它没有产品要求的“我发起的/最近完成”，也没有付款审批所需的金额、公司、往来方、发起人、状态和可用 action。更关键的是旧 handler 使用 `sudo` 搜索、计数和读取 record title，再尝试按项目范围裁剪，数量与最终列表不是同一权限结果，不能作为本分支的权威工作项边界。

付款申请已有完整正式 intent 链：`payment.request.available_actions` 组合当前 Odoo state、模型方法、业务前置条件和正式角色组；所有状态转换统一由 `payment.request.execute` 委托 submit/approve/reject/done handler，具备 request-id 幂等、审计和后端权限拒绝。审批交接的正式角色是 `smart_construction_custom.group_sc_role_executive`（管理层），验收账号 `demo_role_executive` 已存在；finance 角色负责 draft→submit 和 approved→done，executive 负责 submit→approved 或 submit→draft（reject，reason 必填）。PM、owner 和 project member 没有付款审批 action 证据，不纳入付款待办。

| 业务对象 | 当前状态 | 可执行操作 | 正式 capability / intent | 合法角色 | 权威待办语义 | 完成后去向 |
| --- | --- | --- | --- | --- | --- | --- |
| 合同 `construction.contract` | 由 workflow contract 返回 | 仅 contract 明确允许的模型方法 | `sc.workflow.contract.service` | 按现有 contract action | 本分支没有稳定的审批工作项证据 | 保持业务详情 |
| 结算 `sc.settlement.order` | draft/submit/approve/done 等既有状态 | 由 workflow contract 返回 | `sc.workflow.contract.service` | PM/finance 现有权限 | 没有可证明与角色一一对应的待办载体 | 保持业务详情 |
| 付款申请 `payment.request` | draft | submit | `payment.request.available_actions` → `payment.request.execute` | finance | 进入“我发起的”，不进入审批人的“待我处理” | submit 后交接 executive |
| 付款申请 `payment.request` | submit | approve/reject | 同上；正式角色组 `group_sc_role_executive` | executive | executive“待我处理” | approve/reject 后从待办移除并进入最近完成 |
| 付款申请 `payment.request` | approved | done | 同上 | finance | finance“待我处理” | done 后进入最近完成并产生既有台账副作用 |
| 付款执行 `sc.payment.execution` | 既有状态 | 模型 contract 明确操作 | 现有 workflow/model method | finance | 当前没有独立 My Work 权威投影 | 保持资金详情 |

表单字段的 label、required、readonly、selection、relation/domain、default、currency 和 help 均来自 action/page contract 的 field schema、native view modifier 与 onchange；保存走 `api.data` create/write，提交走付款专用 intent。后端错误通过统一 envelope 的 field errors、reason code、message 和 suggested action 返回。当前 J07 阻塞于 My Work 的不可信 `sudo` 聚合、非产品分区和工作项事实缺失；J08 阻塞于结算详情没有权威“新建付款申请”入口、表单缺少付款业务分组，以及旧浏览器 handoff smoke 可因 token/候选缺失标记 skipped，不能证明真实提交—审批—待办迁移。

本分支据此只建立付款申请的权威工作项投影：当前用户必须先通过 payment.request 的 ACL/record rule，随后每条记录再由 available-actions contract 判定是否进入待处理；“我发起的”按 `create_uid` 且仍在当前公司/项目范围读取；“最近完成”只展示当前用户发起或真实参与审批且已离开可操作状态的记录。不得用 `sudo`、中文状态文案或前端数组模拟转移。

## FE-B05 我的工作、业务表单与审批交付事实

最终 My Work 契约由 `payment_request_work_item_service` 在当前用户环境内聚合，不使用 `sudo`：先验证付款申请模型读取权限与 finance/executive 正式 capability，再按当前唯一 active company、record rule、`create_uid` 和 `payment.request.available_actions` 生成“待我处理/我发起的/最近完成”。数量与列表来自同一结果；project member、PM、owner 没有付款工作项 capability 时在读取敏感记录前返回空产品工作区。公司切换、角色切换、logout/login、保存和状态 intent 成功后均重新请求契约，不通过前端数组模拟迁移。最近完成只在现有审计载体可证明当前用户真实参与时返回；无法安全证明时隐藏该分区。

角色矩阵冻结为：finance 可创建、保存、编辑并提交付款申请，approved 状态下可执行既有 done 操作；正式 executive 角色 `group_sc_role_executive` 可审批或拒绝 submit 状态申请，拒绝理由必填；project member、PM、owner 均没有付款审批按钮和工作项。验收沿用已有 `demo_role_executive`，没有新增角色、ACL、record rule、金额公式或状态转换。Journey fixture 仅在 `sc_frontend_acceptance` 增加可复位起始记录，并由正式 intent 产生 submit、approve/reject 结果。

付款申请表单字段 schema 继续取自 action/page contract 和原生 view modifier；资金工作区只补充权威 entry defaults、关系显示名和 `project_scope_policy=exempt`。该策略只阻止全局项目上下文污染 finance 的公司级 create，不放宽后端访问：显式 company、settlement、contract、project 值仍由现有 ACL、record rule、domain、onchange 和 create 校验。提交返回 `type=refresh` 时前端保留当前业务详情并重新加载权威状态，不再误跟随 legacy compatibility action 进入无权 action。

J07 PASS：finance 公司 A 打开 My Work 时待处理 4、我发起的 5，数量与列表一致；进入付款申请、返回并提交草稿后工作项重新读取；A→B 时 A 项消失且 B 项出现，B→A 后 A 结果恢复。J08 PASS：finance 从专用结算入口创建 `PRQ2600028`，验证默认项目/合同/结算与必填校验，保存、刷新、重新编辑并提交；logout 后 `demo_role_executive` 登录，申请进入待处理，批准后移出待办；finance 再登录可见 approved 权威状态。缺少必填、拒绝缺少理由两条失败路径均保持状态、金额和工作项数量不变，合法拒绝才产生正式状态转换；重复提交由提交中禁用、request-id 幂等和后端非法状态共同阻止。

浏览器报告 `artifacts/frontend-my-work-approval/report.json` 记录 J07/J08、1440×900、1280×800、390×844、project member 隔离全部 PASS；console error、pageerror 和非预期 HTTP 错误为 0。390 宽度下卡片和表单为单列且页面无横向滚动；原生 dialog 打开后焦点进入，关闭后返回触发按钮，提交期间按钮禁用。FE-B02/B03/B04 回归分别保持 70/70 权威叶节点可达、action 876/menu 606 明确拒绝、页面身份守卫通过、J02–J06 PASS，四个已移除入口没有回升。

当前明确边界：产品 My Work 只投影具有完整权限和动作事实的付款申请；合同、结算、付款执行等对象尚无可证明的统一工作项载体，因此未以状态字符串推断加入。最近完成在审计参与证据不可读时隐藏，不以扩大审计模型权限换取展示。
