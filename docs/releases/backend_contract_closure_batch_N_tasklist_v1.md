# Batch-N 可执行任务单（收口防回归门禁固化）

## 1. 任务目标

- 将本轮后端契约收口关键点固化为可执行门禁，防止回退。

## 2. 改动范围

- `scripts/verify/backend_contract_closure_guard.py`
- `Makefile`

## 3. 实现要点

- 新增守卫脚本 `backend_contract_closure_guard.py`，静态检查关键收口锚点：
  - system.init 最小 intents + intent_catalog_ref
  - meta.intent_catalog 的 catalog 输出
  - capability 真实性字段
  - scene_governance_v1 的 surface_mapping + scene_metrics
  - workspace_home blocks（hero/metric/risk/ops）
- 新增 Makefile target：
  - `verify.backend.contract.closure.guard`

## 4. 验收断言

- 执行 `make verify.backend.contract.closure.guard` 返回 PASS。

## 5. 执行命令

```bash
python3 scripts/verify/backend_contract_closure_guard.py
pnpm -C frontend/apps/web typecheck:strict
```

## 6. 交付产物

- 代码提交（Batch-N）
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
