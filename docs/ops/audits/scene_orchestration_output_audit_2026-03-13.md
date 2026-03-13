# 场景编排输出专项审核（2026-03-13）

## 审核范围
- 目标：确认“场景编排层输出契约”是否达标，作为前端迭代前置门槛。
- 不包含：前端渲染实现细节。
- 结论口径：以仓库 `verify.*` 产物和守卫结果为准。

## 审核命令
- `make verify.page_orchestration.target_completion.guard`
- `make verify.page_contract.orchestration_schema.guard`
- `make verify.page_contract.action_schema_semantics.guard`
- `make verify.page_contract.data_source_semantics.guard`
- `make verify.orchestration.semantics_registry.guard`
- `make verify.workspace_home.orchestration_schema.guard`
- `make verify.workspace_home.sections_schema.guard`
- `make verify.workspace_home.provider_split.guard`
- `make verify.scene.schema`
- `make verify.scene.capability.matrix.schema.guard`
- `make verify.scene.contract.semantic.v2.guard`
- `make verify.scene.contract.shape`
- `make verify.runtime.surface.dashboard.report`
- `make verify.runtime.surface.dashboard.schema.guard`

## 审核结果摘要
- 结论：**未达标（Fail）**，暂不切前端迭代。
- 通过：11 项
- 失败：2 项（核心阻断）

## 通过项（关键）
1. `verify.page_contract.orchestration_schema.guard` ✅
2. `verify.page_contract.action_schema_semantics.guard` ✅
3. `verify.page_contract.data_source_semantics.guard` ✅
4. `verify.orchestration.semantics_registry.guard` ✅
5. `verify.workspace_home.sections_schema.guard` ✅
6. `verify.workspace_home.provider_split.guard` ✅
7. `verify.scene.schema` ✅
8. `verify.scene.capability.matrix.schema.guard` ✅
9. `verify.scene.contract.semantic.v2.guard` ✅
10. `verify.scene.contract.shape` ✅
11. `verify.runtime.surface.dashboard.schema.guard` ✅

## 失败项（阻断）
### A. `verify.page_orchestration.target_completion.guard` ❌
失败信息：
- `workspace_home_contract_builder.py missing token: "page_orchestration_v1": _build_page_orchestration_v1(role_code)`
- `workspace_home_contract_builder.py missing token: "page_orchestration": _build_page_orchestration(role_code)`
- `HomeView.vue missing token: return hasV1 && isDashboard && zones.length > 0;`

说明：
- 该守卫判定“编排主链闭合”未满足，属于结构性阻断。

### B. `verify.workspace_home.orchestration_schema.guard` ❌
失败信息：
- `pm/finance/owner: zones[3].blocks[0].payload unexpected keys for block_type=entry_grid: max_items`
- `zone priority order should vary across pm/finance/owner for heterogeneous same-page layout`

说明：
- `entry_grid` payload 与语义注册表不一致。
- 角色异构排序策略未满足守卫预期。

## 附加观察
- `verify.contract.evidence` 当前会被 `verify.baseline.freeze_guard` 阻断（冻结基线文件改动），与本次“编排输出达标”主问题不同，单列为发布治理风险。

## 达标门槛（切前端前必须全部满足）
1. `verify.page_orchestration.target_completion.guard` 通过。
2. `verify.workspace_home.orchestration_schema.guard` 通过。
3. 上述通过后，复跑：
   - `make verify.scene.schema`
   - `make verify.scene.contract.semantic.v2.guard`
   - `make verify.runtime.surface.dashboard.schema.guard`

## 下一步（后端整改）
1. 修正 `workspace_home_contract_builder` 输出键位与守卫对齐（`page_orchestration_v1`/legacy alias 期望）。
2. 清理 `entry_grid` 的未注册 payload 键 `max_items`，或在语义注册表正式登记并同步守卫。
3. 补齐 PM/Finance/Owner 的异构 zone priority 排序策略（避免同构顺序）。

