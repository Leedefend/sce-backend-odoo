# SCEMS v1.0 Round 4 工作台用户视角迭代计划

## 1. 目标

本轮目标是基于 `workspace_home_contract_builder` 完成“用户首跳体验”收口，让工作台从“能力摘要页”进一步收敛为“业务行动中枢”。

用户进入工作台后，10 秒内应回答三个问题：

1. 今天先处理什么；
2. 哪些风险必须优先处理；
3. 当前业务状态是否偏离。

## 2. 边界与不改项

本轮严格不改：

- 登录链路与 token/session 机制；
- scene governance / delivery policy 主机制；
- ACL 基线与角色权限模型；
- page_orchestration_v1 主协议。

本轮允许改动：

- `workspace_home_contract_builder` 的页面语义收口；
- 首页默认可见区块与文案层级；
- 调试/能力清单类信息的默认显隐策略；
- 与用户视图相关的最小前端消费映射。

## 3. 批次执行

### Batch A：首跳语义收敛（当前批）

- 前置 `today_actions` 与 `risk`，强化“行动优先”；
- `group_overview` 收敛为“常用功能”；
- 默认隐藏 `scene_groups` 与 `filters` 噪音区。

### Batch B：真实业务动作链路校准

- 校准 `today_actions` 与 `risk.actions` 的业务优先占比；
- 补齐 PM 角色下可见任务/风险事实数据；
- 确保 fallback 只兜底，不伪装为业务指标。

### Batch C：首跳可观测与验收

- 输出“工作台点击 -> intent”链路清单；
- 校准工作台验收标准（10 秒 / 30 秒）；
- 执行最小回归并记录。

## 4. 验收标准

- 页面主区只保留 `hero / today_focus / analysis / quick_entries` 的产品叙事；
- 用户默认视图不展示调试字段与能力清单噪音；
- `today_actions` 与 `risk.actions` 可直接一跳进入业务页；
- 既有 verify 主链路不被破坏。

## 5. 最小回归

建议本轮结束后至少执行：

- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.phase_next.evidence.bundle`
