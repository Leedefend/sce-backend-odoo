# Frontend Guesswork Due To Backend Contract Gaps v1

## Purpose
列出前端仍需推断/兜底的部分，这些点应视为后端契约闭环未完成。

## Guesswork List
1. 标题字段回退选择（`display_name/name` 等）。
2. 状态字段语义归一（`state/status/stage_id/kanban_state` 多来源兜底）。
3. 批量动作可见性组合判断（模型 + 权限 + contract rights）。
4. 列表汇总口径从当前页记录推断（已开始修复为后端总量优先）。
5. relation 区块渲染类型（table/cards）缺少稳定后端指示时前端回退。
6. 某些按钮语义（primary/secondary/danger）仍需前端 fallback。
7. view mode 切换时对 contract 缺失字段进行客户端降级补齐。

## Root Cause
- 后端尚未提供单一且完整的 semantic page contract，导致前端在 `ActionView.vue` 内承担了部分解释责任。

## Closure Goal
- 把上述 guesswork 逐步迁移到后端契约输出，并用 verify 快照锁定。
