# Wave2 Backlog · Scene Productization

## Goal

- 从 "配置级 R3" 进入 "运行态 R3"：
  - 角色差异有真实数据支撑
  - 动作链路有闭环监控
  - 模板复用有质量基线

## Backlog

1. **R3 Runtime Criteria**
   - 定义 R3 运行态验收字段（使用率、动作成功率、异常回流率）
   - 新增 `scene_r3_runtime_guard`（按场景输出通过/失败）

2. **Role Policy Hardening**
   - 将 `role_variants` 与 `role_surface_overrides` 做一致性校验
   - 补充角色策略冲突检测与报告

3. **Data Source Contracting**
   - 为 `data_sources` 建立 schema 守护（provider 存在性、source_type 合法性）
   - 增加 provider 健康检查和降级路径

4. **Action Chain Observability**
   - 为 `action_specs` 增加 intent->route 可打开性批量校验
   - 输出场景级动作链路报告（成功/失败/回退）

5. **Legacy Exemption Burn-down**
   - 清理 `scene_inventory_freeze_guard_exemptions` 中遗留项
   - 目标：exemption 从 `1` 降到 `0`

6. **Inventory Automation**
   - 自动从场景 payload 生成 inventory 草案（减少人工维护误差）
   - 变更时自动生成 diff 报告（scene_key、maturity、owner、next_action）

## Suggested Deliverables

- `scripts/verify/scene_r3_runtime_guard.py`
- `scripts/verify/scene_role_policy_consistency_guard.py`
- `scripts/verify/scene_role_surface_consistency_guard.py`
- `scripts/verify/scene_data_source_schema_guard.py`
- `docs/ops/audit/scene_r3_runtime_dashboard.md`
- `docs/ops/audit/scene_role_surface_consistency_report.md`

## Progress

- ✅ Round1 已落地：
  - `scripts/verify/scene_role_policy_consistency_guard.py`
  - `scripts/verify/scene_data_source_schema_guard.py`
  - `Makefile` 新增对应 `verify` 入口
- ✅ Round2 已落地：
  - `scripts/verify/scene_r3_runtime_guard.py`
  - `docs/ops/audit/scene_r3_runtime_dashboard.md`
  - `Makefile` 新增 `verify.scene.r3.runtime.guard`
- ✅ Round3 已落地：
  - `scene_r3_runtime_guard` 增加动作链观测列：`action_chain_status/resolution/route`
  - 动作链汇总指标：`success/fallback/fail`
  - 支持主动作 route 解析回退链路（direct / scene_ref / related / self_target）
- ✅ Round4 已落地：
  - 新增 `scene_role_surface_consistency_guard`，校验 `role_surface_overrides` 与 R3 `role_variants` 一致性
  - 新增冲突检测：角色合法性、allow/blocklist 冲突、R3 场景未知角色
  - 输出 `scene_role_surface_consistency_report` 供后续收敛告警项
- ✅ Round5 已落地：
  - `risk.center` 纳入 inventory（`R2`），移除 freeze guard legacy exemption
  - `scene_inventory_freeze_guard_exemptions` 从 `1` 收敛至 `0`
  - 完成 Legacy Exemption Burn-down 阶段目标
- ✅ Round6 已落地：
  - 新增 `scene_inventory_draft_diff_report`：自动从 scene payload 生成 inventory 草案
  - 输出草案对比报告（含 `scene_key/maturity_level/owner_module/next_action` 重点差异）
  - `Makefile` 新增 `verify.scene.inventory.draft.diff.report` 入口
- ✅ Round7 已落地：
  - 将 8 个候选场景批量回填进正式 inventory（按 `R0/R1` 过渡分级）
  - inventory 与 payload 草案实现 `added/removed = 0` 对齐
  - role surface 一致性告警从 `3` 收敛至 `1`
- ✅ Round8 已落地：
  - 新增 `scene_r1_r2_upgrade_queue_report`，自动产出 `R0/R1 -> R1/R2` 升级队列
  - 队列按 `priority + template + prerequisite` 编排，支持主线优先执行
  - `Makefile` 新增 `verify.scene.r1_r2.upgrade.queue.report` 入口
