# Batch-B 可执行任务单（P0-3 版本统一）

## 1. 任务目标

- 将 `login/system.init/ui.contract` 顶层元数据的 `contract_version` 统一到语义化版本。
- 为主链意图补齐 `schema_version` 语义字段，并新增版本职责守卫（drill）。

## 2. 改动范围

- 后端版本元数据：
  - `addons/smart_core/controllers/intent_dispatcher.py`
  - `addons/smart_core/handlers/system_init.py`
  - `addons/smart_core/handlers/ui_contract.py`
  - `addons/smart_core/core/exceptions.py`
- 版本守卫：
  - `scripts/verify/contract_version_evolution_drill.py`
  - `scripts/verify/baselines/contract_version_evolution.json`
  - `scripts/verify/contract_envelope_guard.py`

## 3. 实现要点

- `contract_version` 默认值统一为 `1.0.0`。
- `intent_dispatcher` 顶层 `meta` 默认补齐 `schema_version=1.0.0`。
- `ui.contract` 在保留现有业务 `schema_version` 的同时，补充 `response_schema_version=1.0.0`。
- `contract_version_evolution_drill`：
  - 增加 `login` 契约校验；
  - token 兼容 `data.session.token` 与 `data.token`；
  - 校验 `contract_version/schema_version` 为 semver；
  - `ui.contract` 校验 `response_schema_version`。

## 4. 验收断言

- `login/system.init/ui.contract` 的 `meta.contract_version` 为 semver（当前目标：`1.0.0`）。
- `login/system.init` 顶层 `meta.schema_version` 为 semver。
- `ui.contract` 至少包含 `meta.response_schema_version` 且为 semver。
- `verify.contract.version.evolution.drill` 在可联通环境通过。

## 5. 执行命令

```bash
python3 -m py_compile \
  addons/smart_core/controllers/intent_dispatcher.py \
  addons/smart_core/handlers/system_init.py \
  addons/smart_core/handlers/ui_contract.py \
  addons/smart_core/core/exceptions.py \
  scripts/verify/contract_version_evolution_drill.py \
  scripts/verify/contract_envelope_guard.py

# 需要可访问本地 intent 服务
python3 scripts/verify/contract_version_evolution_drill.py
```

## 6. 交付产物

- 代码提交（Batch-B / P0-3）
- 版本守卫结果（可联通环境下）
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
