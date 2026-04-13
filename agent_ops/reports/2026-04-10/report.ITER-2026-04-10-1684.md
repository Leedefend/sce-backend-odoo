# ITER-2026-04-10-1684 Report

## Batch
- Batch: `P1-Batch13`
- Mode: `implement`
- Stage: `v2 ui.contract dispatch failure hotfix`

## Architecture declaration
- Layer Target: `Backend v2 dispatch pipeline`
- Module: `smart_core v2 kernel request-schema handling`
- Module Ownership: `addons/smart_core/v2/kernel`
- Kernel or Scenario: `kernel`
- Reason: 修复 `request_schema` 契约标识误导入导致 `No module named 'v2'`。

## Change summary
- Updated `addons/smart_core/v2/kernel/pipeline.py`
  - 对 `v2.*.v1` 形态的契约标识符直接视为 schema-id，不执行 Python import
  - 仅对可导入前缀（`odoo.addons.` / `addons.` / `smart_core.`）执行动态导入

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1684.yaml` ✅
- `python3 -m py_compile addons/smart_core/v2/kernel/pipeline.py` ✅
- `make restart` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅收紧 schema 动态导入条件，不涉及业务事实与权限模型。

## Rollback suggestion
- `git restore addons/smart_core/v2/kernel/pipeline.py`

## Next suggestion
- 用户重试菜单点击；若仍失败，附上同一 trace_id 的最新响应和 odoo 日志时间点。
