# ITER-2026-04-08-1393 Report

## Batch
- Batch: `1/1`

## Summary of change
- 事实核对：开发态主链端口为 `8069`。
- 根因确认：`contract_api_mode_smoke.py` 默认 `FRONTEND_API_BASE_URL=http://localhost:8070`，与当前环境不一致导致超时。
- 修复：`scripts/verify/contract_api_mode_smoke.py`
  - 默认 base URL 改为 `get_base_url()`（当前即 `http://localhost:8069`）；
  - 保留 `FRONTEND_API_BASE_URL` 覆盖能力。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1393.yaml` ✅
- `make verify.contract.api.mode.smoke DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅（`PASS (http://localhost:8069)`）
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 8070 超时阻断；
  - 新阻断前移到 `verify.frontend.search_groupby_savedfilters.guard`（frontend marker 缺失）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为前端搜索/分组/已保存过滤契约守卫，不属于端口口径问题。

## Rollback suggestion
- `git restore scripts/verify/contract_api_mode_smoke.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1393.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1393.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1393.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：修复或对齐 `verify.frontend.search_groupby_savedfilters.guard` 所需 marker（`action_view` 中 resolve context / saved filters / group_by 语义）。
