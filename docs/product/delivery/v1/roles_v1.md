# Roles V1

## Scope
- Delivery roles: 6 (<=6)
- Goal: provide implementation-ready role package for pilot delivery.

| Role | Responsibility | Default Home Scene | Visible Modules | Hidden Modules |
|---|---|---|---|---|
| 项目经理 (`pm`) | 立项与执行推进 | `projects.dashboard` | 项目立项与台账、项目执行与任务协同、采购与物资协同、付款申请与审批、成本预算与利润分析、主数据与工作台 | 资金与结算台账、经营指标与领导看板、生命周期与治理审计 |
| 财务经理 (`finance`) | 付款审批与资金结算 | `finance.center` | 付款申请与审批、资金与结算台账、成本预算与利润分析、主数据与工作台 | 项目执行与任务协同、采购与物资协同、经营指标与领导看板 |
| 采购经理 (`purchase_manager`) | 采购执行与物资协同 | `cost.project_boq` | 项目立项与台账、采购与物资协同、成本预算与利润分析、主数据与工作台 | 付款申请与审批、资金与结算台账、经营指标与领导看板、生命周期与治理审计 |
| 老板/领导 (`executive`) | 看板与经营风险洞察 | `portal.dashboard` | 经营指标与领导看板、生命周期与治理审计、主数据与工作台 | 采购与物资协同、付款申请与审批、资金与结算台账 |
| 系统管理员 (`admin`) | 系统治理与运维支持 | `portal.capability_matrix` | 全模块可见 | 无 |
| 运营专员 (`ops`) | 日常跟单与数据维护 | `projects.list` | 项目立项与台账、付款申请与审批、主数据与工作台 | 资金与结算台账、经营指标与领导看板、生命周期与治理审计 |

## Delivery Rule
- 交付环境只下发本表角色包。
- 每个角色必须有默认首页 scene，且可通过 `ui.contract` 正常渲染。

## Evidence
- 默认首页可打开性证据：`artifacts/product/role_home_openability_report.json`
- 审计视图：`docs/ops/audit/role_home_openability_report.md`
