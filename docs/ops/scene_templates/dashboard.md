# Dashboard Scene Template

## 适用场景

- 驾驶舱/总览类场景：强调指标、告警、趋势和主动作。

## 标准结构

- `scene/page`：声明 scene 基础信息、route、标题。
- `zones`：`header`、`metrics`、`progress`、`risk`、`actions`。
- `blocks`：每个 zone 至少有一个主 block，且声明 data_source。

## 最低产品化要求（R2 -> R3）

- R2：有完整 zone/block 编排，且可渲染。
- R3：补充角色差异（至少 2 角色）、主动作优先级、告警策略。

## 检查清单

- 是否声明主 KPI 与口径。
- 是否存在“今日关键动作”入口。
- 是否有风险提醒与 drill-down。

