# Batch-M 可执行任务单（P2-4 首页 block 化）

## 1. 任务目标

- 为 `workspace_home` 增加统一 `blocks` 结构，向编排驱动渲染过渡。
- 在保持 `hero/metrics/risk/ops` 兼容字段的同时，提供 block-first 入口。

## 2. 改动范围

- `addons/smart_core/core/workspace_home_contract_builder.py`
- `addons/smart_core/tests/test_v1_intent_smoke.py`

## 3. 实现要点

- `workspace_home.blocks` 新增四类 block：
  - `hero`
  - `metric`
  - `risk`
  - `ops`
- 每个 block 统一输出：
  - `type`
  - `key`
  - `data`
  - `actions`

## 4. 验收断言

- `system.init` 在 `with=["workspace_home"]` 场景下，`workspace_home.blocks` 为非空列表。
- 任一 block 至少包含：`type/data/actions`。

## 5. 执行命令

```bash
python3 -m py_compile addons/smart_core/core/workspace_home_contract_builder.py addons/smart_core/tests/test_v1_intent_smoke.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-M / P2-4）
- smoke 断言同步
- 上下文日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
