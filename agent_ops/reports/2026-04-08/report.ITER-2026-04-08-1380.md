# ITER-2026-04-08-1380 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因一次性修复（兼容层）：
  - `addons/smart_core/handlers/login.py`
    - 默认模式补回 `data.token/data.token_type/data.expires_at` 兼容字段（真源仍为 `data.session.*`）。
  - `addons/smart_core/handlers/system_init.py`
    - 补回 `data.contract_mode` 兼容字段；
    - user 模式下剥离 `scene_channel_selector/scene_channel_source_ref/scene_diagnostics/diagnostic`；
    - hud 模式下补齐 `hud` trace 键与 `scene_diagnostics`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1380.yaml` ✅
- `make verify.contract.mode.smoke DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅（由 FAIL → PASS）
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 新阻断：`verify.scene.contract_v1.field_schema.guard`
  - 错误：`scene count below baseline: 8 < 50`、`scene row schema violations: 8`

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - 本轮代码根因修复已生效（关键 token/mode smoke 已通过）；
  - 当前 preflight 阻断已转为运行环境基线问题（DB 场景数据不足），非同一代码根因。

## Rollback suggestion
- `git restore addons/smart_core/handlers/login.py`
- `git restore addons/smart_core/handlers/system_init.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1380.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1380.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1380.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开环境治理批次：对 `sc_demo` 回填 scene baseline（或切换到满足基线的 `sc_test`），再重跑 preflight。
