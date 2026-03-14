# 前端 `scene_contract_v1` 迁移阶段结论（Round 2：P0/P1/P2 同步）

## 本轮目标
- 在不改路由与协议主键的前提下，同步推进 `P0/P1/P2` 页面对 `scene_contract_v1` 的消费收敛。
- 将“页面内硬编码推断”继续下沉为“契约优先 + 兼容回退”。

## 本轮完成项

### P0（关键视图）
- `ActionView`：
  - 新增 `scene_contract_v1` 消费入口（`pageContract.contract.scene_contract_v1`）。
  - 支持从契约注入 `surface_kind`、`surface_intent`、`empty_reason`。
  - 删除 `construction.work.breakdown` 空态硬编码分支。
  - 删除 `project.project` 的批量动作前端特判，改为契约策略 `delete_mode` 驱动（默认 `archive`）。
- `RecordView`：
  - 删除基于 `model/title` 的项目页关键词特判。
  - 改为基于记录实际数据信号决定摘要区是否展示。

### P1（核心导航页）
- `SceneView`、`MenuView` 保持 `usePageContract` 统一入口。
- 通过 `pageContract.ts` 增强，自动获得 `scene_contract_v1` 驱动能力，无需页面内新增特判。

### P2（辅助页）
- `SceneHealthView`、`ScenePackagesView`、`UsageAnalyticsView`、`PlaceholderView`、`LoginView` 全部保持 `usePageContract` 统一消费。
- 通过 `pageContract.ts` 的收敛增强，统一获得 `scene_contract_v1` 兼容路径。

## 契约消费层收敛（核心）
- `frontend/apps/web/src/app/pageContract.ts` 现支持：
  - 优先识别 `scene_contract_v1`（`contract_version=v1`）。
  - 当 `page_orchestration_v1` 不可用时，从 `scene_contract_v1.zones` 生成 section 语义。
  - 从 `scene_contract_v1.actions` 自动构建 action schema 与 global actions 回退路径。
  - 保持原有 `page_orchestration_v1` 完整兼容。

## 新增/升级守卫
- `verify.frontend.scene_contract_v1.consumption.guard` 升级覆盖：
  - Round 1 四页（home/project.management/my_work/workbench）
  - `ActionView` / `RecordView`
  - `pageContract.ts` 主收敛逻辑
  - `P1/P2` 页面 `usePageContract` 一致性

## 边界与兼容性
- 不修改 scene key / page key / 主路由。
- 不修改权限基线与业务判定。
- 前端仅改“契约消费路径”，保持后端协议向后兼容。

## 下一步建议
- 在后端场景编排层补齐 `extensions.surface_intent / surface_kind / empty_reason` 的标准输出，逐步消除 ActionView 剩余关键词回退逻辑。
- 将 RecordView 的“摘要信号字段集”外置为 `scene_contract_v1.extensions.record_summary_signals`，彻底移除页面内字段集合常量。
