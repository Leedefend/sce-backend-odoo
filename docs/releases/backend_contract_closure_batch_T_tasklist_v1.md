# Batch-T 可执行任务单（收口 summary 接入交付总览）

## 1. 任务目标

- 将 `backend_contract_closure_mainline_summary.json` 纳入 `delivery_readiness_ci_summary` 汇总链。
- 让交付看板在单一 summary 中可见契约收口状态。

## 2. 改动范围

- `scripts/verify/delivery_readiness_scoreboard_refresh.py`

## 3. 实现要点

- 读取 `artifacts/backend/backend_contract_closure_mainline_summary.json`。
- 在 `delivery_readiness_ci_summary.json` 增加 `contract_closure` 段：
  - `present/path/ok/generated_at/policy/status/checks`
- 在 `delivery_readiness_ci_summary.md` 增加 `Contract Closure` 小节与三项检查状态表。

## 4. 验收断言

- 执行 `refresh.delivery.readiness.scoreboard` 后：
  - JSON summary 包含 `contract_closure`。
  - Markdown summary 包含 `## Contract Closure`。

## 5. 执行命令

```bash
python3 -m py_compile scripts/verify/delivery_readiness_scoreboard_refresh.py
make refresh.delivery.readiness.scoreboard
```

## 6. 交付产物

- 代码提交（Batch-T）
- 迭代日志更新：`docs/ops/iterations/delivery_context_switch_log_v1.md`
