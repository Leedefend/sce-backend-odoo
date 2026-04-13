# ITER-2026-04-10-1680 Report

## Batch
- Batch: `P1-Batch9`
- Mode: `verify`
- Stage: `v2_primary minimum business usability validation`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core focus-intent business usability verification`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 验证 v2_primary 的真实业务可用性、v1/v2 漂移与 rollback 可恢复性。

## Change summary
- 新增脚本：
  - `scripts/verify/v2_primary_minimum_business_smoke.py`
  - `scripts/verify/v2_focus_intent_diff_audit.py`
  - `scripts/verify/v2_rollback_readiness_recheck.py`
- 更新门禁：`scripts/verify/v2_app_governance_gate_audit.py`
  - 新增阻断检查：smoke / diff / rollback recheck
- 新增产物：
  - `artifacts/v2/v2_primary_minimum_business_smoke_v1.json`
  - `artifacts/v2/v1_v2_focus_intent_diff_report_v1.json`
  - `artifacts/v2/v2_rollback_readiness_recheck_v1.json`
- 新增结论文档：`docs/ops/ITER-1680-business-usability-validation.md`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1680.yaml` ✅
- `python3 scripts/verify/v2_primary_minimum_business_smoke.py --json` ❌
  - fail: `meta.describe_model_missing_fields`
- `python3 scripts/verify/v2_focus_intent_diff_audit.py --json` ✅
  - risk: `P2`
- `python3 scripts/verify/v2_rollback_readiness_recheck.py --json` ❌
  - fail: `shadow_mode_smoke_fail`
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ❌
  - failed checks: `v2_primary_minimum_business_smoke.py`, `v2_rollback_readiness_recheck.py`
- `python3 scripts/verify/v2_focus_intent_promotion_state_machine_audit.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_compare_failure_summary.py --json` ✅
- `python3 -m py_compile ...` ✅
- `rg` 门禁规则与文档关键字检查 ✅

## Usability verdict
- Decision: **NO-GO**
- Blocking root cause:
  - `meta.describe_model` 在 v2_primary 下返回 `fields=[]`，不满足最小业务可用性。
  - rollback 模式切回 v2_shadow 后仍因同一 smoke 根因失败。

## Risk analysis
- Iteration result: `FAIL`
- Risk level: `high`（因为阻断门禁失败）
- Stop condition triggered: `acceptance_command_failed`

## Rollback suggestion
- 本批可回滚：
  - `git restore scripts/verify/v2_primary_minimum_business_smoke.py scripts/verify/v2_focus_intent_diff_audit.py scripts/verify/v2_rollback_readiness_recheck.py scripts/verify/v2_app_governance_gate_audit.py artifacts/v2/v2_primary_minimum_business_smoke_v1.json artifacts/v2/v1_v2_focus_intent_diff_report_v1.json artifacts/v2/v2_rollback_readiness_recheck_v1.json docs/ops/ITER-1680-business-usability-validation.md`

## Next suggestion
- 进入 `ITER-1680-fix`（仅 focus intents）：修复 `meta.describe_model` 返回字段面，再复跑 1680 三条阻断校验。
