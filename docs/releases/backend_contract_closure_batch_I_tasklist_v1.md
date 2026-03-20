# Batch-I 可执行任务单（P1-5 default_route 语义补全）

## 1. 任务目标

- 为 `default_route` 补齐可直接消费的语义字段：
  - `scene_key`
  - `route`
  - `reason`
- 降低前端对 `menu_id -> scene` 的反推依赖。

## 2. 改动范围

- `addons/smart_core/core/scene_nav_contract_builder.py`
- `addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py`
- `addons/smart_core/identity/identity_resolver.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`
- `frontend/packages/schema/src/index.ts`

## 3. 实现要点

- scene contract 导航默认入口改为结构化 `default_route`。
- 传统 nav dispatcher 默认入口返回补齐 `scene_key/route/reason`。
- identity resolver 的导航回退入口也统一输出语义字段。

## 4. 验收断言

- `system.init.data.default_route`（dict 时）必须包含：
  - `scene_key`
  - `route`
  - `reason`
- 兼容保留：`menu_id` 仍可用。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/core/scene_nav_contract_builder.py addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py addons/smart_core/identity/identity_resolver.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-I / P1-5）
- smoke 断言与 schema 同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
