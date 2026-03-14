# Workspace Scene Template

## 适用场景

- 工作台类场景：强调角色入口、待办聚合、风险与任务闭环。

## 标准结构

- `scene/page`：工作台标识、默认 route。
- `zones`：`hero`、`today_focus`、`entries`、`risk_alerts`、`my_items`。
- `actions`：`open_landing`、`open_workbench`、`open_detail` 等动作语义。

## 最低产品化要求（R2 -> R3）

- R2：具备基本 zone/block + data_source。
- R3：具备角色差异（zone 顺序/动作模板差异）和策略化入口。

## 检查清单

- 是否有按角色差异化的 zone 顺序。
- 是否有今日行动模板与优先级。
- 是否可追踪 action 使用（埋点/统计）。

