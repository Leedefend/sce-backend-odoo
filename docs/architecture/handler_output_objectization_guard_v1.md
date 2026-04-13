# Handler Output Objectization Guard v1

状态：Frozen

## 1. 目标

为 `smart_core` handler 输出对象化迁移提供统一审计口径，避免回退到无序新增 legacy dict 返回。

## 2. 当前迁移策略

- 标准对象：`IntentExecutionResult`
- 兼容适配链：
  - `BaseIntentHandler.run()` 使用 `adapt_handler_result(...)`
  - `intent_dispatcher._normalize_result_shape()` 支持 `to_legacy_dict()`

## 3. migration gauge

审计脚本：`scripts/verify/handler_output_style_audit.py`

输出核心指标：

- `total_handlers`
- `objectized_handlers`
- `migration_gauge.objectized_ratio`
- `legacy_status_returns`
- `legacy_ok_returns`
- `err_helper_returns`

## 4. Guard 规则

1. 新增 handler 优先使用 `IntentExecutionResult`。
2. 允许 legacy dict 暂存，但必须可被审计脚本识别。
3. 对象化迁移不得改变外部 envelope 与错误语义。
4. 高风险意图（权限/财务）迁移必须走独立任务线。

## 5. 推荐验证

- `python3 scripts/verify/handler_output_style_audit.py --json`
- 将审计结果作为 C-line 迁移的 checkpoint 证据。

## 6. next_candidates

审计脚本新增 `next_candidates` 输出：

- `candidate_rank`
- `ok_returns`
- `status_returns`
- `err_returns`

用于快速选择下一批低风险迁移目标，提升迭代效率。
