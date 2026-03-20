# Batch-D 可执行任务单（P0-4 启动链路唯一化）

## 1. 任务目标

- 固化产品主链：`login -> system.init -> ui.contract(按需)`。
- 明确白名单例外：`session.bootstrap`（dev/test）、health/ping、public/minimal 只读页。

## 2. 改动范围

- 前端启动链：
  - `frontend/apps/web/src/stores/session.ts`
  - `frontend/apps/web/src/api/client.ts`
  - `frontend/apps/web/src/views/LoginView.vue`（仅消费链路验证）
- 启动链守卫：
  - `scripts/verify/startup_chain_mainline_guard.py`

## 3. 实现要点

- 登录后读取 `bootstrap.next_intent`，仅允许 `system.init/session.bootstrap`。
- `session.loadAppInit()` 强制调用 `system.init`，不再发 `app.init`。
- 若 `next_intent=session.bootstrap`，先执行 bootstrap，再进入 `system.init`。
- 客户端网络诊断日志统一标注为 `system.init`。

## 4. 验收断言

- `session.ts` 中 `loadAppInit` 请求意图必须是 `system.init`。
- 启动链静态守卫通过：
  - 存在 `intent: 'login'`、`intent: 'system.init'`
  - 不存在 `intent: 'app.init'`
  - 存在白名单 `system.init/session.bootstrap`
- 前端严格类型检查通过。

## 5. 执行命令

```bash
python3 -m py_compile scripts/verify/startup_chain_mainline_guard.py
python3 scripts/verify/startup_chain_mainline_guard.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-D / P0-4）
- 启动链守卫结果
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
