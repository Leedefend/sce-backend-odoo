# Batch-K 可执行任务单（P2-2 surface_mapping 差异做实）

## 1. 任务目标

- 在 `scene_governance_v1` 中输出可审计的治理差异映射。
- 形成稳定结构：`before/after/removed`，并补充可读的 `removed.scene_codes_sample`。

## 2. 改动范围

- `addons/smart_core/core/scene_governance_payload_builder.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`

## 3. 实现要点

- 新增 `_governance_surface_mapping()`：
  - 汇总治理前后的 scene/capability 计数。
  - 输出 `removed` 计数。
  - 基于 `nav_policy.excluded_scenes_sample`（回退 `delivery_policy.excluded_scenes`）提取 `scene_codes_sample`。
- 在 `scene_governance_v1` 中新增 `surface_mapping` 块，保证契约固定可消费。

## 4. 验收断言

- `system.init.data.scene_governance_v1.surface_mapping` 存在。
- `surface_mapping` 内至少包含：
  - `before`
  - `after`
  - `removed`

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/core/scene_governance_payload_builder.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-K / P2-2）
- smoke 断言同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
