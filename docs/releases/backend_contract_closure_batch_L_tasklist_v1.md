# Batch-L 可执行任务单（P2-3 scene 治理指标统一）

## 1. 任务目标

- 统一场景治理统计口径，固定输出如下字段：
  - `scene_registry_count`
  - `scene_deliverable_count`
  - `scene_navigable_count`
  - `scene_excluded_count`

## 2. 改动范围

- `addons/smart_core/core/scene_governance_payload_builder.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`

## 3. 实现要点

- 新增 `_scene_metrics_unified()`，融合 `delivery_policy` 与 `nav_policy` 计数来源。
- 在 `scene_governance_v1` 中新增 `scene_metrics`，输出统一命名统计口径。

## 4. 验收断言

- `system.init.data.scene_governance_v1.scene_metrics` 存在。
- `scene_metrics` 必含四个统一字段。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/core/scene_governance_payload_builder.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-L / P2-3）
- smoke 断言同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
