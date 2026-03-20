# Batch-A 可执行任务单（P0-1 Login 契约收口）

## 1. 任务目标

- 将 `login` 契约收口为认证+启动指引主干结构：`session/user/entitlement/bootstrap/meta`。
- 默认模式去除 `groups` 与 `system.intents`，并保留迁移期 `compat/debug` 能力。

## 2. 改动范围

- 后端：`addons/smart_core/handlers/login.py`
- 前端：
  - `frontend/packages/schema/src/index.ts`
  - `frontend/apps/web/src/stores/session.ts`
- 验证：
  - `addons/smart_core/tests/test_v1_intent_smoke.py`
  - `scripts/verify/contract_envelope_guard.py`（如需补字段断言）

## 3. 实现要点

- `default`：仅返回新结构（允许保留顶层 token 仅在兼容窗口内）。
- `compat`：返回迁移兼容字段（旧前端可用）。
- `debug`：附加 `groups/system.intents` 调试信息，不进入主产品链路。
- `bootstrap.next_intent` 固定为 `system.init`。

## 4. 验收断言

- 结构断言：`default` 返回必须包含且仅包含主干结构 `session/user/entitlement/bootstrap/meta`。
- 行为断言：前端登录成功后仅触发 `system.init` 启动路径。
- 兼容断言：
  - `compat` 下旧结构可消费
  - `debug` 下仅增加调试字段

## 5. 执行命令（建议顺序）

```bash
# 1) 后端/前端实现后
pnpm -C frontend typecheck:strict

# 2) 关键 smoke
pnpm -C frontend gate
CI_SCENE_DELIVERY_PROFILE=restricted make verify.product.delivery.mainline

# 3) 契约烟测
python3 scripts/verify/contract_envelope_guard.py
```

## 6. 交付产物

- 代码提交（feat/fix）
- 契约验证结果（命令输出）
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`

