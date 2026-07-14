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

深度旅程审计后确认，项目成员账号原先仅携带项目读取/业务发起能力，但角色解析将 `group_sc_cap_project_read` 误归为 `pm`，前端最终回退显示为 owner；同一错误还使敏感财务、税务、人事和付款菜单进入权威导航。修复在角色解析、delivery menu projection 和 action 直达状态三层收口：项目成员角色代码为 `project_member`、显示名为“项目成员”，导航仅保留项目/合同等允许入口；未授权 action 不再渲染空列表，而进入统一无权限状态。记录规则和业务数据权限未放宽。
