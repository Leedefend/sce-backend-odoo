# ITER-2026-04-08-1358 Report

## Batch
- Batch: `3/3`

## Summary of change
- Added `Batch 3/3` task contract:
  - `agent_ops/tasks/ITER-2026-04-08-1358.yaml`
- Corrected scenario-layer role mapping to avoid broad PM/Finance capture:
  - `addons/smart_construction_scene/core_extension.py`
  - removed `smart_construction_custom.group_sc_role_project_user` from PM explicit mapping
  - removed `smart_construction_custom.group_sc_role_payment_read` from Finance explicit mapping
  - removed `smart_construction_core.group_sc_cap_project_user` from PM capability fallback

## Verification result
- Runtime stack confirmed on `sc_test`:
  - `smart_construction_scene:installed`
  - `smart_construction_custom:installed`
  - `smart_construction_core:installed`
  - `smart_scene:installed`
  - `smart_core:installed`
- Backend restarted on `ENV=test`, then acceptance commands passed:
  - `DB_NAME=sc_test E2E_BASE_URL=http://localhost:8071 python3 scripts/verify/native_business_admin_config_home_block_runtime_verify.py`
  - `DB_NAME=sc_test E2E_BASE_URL=http://localhost:8071 python3 scripts/verify/native_business_admin_config_home_block_clickpath_verify.py`
- Extra runtime evidence (intent payload role_surface):
  - `sc_fx_pm -> role_code=pm`
  - `sc_fx_finance -> role_code=finance`
  - `sc_fx_outsider -> role_code=owner`
  - `sc_fx_pure_outsider -> role_code=owner`

## Risk analysis
- Conclusion: `PASS`
- Residual note: acceptance脚本中的 outsider 样本当前仍使用 `sc_fx_outsider`（该账号并非纯 outsider），但本轮已补充纯 outsider 运行时证据并完成角色分离。

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-08-1358.yaml`
- `git restore addons/smart_construction_scene/core_extension.py`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1358.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1358.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- Freeze current role-surface split evidence and, if needed, open a tiny follow-up to align outsider verify sample account semantics with `sc_fx_pure_outsider`.
