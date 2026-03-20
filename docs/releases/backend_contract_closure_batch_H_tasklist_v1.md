# Batch-H 可执行任务单（P1-4 capability 交付真实性增强）

## 1. 任务目标

- 在 capability 用户契约中补齐真实交付标识：
  - `delivery_level`
  - `target_scene_key`
  - `entry_kind`
- 让前端与交付治理可区分独立入口能力、共享入口能力和占位能力。

## 2. 改动范围

- 归一化治理：`addons/smart_core/utils/contract_governance.py`
- smoke：`addons/smart_core/tests/test_v1_intent_smoke.py`
- schema：`frontend/packages/schema/src/index.ts`

## 3. 实现要点

- 扩展 capability canonical map 和用户可见白名单，允许新字段透出。
- 在 `normalize_capabilities` 中新增派生逻辑：
  - `target_scene_key`：优先显式字段，其次 `default_payload.scene_key`，最后从 `default_payload.route` 提取 `scene=`。
  - `entry_kind`：显式优先，否则按是否具备直接入口语义推导 `exclusive/alias`。
  - `delivery_level`：显式优先，否则按入口可达性与 `entry_kind` 推导 `exclusive/shared/placeholder`。

## 4. 验收断言

- `system.init.data.capabilities[*]` 至少包含：
  - `delivery_level`
  - `target_scene_key`
  - `entry_kind`
- 值域校验：
  - `delivery_level in {exclusive, shared, placeholder}`
  - `entry_kind in {exclusive, alias}`

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/utils/contract_governance.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-H / P1-4）
- smoke 断言与 schema 同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
