# Batch-R 可执行任务单（收口门禁聚合 mainline）

## 1. 任务目标

- 提供一个可被 CI 直接调用的后端契约收口聚合门禁目标。
- 将交付主线中的收口验证步骤统一切换为该聚合目标。

## 2. 改动范围

- `Makefile`

## 3. 实现要点

- 新增目标：`verify.backend.contract.closure.mainline`
  - `backend_contract_closure_guard`
  - `backend_contract_closure_snapshot_guard`
  - `intent_canonical_alias_snapshot_guard`
- `verify.product.delivery.mainline` 的收口步骤改为调用：
  - `verify.backend.contract.closure.mainline`

## 4. 验收断言

- `make verify.backend.contract.closure.mainline` PASS。
- `verify.product.delivery.mainline` 日志显示 `step=backend_contract_closure_mainline`。

## 5. 执行命令

```bash
make verify.backend.contract.closure.mainline
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-R）
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
