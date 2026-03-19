# Delivery Readiness Scoreboard v1

## Snapshot

- generated_at_utc: 2026-03-19T15:22:03Z
- branch: `codex/delivery-sprint-seal-gaps`
- commit_ref: `2ffdf72`
- primary_gate: `make verify.scene.delivery.readiness.role_company_matrix`
- gate_result: `PASS`

## System-Bound Evidence Summary

| Evidence | Status | Source |
|---|---|---|
| Scene delivery readiness (strict) | PASS | `artifacts/backend/scene_product_delivery_readiness_report.json` |
| Role matrix source-mix (`executive/pm/finance/ops`) | PASS | `artifacts/backend/scene_base_contract_source_mix_role_matrix_report.json` |
| Company matrix source-mix (`primary/secondary`) | PASS | `artifacts/backend/scene_base_contract_source_mix_company_matrix_report.json` |
| No-action regression guard | PASS | `make verify.scene.no_action_scene.guard` |

## 9-Module Readiness Board

| Module | Entry Scenes | Key Roles | Data Prerequisites | Smoke/Gate Status | Known Limits |
|---|---|---|---|---|---|
| 项目立项与台账 | `projects.intake`, `projects.list`, `projects.ledger` | PM, 采购经理 | 项目类型、组织字典、用户 | Covered by strict scene gate (`PASS`) | 需补旅程级 trace 固化 |
| 项目执行与任务协同 | `projects.dashboard`, `projects.dashboard_showcase` | PM | 项目、任务、周报样例 | Covered by strict scene gate (`PASS`) | 需补任务动作 system-bound 脚本 |
| 采购与物资协同 | `cost.project_boq`, `projects.ledger` | 采购经理, PM | BOQ、供应商主数据 | Covered by strict scene gate (`PASS`) | 需补采购动作回放证据 |
| 付款申请与审批 | `finance.payment_requests`, `finance.center` | 财务, PM | 付款申请、审批角色 | Strict scene gate (`PASS`), payment approval smoke chain available | 需把审批 smoke 结果纳入统一看板 |
| 资金与结算台账 | `finance.payment_ledger`, `finance.treasury_ledger`, `finance.settlement_orders` | 财务 | 账户、结算基础数据 | Covered by strict scene gate (`PASS`) | 需补台账对账快照证据 |
| 成本预算与利润分析 | `cost.project_budget`, `cost.project_cost_ledger`, `cost.profit_compare` | PM, 财务 | 预算、成本流水、BOQ | Covered by strict scene gate (`PASS`) | 需补搜索/分页动作证据 |
| 经营指标与领导看板 | `portal.dashboard`, `finance.operating_metrics` | 领导/老板 | 指标快照数据 | Covered by strict scene gate (`PASS`) | 需补只读角色验收脚本 |
| 生命周期与治理审计 | `portal.lifecycle`, `portal.capability_matrix` | 管理员, 领导 | capability/scene baseline | Covered by strict scene gate (`PASS`) | 需补审计导出证据链 |
| 主数据与工作台 | `data.dictionary`, `default` | 全角色 | 用户角色、字典主数据 | Covered by strict scene gate (`PASS`) | `default` 场景需持续监控占位语义 |

## 4 Key Journey Status

| Journey | Doc | Latest System-Bound Status | Gap |
|---|---|---|---|
| PM | `docs/product/delivery/v1/user_journey_pm.md` | Partially Covered (scene strict gate pass) | 缺独立旅程脚本与最近一次 trace 快照 |
| Finance | `docs/product/delivery/v1/user_journey_finance.md` | Partially Covered (scene strict gate + payment smoke chain) | 缺统一 scoreboard 链接 |
| Purchase | `docs/product/delivery/v1/user_journey_purchase.md` | Partially Covered (scene strict gate pass) | 缺采购动作 system-bound smoke |
| Executive | `docs/product/delivery/v1/user_journey_exec.md` | Partially Covered (scene strict gate pass) | 缺只读角色稳定性快照 |

## Release Blocking Gaps (Current)

1. Frontend gate historical blocker has been rechecked green in current workspace, but needs continuous seal-mode enforcement per release run.
2. Scene contract field-level strict schema and provider-shape closure still tracked as blocker in backlog.
3. Journey-level evidence is not yet fully script-bound for all 4 key roles.
4. Company matrix currently observes one effective company id (`observed_company_ids=[1]`); true multi-company evidence still pending.

## Repro Command Set (Default)

```bash
pnpm -C frontend gate
make verify.scene.no_action_scene.guard
make verify.scene.delivery.readiness.role_company_matrix
make verify.delivery.journey.role_matrix.guard
```
