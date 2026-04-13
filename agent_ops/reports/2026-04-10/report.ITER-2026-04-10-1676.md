# ITER-2026-04-10-1676 Report

## Batch
- Batch: `P1-Batch5`
- Mode: `implement`
- Stage: `focus intent compare error correction`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core focus-intent compare error correction`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 修复三条 focus intents 在 v2_shadow compare 下共性 `AUTHENTICATION_REQUIRED`。

## Change summary
- 更新：`addons/smart_core/core/intent_router.py`
  - 新增 `_enrich_v2_auth_context`，在 `v2_primary/v2_shadow` 调用前补齐 `user_id/company_id`。
  - `v2_shadow` compare 旁路执行改为使用补齐后的 context。
- 更新 compare 审计（3个）：
  - `scripts/verify/v2_session_bootstrap_compare_audit.py`
  - `scripts/verify/v2_meta_describe_model_compare_audit.py`
  - `scripts/verify/v2_ui_contract_compare_audit.py`
  - 增加 `user_id/company_id` 样本上下文，并新增 `v2_status_not_ok` 审计断言。
- 更新 failure diagnose（3个）：
  - `scripts/verify/v2_session_bootstrap_compare_failure_diagnose.py`
  - `scripts/verify/v2_meta_describe_model_compare_failure_diagnose.py`
  - `scripts/verify/v2_ui_contract_compare_failure_diagnose.py`
  - 当无错误码时输出 `failure_stage=none`、`suggested_fix_area=none`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1676.yaml` ✅
- `python3 scripts/verify/v2_session_bootstrap_compare_audit.py --json` ✅
- `python3 scripts/verify/v2_meta_describe_model_compare_audit.py --json` ✅
- `python3 scripts/verify/v2_ui_contract_compare_audit.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_compare_summary.py --json` ✅
- `python3 scripts/verify/v2_session_bootstrap_compare_failure_diagnose.py --json` ✅
- `python3 scripts/verify/v2_meta_describe_model_compare_failure_diagnose.py --json` ✅
- `python3 scripts/verify/v2_ui_contract_compare_failure_diagnose.py --json` ✅
- `python3 scripts/verify/v2_focus_intent_compare_failure_summary.py --json` ✅
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅
- `python3 -m py_compile addons/smart_core/core/intent_router.py scripts/verify/v2_session_bootstrap_compare_audit.py scripts/verify/v2_meta_describe_model_compare_audit.py scripts/verify/v2_ui_contract_compare_audit.py scripts/verify/v2_focus_intent_compare_summary.py` ✅

## Correction result (core)
- compare 共性认证错误已消除：三条 focus intents `v2_status=ok`。
- failure diagnose 汇总从 `NEEDS_CORRECTION` 变为 `READY_FOR_CANDIDATE`。
- 当前仍有 `root_shape_mismatch`（结构差异），但已不属于认证上下文阻断。

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批仅补齐 compare 认证上下文与审计规则，不改变业务事实或权限定义。

## Rollback suggestion
- `git restore addons/smart_core/core/intent_router.py scripts/verify/v2_session_bootstrap_compare_audit.py scripts/verify/v2_meta_describe_model_compare_audit.py scripts/verify/v2_ui_contract_compare_audit.py scripts/verify/v2_session_bootstrap_compare_failure_diagnose.py scripts/verify/v2_meta_describe_model_compare_failure_diagnose.py scripts/verify/v2_ui_contract_compare_failure_diagnose.py`

## Next suggestion
- 进入 `1677`：promotion/rollback state machine，基于 `allow_v2_candidate=true` 控制三条 focus intents 的升级路径。
