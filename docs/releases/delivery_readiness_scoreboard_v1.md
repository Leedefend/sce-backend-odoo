# 交付就绪证据板 v1

## 1. 目标

本证据板用于给交付经理、实施团队和研发团队提供统一的“可交付状态”视图，覆盖：

- 9 个交付模块的就绪状态
- 前端质量门禁状态
- 关键系统级验证证据
- 已知限制与后续动作

---

## 2. 本轮快照

- 分支：`codex/delivery-sprint-seal-gaps`
- 关注范围：前端 ActionView 主链 + 交付文档封板
- 结论：`P0 前端静态红线已清零，可继续进入模块级 system-bound smoke`

### 2.1 门禁结果（本轮）

- `pnpm -C frontend lint`：通过（`0 errors`，仅 warnings）
- `pnpm -C frontend typecheck:strict`：通过
- `pnpm -C frontend build`：通过

### 2.2 审批 smoke N+2 迁移状态

- `live_no_allowed_actions`：已退场（N+2）
- `live_no_executable_actions`：唯一保留口径
- 审批聚合链（严格审计）：
  - `PAYMENT_APPROVAL_NEED_UPGRADE=0 PAYMENT_APPROVAL_FIELD_AUDIT_STRICT=1 make verify.portal.payment_request_approval_all_smoke.container` 通过
- 字段消费巡检：
  - `make verify.portal.payment_request_approval_field_consumer_audit` 通过（`unexpected_deprecated_refs=0`）

---

## 3. 九模块就绪矩阵（交付口径）

| 模块 | 代表场景 | 当前状态 | 证据 | 下一步 |
|---|---|---|---|---|
| 项目管理 | `projects.list` / `projects.intake` | `IN_PROGRESS` | 导航与 capability 已齐，本轮前端 gate 通过 | 补 PM 旅程 smoke |
| 项目执行 | `projects.execution` / `projects.detail` | `IN_PROGRESS` | 场景已注册、入口已存在 | 补执行中心场景数据验证 |
| 任务管理 | `task.center` | `IN_PROGRESS` | 场景入口已存在 | 补任务中心列表/筛选 smoke |
| 风险管理 | `risk.center` / `risk.monitor` | `IN_PROGRESS` | 场景入口已存在 | 补风险提醒闭环验证 |
| 成本管理 | `cost.project_boq` / `cost.project_budget` | `IN_PROGRESS` | ActionView 主链稳定性提升 | 补预算/台账真实数据验证 |
| 合同管理 | `contract.center` | `IN_PROGRESS` | 场景入口已存在 | 补合同中心动作链 smoke |
| 资金财务 | `finance.payment_requests` / `finance.center` | `IN_PROGRESS` | 付款申请与财务中心入口已在导航 | 补审批/台账流程验证 |
| 数据与字典 | `data.dictionary` | `READY_FOR_PILOT` | 入口清晰、依赖面较窄 | 补样本数据回归 |
| 配置中心 | `config.project_cost_code` | `READY_FOR_PILOT` | 管理入口已明确 | 补管理员角色验收 |

状态定义：

- `READY_FOR_PILOT`：可进入试点验收
- `IN_PROGRESS`：功能/入口已具备，但缺关键旅程证据
- `BLOCKED`：存在阻断交付的硬缺口

---

## 4. 本轮已关闭缺口

1. 前端 ActionView 关键文件 lint/type 红线（`any`、unused、regex 等）
2. 前端门禁三项验证可通过（lint/typecheck/build）
3. 交付冲刺文档（Blocker / 9模块矩阵 / Week1封板计划）已成套落库

---

## 5. 当前已知限制

1. 9 个模块仍需补 system-bound 旅程证据（按角色）
2. scene contract 字段级强校验尚未全部封口
3. 模块状态目前为交付治理口径，不替代业务签收结论

---

## 6. 下一轮执行建议（按优先级）

### P0（立即）

1. 输出 PM/财务/采购/老板四角色旅程 smoke 证据
2. 对 9 模块逐一给出“数据前置 + 验收步骤 + 结果”
3. 将 scene contract/provider shape 缺口挂为发布 blocker

### P1（紧随其后）

1. 建立可追溯的“最近一次通过环境”记录（DB/seed/bundle/commit）
2. 把证据板接入发布检查清单
