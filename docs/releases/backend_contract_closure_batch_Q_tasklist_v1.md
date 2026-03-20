# Batch-Q 可执行任务单（intent canonical/alias 快照与漂移门禁）

## 1. 任务目标

- 产出 `intent canonical/alias` 审计快照。
- 建立基线与漂移守卫，纳入后端契约收口门禁。

## 2. 改动范围

- `scripts/verify/intent_canonical_alias_snapshot_guard.py`
- `scripts/verify/baselines/intent_canonical_alias_snapshot.json`
- `Makefile`

## 3. 实现要点

- 从 `docs/contract/exports/intent_catalog.json` 提取 canonical+alias 行。
- 输出 artifact：`artifacts/backend/intent_canonical_alias_snapshot.json`
- 对比 baseline：`scripts/verify/baselines/intent_canonical_alias_snapshot.json`
- 新增 make 目标：
  - `verify.intent.canonical_alias.snapshot.guard`
- `verify.backend.contract.closure.guard` 串联执行该漂移守卫。

## 4. 验收断言

- `python3 scripts/verify/intent_canonical_alias_snapshot_guard.py` PASS。
- `make verify.backend.contract.closure.guard` 包含该守卫并 PASS。

## 5. 执行命令

```bash
python3 scripts/verify/intent_canonical_alias_snapshot_guard.py
make verify.backend.contract.closure.guard
```

## 6. 交付产物

- 代码提交（Batch-Q）
- 基线与 artifact 生效
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
