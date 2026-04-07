# 基础设置阻塞问题清单 v1

## P0 阻塞（已收敛）

### 1. `verify.scene.legacy_auth.smoke` 运行时不可达语义

- 当前状态：**已完成门禁语义修复**。
- 修复结果：默认严格模式下，runtime unreachable（timeout/connection refused/network unreachable/retries exhausted）直接 FAIL；仅在显式设置 `SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK=true` 时允许本地调试 fallback。
- 影响变化：将“不可达误判 PASS”收敛为“不可达严格 FAIL”，门禁语义与原生业务事实层验收对齐。
- 后续建议：将该项转为“环境可达性运维项”，不再作为业务事实层语义阻塞。

### 1.1 `project.dashboard.enter` 全链路权限阻塞（已收敛）

- 历史现象：`product_project_flow_full_chain_execution_smoke` 在默认 admin 路径触发 `project.project.stage_id` 403，导致 stage gate 持续 FAIL。
- 收敛动作：`ITER-2026-04-07-1269` 将 full-chain 验证身份优先级对齐为真实角色路径（`ROLE_OWNER_*`），并在门禁链路同步。
- 当前状态：**已收敛，stage gate 恢复 PASS**。
- 后续建议：保持“真实角色优先”验证策略，不回退到 admin 默认路径作为业务闭环主证据。

## P1 阻塞

### 2. 角色-能力-ACL 复杂桥接导致冲突排查成本高（部分收敛）

- 现象：`sc_capability_groups.xml` + `sc_role_groups.xml` + `ir.model.access.csv` + `sc_record_rules.xml` 四层叠加。
- 影响：出现权限异常时难以在单点快速判责。
- 根因归类：治理结构复杂，桥接层过深。
- 当前进展：已在 `ITER-2026-04-06-1189` 完成 `project.budget` ACL 重复项去重与最小规则补齐。
- 剩余建议：继续按模型最小闭环推进，避免扩大到非必要权限面。

### 3. 核心模块 data 条目过多（84）

- 现象：`smart_construction_core` manifest 同时装载大量数据、安全、动作、视图。
- 影响：一次升级回归面过宽，阻塞问题定位慢。
- 根因归类：行业核心模块装载面偏重。
- 当前进展：`ITER-2026-04-06-1190` 执行 `make verify.test_seed_dependency.guard` PASS，测试依赖面未发现外部 seed/demo 越界。
- 建议：继续维持“问题点就地最小修复”与短链门禁策略，不做跨模块拆分。

## P2 风险

### 4. 主数据 seed 依赖人工初始化（高风险闸门）

- 现象：公司/部门/用户/岗位以原生维护为主，缺少完整 install-time 业务主数据种子。
- 影响：新环境首轮联调可能因空主数据导致流程断点。
- 当前进展：`ITER-2026-04-06-1192` 已完成最小 install-time 字典种子物化（`project.dictionary` 基线），并通过 `verify.test_seed_dependency.guard`。
- 建议：后续仅按“最小新增字典/主数据骨架”扩展，不引入交易类种子与依赖重排。

### 5. 历史路径痕迹与文档漂移风险

- 现象：已出现旧路径遗留（本轮已完成文档补标修复）。
- 影响：后续审计和交接出现误导。
- 建议：继续把迁移标记作为门禁长期保留。

## 小结

- 当前“原生业务事实层”P0 阻塞已全部收敛，stage gate 处于 PASS。
- 后续主线聚焦 P1/P2 治理项（权限复杂度与主数据持续补齐），保持最小改动策略。