- ✅ Round9 已落地：
  - 首个 `P0` 场景 `portal.dashboard` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - 升级队列自动收敛并反映剩余待升级场景
- ✅ Round10 已落地：
  - 第二个 `P0` 场景 `portal.lifecycle` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - 升级队列继续收敛，保留未升级场景用于下一轮
- ✅ Round11 已落地：
  - 第三个 `P0` 场景 `projects.dashboard` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - 升级队列继续收敛，明确剩余 `R0/R1` 待升级集合
- ✅ Round12 已落地：
  - 第四个 `P0` 场景 `my_work.workspace` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - 升级队列继续收敛，保留剩余场景进入下一轮
- ✅ Round13 已落地：
  - 第五个 `P0` 场景 `portal.capability_matrix` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - 升级队列继续收敛
- ✅ Round14 已落地：
  - `data.dictionary` 与 `projects.dashboard_showcase` 补齐 `target.route`，并从 `R0 -> R1`
  - inventory 与 payload 路由事实对齐，消除 `TARGET_MISSING`
  - 升级队列仅保留可产品化业务候选
- ✅ Round15 已落地：
  - 升级队列脚本剔除 `scene_smoke_default`（测试场景不进入业务产品化队列）
  - 队列语义与执行规则保持一致
- ✅ Round16 已落地：
  - `projects.dashboard_showcase` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
- ✅ Round17 已落地：
  - `data.dictionary` 完成 `R1 -> R2` 模板化升级（补齐 `page/zone_blocks/related_scenes`）
  - inventory 对应场景升级到 `R2`
  - `R1-R2` 升级队列清空
- ✅ Round18 已落地：
  - 新增 `scene_r2_r3_upgrade_queue_report`，自动生成 `R2 -> R3` 升级队列
  - `Makefile` 新增 `verify.scene.r2_r3.upgrade.queue.report` 入口
- ✅ Round19 已落地：
  - `portal.dashboard` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round20 已落地：
  - `portal.lifecycle` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round21 已落地：
  - `my_work.workspace` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round22 已落地：
  - `portal.capability_matrix` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round23 已落地：
  - `projects.dashboard` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
  - `R2-R3` 队列进入收敛阶段
- ✅ Round24 已落地：
  - `projects.dashboard_showcase` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round25 已落地：
  - `data.dictionary` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
- ✅ Round26 已落地：
  - `risk.center` 完成 `R2 -> R3` 升级（补齐 `action_specs/role_variants/data_sources/product_policy`）
  - inventory 对应场景升级到 `R3`
  - `R2-R3` 升级队列清空
- ✅ Round27 已落地：
  - `scene_r3_runtime_guard` 增加运行态门槛机制：`pass_rate`、`action_chain_success_rate`、`action_chain_fallback_rate`
  - 增加失败分级：`BLOCKER`（强失败）与 `WARNING`（可持续治理）
  - 支持 `--fail-on-warning`，可在严格模式将告警提升为失败
- ✅ Round28 已落地：
  - `Makefile` 新增 `verify.scene.r3.runtime.strict` 目标（启用 `--fail-on-warning`）
  - 新增 `gate.scene.r3.runtime.strict` 门禁目标，作为 CI 严格入口
- ✅ Round29 已落地：
  - `gate.full` 默认接入 `gate.scene.r3.runtime.strict`
  - `codex.run FLOW=gate` 通过 `gate.full` 自动覆盖 R3 运行态严格门禁
- ✅ Round30 已落地：
  - 新增 `verify.scene.r3.runtime.quick` 一键目标（严格校验 + 报表摘要输出）
  - 用于快速确认本轮门禁效果，无需手动翻全量日志
- ✅ Round31 已落地：
  - 前端自定义视图重构 Batch1：抽离 `scene_contract_v1 -> page_orchestration_v1` 公共转换器
  - `MyWorkView`、`WorkbenchView` 去重复实现，统一走 `app/sceneContractV1.ts`
  - 降低场景契约适配逻辑漂移风险，为后续批次重构打基础
