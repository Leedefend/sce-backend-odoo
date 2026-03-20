# Batch-C 可执行任务单（P0-2 角色真源统一）

## 1. 任务目标

- 固化 `role_surface.role_code` 为角色真源。
- 确保 `workspace_home.record.hero.role_code` 与 `page_orchestration_v1.page.context.role_code` 始终镜像真源。

## 2. 改动范围

- 角色镜像收口：
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - `addons/smart_core/core/page_contracts_builder.py`
- 验证与守卫：
  - `addons/smart_core/tests/test_v1_intent_smoke.py`
  - `scripts/verify/frontend_home_orchestration_consumption_guard.py`
  - `scripts/verify/page_orchestration_target_completion_guard.py`

## 3. 实现要点

- 新增 `role_source_code` 解析：从 `role_surface.role_code` 提取并作为上下文真源。
- 保留 `role_variant`（`pm/finance/owner`）用于布局策略，不再覆盖镜像字段。
- `workspace_home` 中：
  - `record.hero.role_code` 写入 `role_source_code`；
  - `page_orchestration_v1.page.context.role_code` 写入 `role_source_code`；
  - `meta.role_source_code` 与 `role_variant.role_layout_variant` 显式区分来源与布局变体。
- `page_contracts_builder` 同步支持 `role_source_code`，避免页面编排上下文偏离角色真源。

## 4. 验收断言

- `role_surface.role_code == workspace_home.record.hero.role_code`（字段存在时）。
- `role_surface.role_code == workspace_home.page_orchestration_v1.page.context.role_code`（字段存在时）。
- 允许 `role_variant` 与 `role_source_code` 不同，但必须显式可追踪。

## 5. 执行命令

```bash
python3 -m py_compile \
  addons/smart_core/core/workspace_home_contract_builder.py \
  addons/smart_core/core/page_contracts_builder.py \
  addons/smart_core/tests/test_v1_intent_smoke.py \
  scripts/verify/frontend_home_orchestration_consumption_guard.py \
  scripts/verify/page_orchestration_target_completion_guard.py

python3 scripts/verify/frontend_home_orchestration_consumption_guard.py
python3 scripts/verify/page_orchestration_target_completion_guard.py
```

## 6. 交付产物

- 代码提交（Batch-C / P0-2）
- 角色一致性断言（测试 + guard）
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
