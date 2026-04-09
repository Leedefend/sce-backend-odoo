# ITER-2026-04-09-1447 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Architecture declaration
- Layer Target: `Backend permission-boundary recovery`
- Module: `file.upload intent handler`
- Module Ownership: `smart_core backend contract stack`
- Kernel or Scenario: `scenario`
- Reason: 消除 file.upload 的解释层组门禁越界，恢复由 ACL/模型策略裁决。

## Change summary
- `addons/smart_core/handlers/file_upload.py`
  - `REQUIRED_GROUPS` 从 `smart_core.group_smart_core_data_operator` 调整为 `[]`。
  - 作用：移除解释层硬编码组门禁，避免在业务事实层之前提前拒绝。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1447.yaml` ✅
- `python3 -m py_compile addons/smart_core/handlers/file_upload.py` ✅
- `make restart` ✅
- `make verify.portal.edit_tx_smoke.container DB_NAME=sc_demo E2E_LOGIN=sc_fx_pm E2E_PASSWORD=prod_like` ✅
- `make verify.portal.execute_button_smoke.container DB_NAME=sc_demo E2E_LOGIN=sc_fx_pm E2E_PASSWORD=prod_like` ✅
- Odoo shell denial-source probe（PM/finance）✅
  - 证据：`artifacts/codex/boundary-probes/20260409T0330_file_upload_gate/file_upload_denial_source_probe.json`
  - 结果：
    - `sc_fx_pm`：`file.upload` 成功
    - `sc_fx_finance`：`403 无上传权限`（ACL 拒绝）
    - 未出现 `missing required groups` / `requires REQUIRED_GROUPS`

## Risk analysis
- 结论：`PASS`
- 风险级别：medium
- 风险说明：
  - file.upload 从“组门禁+ACL”收敛为“ACL+allowed_models”；需后续统一审计其余写意图（如 unlink/batch/chatter）。

## Rollback suggestion
- `git restore addons/smart_core/handlers/file_upload.py`
- `git restore agent_ops/reports/2026-04-09/report.ITER-2026-04-09-1447.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-09-1447.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next suggestion
- 继续下一批：把 `api.data.unlink`、`api.data.batch`、`chatter.post` 的 REQUIRED_GROUPS 逐个做同口径收敛，并复验拒绝来源。
