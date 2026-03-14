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
- `scripts/verify/scene_data_source_schema_guard.py`
- `docs/ops/audit/scene_r3_runtime_dashboard.md`

## Progress

- ✅ Round1 已落地：
  - `scripts/verify/scene_role_policy_consistency_guard.py`
  - `scripts/verify/scene_data_source_schema_guard.py`
  - `Makefile` 新增对应 `verify` 入口
- ✅ Round2 已落地：
  - `scripts/verify/scene_r3_runtime_guard.py`
  - `docs/ops/audit/scene_r3_runtime_dashboard.md`
  - `Makefile` 新增 `verify.scene.r3.runtime.guard`
