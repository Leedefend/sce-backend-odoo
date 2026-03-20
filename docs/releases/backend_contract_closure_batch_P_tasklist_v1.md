# Batch-P 可执行任务单（契约快照基线：intent_catalog + scene_governance_v1）

## 1. 任务目标

- 为以下关键契约建立可比对快照基线并接入门禁：
  - `meta.intent_catalog` payload keys
  - `scene_governance_v1` payload keys

## 2. 改动范围

- `scripts/verify/backend_contract_closure_snapshot_guard.py`
- `scripts/verify/baselines/backend_contract_closure_snapshot.json`
- `Makefile`

## 3. 实现要点

- 新增快照守卫脚本：
  - 提取 `meta_intent_catalog.handle` 返回 payload keys
  - 提取 `build_scene_governance_payload_v1` 返回 payload keys
  - 写出当前快照：`artifacts/backend/backend_contract_closure_snapshot.json`
  - 对比基线：`scripts/verify/baselines/backend_contract_closure_snapshot.json`
- `verify.backend.contract.closure.guard` 串联执行快照守卫。
- 新增独立目标：`verify.backend.contract.closure.snapshot.guard`。

## 4. 验收断言

- `python3 scripts/verify/backend_contract_closure_snapshot_guard.py` PASS。
- `make verify.backend.contract.closure.guard` 同时覆盖结构守卫与快照守卫。

## 5. 执行命令

```bash
python3 scripts/verify/backend_contract_closure_snapshot_guard.py
make verify.backend.contract.closure.guard
```

## 6. 交付产物

- 代码提交（Batch-P）
- 基线文件与门禁串联生效
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
