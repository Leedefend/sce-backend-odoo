# 原生基础设置验收矩阵 v1

## 范围与方法

- 范围：`smart_core`、`smart_enterprise_base`、`smart_construction_core`、`smart_construction_scene` 原生模块。
- 目标：仅审计 Odoo 原生业务事实层，不涉及自定义前端、scene 编排优化、平台抽象新增。
- 方法：静态清单审计（manifest/security/views/actions/models/hooks）+ 现有 verify 结果回放。

## 验收矩阵

| 验收项 | 证据 | 结果 | 说明 |
|---|---|---|---|
| 模块依赖链成立 | `addons/smart_construction_core/__manifest__.py` 依赖 `smart_core`、`smart_enterprise_base` | PASS | 基础模块依赖方向正确（核心→企业基座→行业）。 |
| 基础数据加载链成立 | `smart_construction_core` manifest `data` 含 `sequence.xml`、阶段/规则 seed | PASS | 数据项存在且位于安全前后链路可解释位置。 |
| 安全文件加载链成立 | `smart_core`/`smart_enterprise_base`/`smart_construction_core` 均加载 `ir.model.access.csv` | PASS | ACL 文件均进入 manifest `data`。 |
| 菜单入口加载链成立 | `views/menu_root.xml`、`views/menu.xml`、`views/menu_enterprise_base.xml` 在 manifest 内 | PASS | 原生菜单有明确装载来源。 |
| 视图加载链成立 | `smart_construction_core` manifest 含 53 个 `views/*` 条目 | PASS | 关键业务页（项目/付款/结算/预算/成本）均在链上。 |
| 审批动作加载链成立 | `data/material_plan_tier_actions.xml`、`data/payment_request_tier_actions.xml` 已加载 | PASS | Tier server actions 在 manifest 中声明。 |
| 原生菜单→action 绑定完整性 | 静态检查：`smart_construction_core` 菜单 action 引用缺失数 `0` | PASS | 未发现本模块菜单 action 悬挂引用。 |
| 企业基座主数据入口 | `smart_enterprise_base/views/menu_enterprise_base.xml` 提供公司/组织/用户动作 | PASS | 原生主数据入口清晰。 |
| 角色-能力组链路 | `security/sc_capability_groups.xml` + `security/sc_role_groups.xml` | PASS_WITH_RISK | 结构存在，但角色桥接复杂，需 Batch B 冲突清理。 |
| ACL 覆盖关键模型 | `ir.model.access.csv`：`payment.request/payment.ledger/sc.settlement.order` 等存在 | PASS_WITH_RISK | 覆盖存在，但细粒度冲突风险见阻塞清单。 |
| 记录规则覆盖关键财务对象 | `sc_record_rules.xml` 对 `payment.request/payment.ledger/sc.settlement.order` 各 3 条 | PASS | 财务对象已具备规则域约束。 |
| 主链 verify 可持续性 | `ci.preflight.contract` 当前阻断在 `verify.scene.legacy_auth.smoke` 超时 | BLOCKED | 运行时可达性问题阻断整体验收门。 |

## 结论（Batch A）

- 原生业务事实层“结构上成立”，但尚未达到“可交付闭环”状态。
- 当前第一阻断不是字段/菜单缺失，而是 **smoke 运行时超时**（`legacy_auth_smoke`）。
- 可进入 Batch B，优先清理阻塞项与权限冲突，再进入 Batch C 闭环验证。

