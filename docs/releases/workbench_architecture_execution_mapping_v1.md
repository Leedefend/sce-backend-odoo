# 工作台架构基线执行映射（v1）

## 1. 目的

将 `workbench_architecture_calibration_v1` 的规则，映射到当前代码与验证命令，形成可直接迭代的执行面。

---

## 2. 规则 → 代码映射

### R1：`page_orchestration_v1` 为主协议

- 规则：主协议必须是 `page_orchestration_v1`，legacy 仅兼容。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 字段：`contract_protocol.primary` / `contract_protocol.legacy`
- 验证：
  - 打开 contract 响应，确认 `contract_protocol.primary=page_orchestration_v1`

### R2：首屏四区冻结（hero/today_focus/analysis/quick_entries）

- 规则：不得新增第五主区。
- 代码：
  - `addons/smart_core/core/workspace_home_data_provider.py`
  - 函数：`build_v1_zones`
- 验证：
  - 浏览器控制台打印 `workspaceHome.page_orchestration_v1.zones`
  - 区块只含四个主 zone key

### R3：`today_actions` 业务优先，capability fallback 次之

- 规则：业务动作优先抽取，数据不足再兜底。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 函数：`_build_business_today_actions` / `_build_capability_today_actions` / `_build_today_actions`
- 验证：
  - `diagnostics.extraction_stats.today_actions_business > 0` 时优先使用业务项

### R4：`risk.actions` 业务优先，capability fallback 次之

- 规则：风险动作优先使用业务风险数据。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 函数：`_build_risk_actions`
- 验证：
  - `diagnostics.extraction_stats.risk_actions_business`

### R5：指标分层（业务 vs 平台）

- 规则：`metrics` 不得混入平台计数；平台计数进入 `platform_metrics`。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 函数：`_build_metric_sets`
- 验证：
  - contract 同时存在 `metrics` 与 `platform_metrics`

### R6：调试字段分层

- 规则：用户主视图不展示调试字段，调试信息归 `diagnostics`。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 字段：`diagnostics.*`
- 验证：
  - 主页面无 `result_summary/active_filters` 等技术词

### R7：行动排序策略可解释

- 规则：按严重度 + 时效 + 待处理量 + 来源优先排序。
- 代码：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - 函数：`_urgency_score`
  - 字段：`diagnostics.action_ranking_policy`
- 验证：
  - 同类动作中“逾期/紧急”项排序前置

### R8：前后端职责边界

- 规则：后端定语义与排序，前端不重排业务优先级。
- 代码：
  - 后端：`workspace_home_contract_builder.py`
  - 前端：`frontend/apps/web/src/components/page/PageRenderer.vue`（仅按 priority 渲染）
- 验证：
  - 前端无按业务含义二次重排逻辑

---

## 3. 验证命令映射

- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.project.dashboard.contract`
- `make verify.phase_next.evidence.bundle`

建议执行环境：

- `ENV=test`
- `ENV_FILE=.env.prod.sim`
- `COMPOSE_FILES='-f docker-compose.yml -f docker-compose.prod-sim.yml'`

---

## 4. 直接迭代优化 Backlog（下一批）

### P0（立即执行）

1. 角色化排序参数模板（PM/Finance/Owner）代码化。
2. `today_actions` 增加“金额影响/项目影响”权重。
3. HUD 增加 `diagnostics.extraction_stats` 可视化开关。

### P1（随后）

1. 输出命中率周报（按角色/租户/环境）。
2. 固化 `action_ranking_policy_v1` 到独立文档并纳入回归。

---

## 5. 本轮执行结论

当前已具备“直接迭代优化”条件：

- 架构基线已冻结；
- 规则与代码位置已映射；
- 验证命令链路明确；
- 下一批可直接按 P0 开工。

