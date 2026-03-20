# Batch-O 可执行任务单（主链门禁串联 + 阶段总览）

## 1. 任务目标

- 把 `backend_contract_closure_guard` 串入 `verify.product.delivery.mainline`。
- 输出本阶段收口状态总览，便于交付与合并前审阅。

## 2. 改动范围

- `Makefile`
- `docs/releases/backend_contract_closure_phase_status_v1.md`

## 3. 实现要点

- `verify.product.delivery.mainline` 新增步骤：
  - `step=backend_contract_closure_guard`
  - 失败时设置 `CONTRACT_CLOSURE_STATUS=FAIL`
  - 汇总成功条件纳入 `CONTRACT_CLOSURE_STATUS=PASS`
- 补充阶段总览文档，覆盖 Batch-E~N 完成状态与下一步建议。

## 4. 验收断言

- mainline 日志中出现：
  - `step=backend_contract_closure_guard`
  - `contract_closure_guard=PASS|FAIL|SKIP`
- 阶段状态文档存在并可审阅。

## 5. 执行命令

```bash
make verify.backend.contract.closure.guard
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-O）
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
