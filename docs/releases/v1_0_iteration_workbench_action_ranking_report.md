# v1.0 工作台行动排序与命中率报告（本轮）

## 1. 本轮目标

在不改变权限、治理、交付主机制前提下，为 `today_actions` 与 `risk.actions` 增加可解释的业务优先排序能力：

- 业务动作优先于能力兜底；
- 逾期/临期动作优先；
- 高风险语义优先；
- 待处理数量作为辅助权重。

## 2. 实现摘要

核心实现位于：

- `addons/smart_core/core/workspace_home_contract_builder.py`

新增能力：

- `_urgency_score(...)`：统一计算行动紧急度；
- `_build_today_actions(...)`：按 `urgency_score` + 业务来源优先排序；
- `_build_risk_actions(...)`：风险动作按紧急度排序并提升 `urgent/danger` 语义；
- `diagnostics.extraction_stats`：输出业务命中与 fallback 统计。

## 3. 排序规则（当前版本）

动作分值由以下因子叠加：

1. 风险严重度关键词（critical/urgent/overdue/严重/紧急/逾期）
2. 时效（`due_date/deadline/planned_date/date_deadline`）
   - 已逾期 > 24h 内到期 > 3 天内到期 > 7 天内到期
3. 待处理计数（`count/pending_count`）
4. 来源优先级（business > capability fallback）

## 4. 命中率输出位

本轮将命中率统计放入 contract：

- `diagnostics.extraction_stats.business_collections`
- `diagnostics.extraction_stats.business_rows_total`
- `diagnostics.extraction_stats.today_actions_business`
- `diagnostics.extraction_stats.today_actions_fallback`
- `diagnostics.extraction_stats.risk_actions_business`
- `diagnostics.extraction_stats.risk_actions_fallback`

用于后续按角色/环境对比命中率，不暴露到用户主视图。

## 5. 验证建议

1. 打开工作台，确认首屏行动项存在“紧急优先”排序变化；
2. 在 HUD/contract 导出中检查 `diagnostics.extraction_stats`；
3. 检查业务数据为空时是否自动回落到 capability fallback，且页面不空壳。

## 6. 下一轮建议

1. 为动作模型引入“金额影响/项目影响”维度；
2. 按角色输出阈值模板（PM/Finance/Owner）；
3. 形成 `action_ranking_policy_v1` 独立文档并冻结。

