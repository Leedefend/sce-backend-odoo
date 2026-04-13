# C1-4 ui_contract Objectization Screen v1

状态：Screen Freeze

## 1. 目标

在不改变 `ui_contract` 语义与外部契约的前提下，识别可安全对象化的分支与禁止直接改造区域。

## 2. 扫描结论

- `ui_contract` 属于高耦合 handler：聚合入口判断、场景兼容、错误分支密集。
- 当前输出口径以 `ok/data/meta` 与 `_err` 混合为主。

## 3. Tier 分类

### Tier-1（first safe slice）

1. 仅迁移“主成功返回”分支为 `IntentExecutionResult`。
2. 保留 `_err` 全部分支不变，避免错误语义漂移。

### Tier-2（受控扩展）

1. 迁移 `not_modified`/etag 相关返回分支。
2. 为核心子流程补 objectization checkpoint（不改业务逻辑）。

### Tier-3（高风险后置）

1. 全量 `_err` 分支对象化。
2. 历史兼容路径（legacy op）对象化。

## 4. forbidden branch

以下分支不得在同一批次与对象化混改：

- 场景选择与交付模式推导链
- native/custom 兼容分流
- 权限裁剪策略逻辑
- 任何涉及 contract 字段新增/删减

## 5. 执行建议

- 先开 `ui_contract` C1-4 safe implement 批次，仅处理 Tier-1 主成功分支。
- 每批必须运行 `handler_output_style_audit.py --json` 做迁移比率 checkpoint。
