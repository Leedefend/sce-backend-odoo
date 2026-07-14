# 自定义前端成熟产品全量审计 v1

## 执行摘要

本审计基于 `origin/main@cd73cf72c`、固定验收数据库 `sc_frontend_acceptance`、独立验收前端和 Odoo runtime。审计只读，不执行创建、编辑、提交、审批、删除、导入、发布或付款操作。

已有真实证据确认：四个固定账号可登录；finance 公司 A/B 数据隔离；project member 仅可见项目 A；B/C 敏感业务记录访问被拒绝；付款列表基础旅程通过。

本轮新增全表面巡检脚本，但真实运行显示权威菜单中部分节点只有按钮/父节点信息，尚未形成可直接巡检的 route target。该事实本身是产品交付和导航契约的 P1 缺口，不能用源码清单替代页面通过证据。

## 覆盖统计

| 项目 | 结果 |
| --- | --- |
| 角色登录检查 | 4/4 |
| 全表面机器记录 | 8 条首轮记录 |
| 实际到达的动态列表页面 | 3 条 |
| 1440×900 | 固定付款/项目证据已有；全表面未完成 |
| 1280×800 | 核心页面已有部分证据；全表面未完成 |
| 390×844 | 既有代表性证据；全表面未完成 |
| J01–J08 | 已有局部证据，尚未全部逐步通过 |

## 架构事实

- `/a/:actionId` → `ActionViewShell` → `ActionView` → `ListPage`。
- `/r/:model/:id`、`/f/:model/:id` → `ContractFormPage`。
- 页面标题、字段 label、关系字段和权限状态应来自 contract/native descriptor/access policy。
- 通用渲染器不应根据业务模型复制页面。
- 普通用户不应看到 model、action、record id、contract、trace 等技术信息。

## 成熟度评分

| 维度 | 当前分数 | 依据 |
| --- | ---: | --- |
| 信息架构 | 2 | 权威导航存在，但部分节点无法形成稳定可巡检路径 |
| 视觉层级 | 3 | FE-P00/P01 已建立 token 与壳层基线，跨 surface 仍有漂移 |
| 一致性 | 2 | 列表、详情、表单 contract surface 尚未完成统一证据 |
| 信息密度 | 3 | 桌面列表可用，完整业务域未验证 |
| 文案 | 2 | 已发现 record 技术标题回退风险 |
| 状态反馈 | 3 | 加载/空/错/权限已有基础分支，统一度需审计 |
| 操作安全 | 3 | 权限隔离有证据，写操作全量审计未完成 |
| 导航 | 2 | 真实菜单按钮与 route target 映射存在缺口 |
| 响应式 | 2 | 桌面基础可用，窄屏仅有代表性证据 |
| 可访问性 | 1 | 尚无全量键盘、焦点、语义和对比度证据 |
| 性能感知 | 2 | 缺少同环境初始化、列表、详情、切换基线 |
| 专业可信度 | 2 | 已有产品化基础，但尚不足以宣称全量成熟 |

## P0/P1/P2/P3

- P0：0 个已确认。
- P1：3 个，见 `frontend_maturity_backlog_v1.csv` 的 FE-AUD-0001–0003。
- P2：3 个，见 FE-AUD-0004–0006。
- P3：待完整表面覆盖后再评估。

## 最严重问题

1. record 路由技术标题回退。
2. 权威菜单节点缺少稳定可巡检 route target。
3. 全表面巡检尚不能证明所有角色页面真实可达。
4. 结算/付款详情关系链缺少完整浏览器证据。
5. 全量可访问性没有证据。
6. 全量性能没有基线。

## 证据索引

- `artifacts/frontend-audit/full-surface-report.json`
- `artifacts/frontend-audit/full-surface-report.csv`
- `docs/frontend_productization/frontend_surface_inventory_v1.csv`
- `docs/frontend_productization/frontend_maturity_backlog_v1.csv`
- `docs/frontend_productization/frontend_delivery_readiness_v1.md`
- `scripts/verify/frontend_productization_fixture_browser.mjs`

## 审计边界

本任务未修改产品页面、样式、后端、API、权限、fixture、数据库或 runtime；后续修复分支必须由本审计 backlog 重新编排。
