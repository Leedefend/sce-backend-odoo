# Batch-J 可执行任务单（P2-1 intent canonical/alias 体系）

## 1. 任务目标

- 在意图目录中输出可追溯的 canonical/alias 关系。
- 让每个 intent 都可判断其归属与别名状态。

## 2. 改动范围

- `addons/smart_core/core/intent_surface_builder.py`
- `addons/smart_core/handlers/meta_intent_catalog.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`
- `frontend/packages/schema/src/index.ts`

## 3. 实现要点

- `intents_meta` 增加：
  - `status`（canonical/alias）
  - `canonical`（归属主意图）
- 新增 `intent_catalog` 列表，逐条输出：
  - `name/status/canonical/version/required_groups_xmlids`
- alias 收集同时覆盖：
  - handler `ALIASES`
  - registry 中 `name != INTENT_TYPE` 的映射别名

## 4. 验收断言

- `meta.intent_catalog` 返回 `intent_catalog` 且为列表。
- `intents_meta.system.init.status=canonical`。
- `intent_catalog` 中存在 `app.init`，且 `status=alias`、`canonical=system.init`。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/core/intent_surface_builder.py addons/smart_core/handlers/meta_intent_catalog.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-J / P2-1）
- smoke 与 schema 同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
