# Batch-G 可执行任务单（P1-3 intent 目录独立化）

## 1. 任务目标

- 新增独立意图目录能力：`meta.intent_catalog`。
- `system.init` 默认仅返回最小启动意图集合，不再承载全量意图目录。
- `system.init` 返回 `intent_catalog_ref`，前端按需拉取完整目录。

## 2. 改动范围

- 后端：`addons/smart_core/handlers/meta_intent_catalog.py`
- 后端：`addons/smart_core/handlers/system_init.py`
- smoke：`addons/smart_core/tests/test_v1_intent_smoke.py`
- schema：`frontend/packages/schema/src/index.ts`

## 3. 实现要点

- `meta.intent_catalog`：返回 `intents + intents_meta` 全量目录。
- `system.init`：
  - 保留最小启动集合：`system.init/ui.contract/meta.intent_catalog/app.nav/app.open/auth.logout`（按可用性过滤）。
  - 新增 `intent_catalog_ref`：`intent=meta.intent_catalog`、`loaded=false`、`count=<full intents count>`。
- 保持兼容：`intents` 字段仍保留（但为最小集合），避免破坏既有消费方。

## 4. 验收断言

- `system.init`：
  - 包含 `intent_catalog_ref`。
  - `intents` 中包含 `meta.intent_catalog`。
  - `intents` 不再是全量（例如不包含 `api.data`）。
- `meta.intent_catalog`：
  - 返回全量 `intents/intents_meta`。
  - 可见 `api.data`、`system.init`、`ui.contract`、`meta.intent_catalog`。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/handlers/system_init.py addons/smart_core/handlers/meta_intent_catalog.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-G / P1-3）
- smoke 增补 `meta.intent_catalog` 覆盖
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
