# SCEMS v1.0 Phase 1：导航收口报告

## 1. 执行结论
- 状态：`DOING`
- 已完成：主导航目标清单锁定、策略文件更新、导航-Scene 映射清单输出。
- 待完成：4 个目标 workspace 场景补齐（`contracts.workspace`/`cost.analysis`/`finance.workspace`/`risk.center`）。

## 2. 已落地变更
- 主策略文件：`docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json`
  - `construction_pm_v1.nav_allowlist` 固化为 V1 目标 7 项。
  - 从 deep-link allowlist 移除 `config.*` / `data.*` 相关条目。
- 映射清单：`docs/releases/phase_1_navigation_scene_mapping.md`

## 3. 运行验证（本轮）
- 执行命令：
  - `make verify.scene.catalog.governance.guard`
  - `make verify.project.form.contract.surface.guard`
  - `make verify.runtime.surface.dashboard.strict.guard`
- 预期：验证通过，确保策略与运行态在当前基线上可共存。

## 4. 风险与控制
- 风险：目标 7 项中的 4 个 workspace 场景尚未全部落地。
- 控制：保留 `contract.center` / `finance.center` / `risk.monitor` / `cost.*` 深链过渡能力。

## 5. 下一步
- 进入 Phase 2 的首批任务：
  - 实现 4 个 workspace 场景定义
  - 建立 `project.management` 7-block 契约专项 verify

