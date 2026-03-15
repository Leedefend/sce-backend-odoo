# 意图返回接入场景治理层迭代计划（v1）

日期：2026-03-15  
分支：`feat/scene-productization-wave1`

## 目标定位

将 `system.init / app.init` 的意图返回，从“仅返回场景/导航事实”升级为“返回可审计的场景治理事实”，并确保前端可消费、可回退、可验证。

## 架构定位

- Layer Target：`Platform Layer + Scene Layer + Frontend Layer`
- Module：`addons/smart_core/handlers/system_init.py`、`addons/smart_core/core/*scene*builder.py`、`frontend/apps/web/src/stores/session.ts`、`frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- Reason：在不破坏既有链路的前提下，分阶段完成治理能力显性化与运行链路产品化。

## 执行纪律

1. 每完成一个任务，必须同步更新本文件中的“状态/证据”。
2. 每次更新必须记录：影响文件、验证命令、结果。
3. 未更新文档的任务视为未完成。

## 任务清单（持续更新）

| ID | 任务 | Layer Target | 状态 | 证据 |
|---|---|---|---|---|
| T1 | 修复前端类型检查基线（`.vue` 声明 + 类型断言） | Frontend | ✅ DONE | `frontend/apps/web/src/env.d.ts`、`frontend/apps/web/src/app/navigationRegistry.ts`；`pnpm -C frontend/apps/web exec tsc --noEmit` 通过 |
| T2 | 后端输出 `scene_ready_contract_v1`（双轨） | Platform + Scene | ✅ DONE | `addons/smart_core/core/scene_ready_contract_builder.py`、`addons/smart_core/handlers/system_init.py` |
| T3 | 前端消费 `scene_ready_contract_v1`（registry 优先） | Frontend | ✅ DONE | `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`、`frontend/apps/web/src/stores/session.ts`、`frontend/apps/web/src/views/SceneView.vue` |
| T4 | 后端输出 `scene_governance_v1`（治理汇总） | Platform + Scene | ✅ DONE | `addons/smart_core/core/scene_governance_payload_builder.py`、`addons/smart_core/handlers/system_init.py` |
| T5 | 前端接收并持久化 `scene_governance_v1` | Frontend | ✅ DONE | `frontend/apps/web/src/stores/session.ts` |
| T6 | 场景治理可视化（SceneHealth/调试面板） | Frontend | ✅ DONE | `frontend/apps/web/src/views/SceneHealthView.vue`：新增 governance runtime 区块展示 `scene_governance_v1.gates/reasons` |
| T7 | 新增治理 guard（验证 `scene_governance_v1` 结构与关键 gates） | Governance/Verify | ✅ DONE | `scripts/verify/scene_governance_payload_guard.py` |
| T8 | 将 guard 接入 Makefile 验证入口 | Governance/Verify | ✅ DONE | `Makefile`：`verify.scene.governance_payload.guard`，并纳入 `verify.scene.runtime_boundary.gate` 依赖 |

## 本轮已执行验证

- `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/core/scene_governance_payload_builder.py addons/smart_core/handlers/system_init.py`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`（T6 完成后复验）：通过
- `python3 scripts/verify/scene_governance_payload_guard.py`：通过
- `make verify.scene.governance_payload.guard`：通过
- `pnpm -C frontend/apps/web exec tsc --noEmit --pretty false`（AppShell HUD 治理信息扩展后复验）：通过

## 增量更新记录

- 2026-03-15：`AppShell` HUD 已加入 `scene_governance_v1` 可视化字段（`scene_channel/runtime_source/gates/reasons`），便于调试与运维核查。
- 2026-03-15：已新增治理 payload 示例快照基线：`docs/ops/assessment/scene_governance_payload_snapshot_v1_2026-03-15.json`。

## 下一步（按顺序）

1. 结合后续版本演进，按需更新治理 payload 快照版本号与字段说明（可选）。
