# ITER-2026-04-09-1448 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Architecture declaration
- Layer Target: `Backend permission-boundary recovery`
- Module: `api.data.unlink and api.data.batch handlers`
- Module Ownership: `smart_core backend contract stack`
- Kernel or Scenario: `scenario`
- Reason: 清理 unlink/batch 的解释层组门禁越界。

## Change summary
- `addons/smart_core/handlers/api_data_unlink.py`
  - `REQUIRED_GROUPS` 调整为 `[]`。
- `addons/smart_core/handlers/api_data_batch.py`
  - `REQUIRED_GROUPS` 调整为 `[]`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1448.yaml` ✅
- `python3 -m py_compile addons/smart_core/handlers/api_data_unlink.py addons/smart_core/handlers/api_data_batch.py` ✅
- `make restart` ✅
- `make verify.portal.edit_tx_smoke.container DB_NAME=sc_demo E2E_LOGIN=sc_fx_pm E2E_PASSWORD=prod_like` ✅
- Odoo shell non-side-effect probe（PM/finance）✅
  - 证据：`artifacts/codex/boundary-probes/20260409T0336_unlink_batch_gate/unlink_batch_denial_source_probe.json`
  - 结果：两角色在 unlink/batch 均进入 handler 参数校验（`缺少参数 model`），未出现 `missing required groups`。

## Risk analysis
- 结论：`PASS`
- 风险级别：medium
- 风险说明：
  - unlink/batch 的组门禁已移除，后续需继续抽样真实参数路径，确认 ACL 拒绝与成功路径均符合预期。

## Rollback suggestion
- `git restore addons/smart_core/handlers/api_data_unlink.py`
- `git restore addons/smart_core/handlers/api_data_batch.py`
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1448.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1448.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- 继续批次：对 `chatter.post` 与 `api.onchange` 做同口径确认（含是否命中 write-gate），并完成最终越界清零报告。
