# Batch-F 可执行任务单（P1-2 workspace_home 按需加载）

## 1. 任务目标

- `system.init` 默认不返回完整 `workspace_home`，改为返回 `workspace_home_ref`。
- 仅在显式请求 `with=["workspace_home"]` 或 `with_preload=true` 时返回完整 `workspace_home`。

## 2. 改动范围

- 后端：`addons/smart_core/handlers/system_init.py`
- 前端：`frontend/apps/web/src/stores/session.ts`（显式请求 `workspace_home` 保持当前行为）
- 契约类型：`frontend/packages/schema/src/index.ts`
- smoke：`addons/smart_core/tests/test_v1_intent_smoke.py`

## 3. 实现要点

- 增加 `with` 参数解析（支持字符串/数组）。
- 计算 `include_workspace_home`：
  - `with_preload=true` 或 `with` 包含 `workspace_home` 时加载完整数据。
  - 否则移除 `workspace_home` 顶层字段。
- 总是返回：
  - `workspace_home_ref.intent=ui.contract`
  - `workspace_home_ref.scene_key=<landing_scene_key>`
  - `workspace_home_ref.loaded=<bool>`
- 前端主链请求改为显式 `with: ['workspace_home']`，确保当前页面功能不退化。

## 4. 验收断言

- 默认 `system.init`：有 `workspace_home_ref`、无 `workspace_home`。
- `system.init` 带 `with=["workspace_home"]`：同时有 `workspace_home` 与 `workspace_home_ref.loaded=true`。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/handlers/system_init.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-F / P1-2）
- smoke 断言更新
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
