# SCEMS v1.0 Phase 1：主导航与 Scene 映射清单

## 1. 映射目标
将 V1 主导航固定到 `construction_pm_v1` 的标准场景代码集合，作为发布口径基线。

## 2. 目标映射（V1）

| 主导航 | 目标 Scene Code | 当前状态 | 备注 |
|---|---|---|---|
| 我的工作 | `my_work.workspace` | 已存在 | 可作为稳定入口 |
| 项目台账 | `projects.ledger` | 已存在 | 与项目控制台联动 |
| 项目管理 | `project.management` | 已存在 | 核心控制台场景 |
| 合同管理 | `contracts.workspace` | 已落地（最小可用） | 保留 `contract.center` 过渡深链 |
| 成本控制 | `cost.analysis` | 已落地（最小可用） | 保留 `cost.*` 过渡深链 |
| 资金管理 | `finance.workspace` | 已落地（最小可用） | 保留 `finance.center` 过渡深链 |
| 风险提醒 | `risk.center` | 已落地（最小可用） | 保留 `risk.monitor` 过渡深链 |

## 3. 当前策略落地
- 已将 `docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json` 的 `construction_pm_v1.nav_allowlist` 固化为上述 7 项。
- `config.*` 与 `data.*` 已从 deep-link allowlist 中移除，符合“非核心域不进入主投放面”的策略。

## 4. 后续动作（衔接 Phase 2）
- 优先补齐 `contracts.workspace` / `cost.analysis` / `finance.workspace` / `risk.center` 的场景定义与契约。
- 在补齐前，保留过渡深链能力，避免关键业务入口中断。
