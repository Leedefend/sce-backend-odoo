# Batch-E 可执行任务单（P1-1 system.init 分层）

## 1. 任务目标

- 在不破坏现有消费者的前提下，将 `system.init` 增加四区块分层结构。
- 将 `system.init` 从“超级聚合接口”逐步收口为“启动总线”。

## 2. 改动范围

- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/handlers/system_init.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`

## 3. 实现要点

- 新增 `init_contract_v1` 根字段，包含四区块：
  - `session`：用户/模式/通道上下文
  - `nav`：导航树/默认路由/导航元信息
  - `surface`：角色面与能力面（role/capability/feature）
  - `bootstrap_refs`：启动引用（`workspace_home_ref`）
- 保留现有顶层字段，兼容当前前端与守卫脚本。

## 4. 验收断言

- `system.init.data.init_contract_v1` 存在。
- 四区块键 `session/nav/surface/bootstrap_refs` 全存在。
- 不破坏既有 `nav/capabilities/intents` 顶层字段读取。

## 5. 执行命令

```bash
python3 -m py_compile \
  addons/smart_core/core/system_init_payload_builder.py \
  addons/smart_core/handlers/system_init.py \
  addons/smart_core/tests/test_v1_intent_smoke.py
```

## 6. 交付产物

- 代码提交（Batch-E / P1-1）
- smoke 断言更新
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
