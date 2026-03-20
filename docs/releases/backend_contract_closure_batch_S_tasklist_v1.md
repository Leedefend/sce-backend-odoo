# Batch-S 可执行任务单（收口门禁 summary artifact + schema guard）

## 1. 任务目标

- 为 `verify.backend.contract.closure.mainline` 输出统一 summary artifact。
- 增加 summary schema guard，确保产物结构稳定可消费。

## 2. 改动范围

- `scripts/verify/backend_contract_closure_mainline_summary.py`
- `scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py`
- `Makefile`

## 3. 实现要点

- 聚合门禁运行后输出：
  - `artifacts/backend/backend_contract_closure_mainline_summary.json`
- summary 包含：
  - `ok`
  - `generated_at`
  - `checks.{closure_structure_guard,closure_snapshot_guard,intent_alias_snapshot_guard}`
  - `overall.{status,policy}`
- mainline 目标内联执行 schema guard。
- 新增独立目标：
  - `verify.backend.contract.closure.mainline.summary.schema.guard`

## 4. 验收断言

- `make verify.backend.contract.closure.mainline` PASS，并生成 summary artifact。
- `python3 scripts/verify/backend_contract_closure_mainline_summary_schema_guard.py` PASS。

## 5. 执行命令

```bash
make verify.backend.contract.closure.mainline
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-S）
- summary artifact + schema guard 生效
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
