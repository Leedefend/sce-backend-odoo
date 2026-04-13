# C1-4 Output Objectization Screen v1

状态：Screen Freeze（C1-4 前置筛查）

## 1. 目标

在不改变外部响应契约的前提下，建立 `IntentExecutionResult` 对象化接入顺序，逐步替代 handler 返回裸 dict 的模式。

## 2. 现状摘要

当前输出口径并存：

- `{"status": ..., "code": ..., "data": ...}`
- `{"ok": ..., "data": ..., "meta": ...}`
- `self._err(...)` / `err(...)` 辅助返回

`BaseIntentHandler.run()` 当前为“直接透传 handle 返回”，尚无统一 result object adapter。

## 3. Tier 分类

### Tier-1（优先 implement）

1. 建立 `IntentExecutionResult` 数据对象与 `to_legacy_dict()` 适配器。
2. 在 `BaseIntentHandler.run()` 增加“对象返回自动降级为 dict”适配层。

### Tier-2（次优先）

1. 首批低风险 handler 试点对象化返回（建议：`session_bootstrap`, `login`）。
2. 对 `intent_dispatcher._normalize_result_shape` 增加对象输入兼容。

### Tier-3（收尾）

1. 对 legacy `status`/`ok` 双口径做统一迁移计划。
2. 以 verify/snapshot 门禁逐步关闭裸 dict 新增入口。

## 4. first implement slices（冻结）

1. `C1-4-1`：新增 `IntentExecutionResult` + `BaseIntentHandler` adapter 接入。
2. `C1-4-2`：dispatcher normalize 增强对象兼容。
3. `C1-4-3`：2~3 个低风险 handler 试点对象返回。
4. `C1-4-4`：输出口径审计脚本与文档冻结。

## 5. 风险与停止条件

- 本批仅 screen，不改运行时代码。
- implement 若触及公开契约字段变更，必须先新增 snapshot guard 批次。
