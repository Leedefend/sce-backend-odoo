# SCEMS 工作台架构级校准（冻结稿 v1 · 2026-03-12）

## 1. 为什么现在校准

工作台已经从“样式迭代”进入“语义协议治理”阶段，当前主要矛盾不再是 UI 好不好看，而是：

- 首页叙事是否始终围绕“行动优先”；
- 协议主次是否稳定（v1 主协议、legacy 兼容）；
- 业务数据与平台诊断是否彻底分层。

结论：下一阶段必须以“语义稳定”替代“视觉微调”。

---

## 2. 工作台定位（统一口径）

工作台唯一定位：

> **业务行动中枢（Action Hub）**

工作台必须回答三问：

1. 今天先处理什么（Action）
2. 哪些风险影响目标（Alert）
3. 当前经营状态是否偏离（Status）

---

## 3. 工作台禁止项（硬约束）

工作台不得：

1. 直接展示 capability registry 原始计数作为主业务指标；
2. 直接展示 diagnostics/debug/raw meta 字段到用户主视图；
3. 直接展示 `scene_key/section_key/source_kind` 等协议字段；
4. 以“功能分组概览”替代首屏行动叙事；
5. 让 `quick_entries` 抢占 `today_focus` 首屏优先级；
6. 让 legacy 协议承载新增页面语义；
7. 通过前端临时排序覆盖后端 contract 排序。

---

## 4. 目标页面模型（四区冻结）

首页主骨架固定四区：

1. `today_focus`（主区）
   - `today_actions`
   - `risk_alert_panel`
2. `analysis`
   - 业务运营指标 + 进展摘要
3. `quick_entries`
   - 常用功能入口（次优先）
4. `hero`
   - 角色与入口摘要（补充区）

严格禁止新增第五主区临时塞信息。

---

## 5. 协议与兼容策略

### 5.1 主协议

- `page_orchestration_v1` 是唯一主协议。

### 5.2 兼容协议

- `page_orchestration` 仅作 legacy 兼容。
- 新增语义不得写入 legacy 专用字段。

### 5.3 Contract 自描述（必须）

- `contract_protocol.primary=page_orchestration_v1`
- `contract_protocol.legacy.status=compatibility`

---

## 6. 数据优先级策略

### 6.1 行动与风险：业务优先、能力兜底

- `today_actions`：业务动作优先（任务/审批/风险/付款）；
- `risk.actions`：真实风险动作优先；
- 业务不足时才使用 capability fallback。

### 6.2 指标命名与来源分层表

| 字段 | 类型 | 数据来源 | 首屏用户展示 | 说明 |
| --- | --- | --- | --- | --- |
| `today_actions` | action list | business / fallback | 是 | 首屏主叙事 |
| `risk.actions` | alert list | business / fallback | 是 | 首屏主叙事 |
| `metrics.*` | business metric | business only | 是 | 不得用 capability 拟态业务 |
| `platform_metrics.*` | platform metric | capability registry | 否 | 仅运维/HUD 参考 |
| `diagnostics.extraction_stats` | diagnostic | extraction pipeline | 否 | 仅诊断 |
| `diagnostics.action_ranking_policy` | diagnostic | ranking engine | 否 | 仅诊断 |

### 6.3 fallback 语义规范

当业务数据缺失触发 fallback 时：

1. 用户主视图不得展示伪经营百分比；
2. 首屏允许弱提示“暂无业务数据，当前展示系统就绪入口”；
3. `diagnostics` 必须记录 `source_kind/fallback_reason/extraction_hit_rate`；
4. fallback 信息不得伪装为真实业务成果。

---

## 7. 行动排序策略（Action Ranking v1）

`today_actions` 排序采用可解释多因子：

1. 风险严重度（critical/urgent/overdue/严重/紧急/逾期）
2. 时效（逾期 > 24h 内 > 3 天内 > 7 天内）
3. 待处理量（`count/pending_count`）
4. 来源优先（business > capability fallback）

排序策略必须通过：

- `diagnostics.action_ranking_policy`
- `diagnostics.extraction_stats`

对外可观测、对内可回放。

---

## 8. 角色模板策略（冻结版）

### PM（项目经理）

- `today_actions` 最高
- `risk_alert_panel` 次高
- `analysis` 第三
- `quick_entries` 第四

### Finance（财务）

- `today_actions` 与 `analysis` 并重
- 风险优先显示付款/结算相关
- `quick_entries` 中资金/合同相关靠前

### Owner（管理层）

- `risk_alert_panel` 与 `analysis` 权重最高
- `today_actions` 精简
- `quick_entries` 弱化为次要入口

---

## 9. 前后端职责边界

### 后端（contract 责任）

- 页面语义与编排；
- 数据来源优先级与降级；
- 指标分层与诊断输出；
- 行动排序与策略声明。

### 前端（renderer 责任）

- 严格按 contract 渲染；
- 执行交互与跳转；
- 不私自重写后端排序优先级。

---

## 10. 可发布验收标准

### 10 秒标准

- 首屏先看到“今日行动 + 系统提醒”；
- 用户无需解释即可知道先做什么。

### 30 秒标准

- 至少一条行动可一跳处理；
- 风险与状态关系可被快速理解；
- 用户主视图无技术字段污染。

### 协议标准

- `page_orchestration_v1` 主协议稳定可用；
- legacy 仅兼容，不承载新需求。

---

## 11. 下一阶段动作

1. 冻结 `action_ranking_policy_v1` 文档并建立快照基线；
2. 角色模板参数化（PM/Finance/Owner）并进入可配置策略；
3. 形成“业务抽取命中率”周报（按角色/租户/环境）；
4. HUD/diagnostics 输出标准化，阻断调试字段回流；
5. 把工作台 contract 快照纳入发布前最小回归。

---

## 12. 一句话结论

> 工作台的下一阶段目标不是“再做一版更漂亮的首页”，而是把“行动优先、风险优先、业务优先”固化为可验证、可演进、可治理的平台级语义协议。

