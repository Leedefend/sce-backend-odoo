# Backend View Contract Gap Classification v1

## G1 Parsing Gaps
1. `load_view` 路径仅 form 解析（`view_dispatcher.py` 仅注册 form）。
2. tree/kanban/search 在 legacy parser 栈不可用或不完整。

## G2 Standardization Gaps
1. `load_view` vs `load_contract` 输出 shape 不一致。
2. 按钮、relation、permission 的字段命名与层级不统一。

## G3 Semantic-Lift Gaps
1. 缺少统一 `semantic_page.zones[].blocks[]` 输出。
2. chatter/x2many/notebook 虽可解析，但未稳定落到统一 zone/block。

## G4 Behavior-Explanation Gaps
1. 按钮可执行性、禁用原因在不同链路分散。
2. row/card actions 的可执行理由未完全契约化。

## G5 Permission/State Gaps
1. modifiers 与最终 verdict（visible/editable/executable）的统一口径不足。
2. 某些页面仍需前端组合判断权限与状态。

## G6 Contract-Governance Gaps
1. 缺少“统一 semantic shape”快照门禁。
2. 缺少以样本页面为中心的覆盖退化检测。

## Overall Risk
- 当前系统处于“功能可跑，但契约一致性不足”的状态，容易导致前端 fallback 持续累积。
