# ITER-2026-04-10-1681 Report

## Batch
- Batch: `P1-Batch10`
- Mode: `implement`
- Stage: `focus intent meta.describe_model field-surface restoration`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core meta.describe_model field-surface restoration`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 修复 `meta.describe_model` 字段面为空导致的 1680 阻断失败。

## Change summary
- 更新 `addons/smart_core/v2/services/meta_service.py`
  - 新增 legacy baseline 读取与通用字段回退逻辑。
  - `project.project` 优先复用 `artifacts/contract/rootfix/menu_278_admin.json` 的字段定义。
- 更新 `addons/smart_core/v2/services/meta_describe_model_service.py`
  - `fields` 类型从 list 处理改为 dict 处理。
- 更新 `addons/smart_core/v2/builders/meta_describe_model_response_builder.py`
  - `fields` 输出改为 dict，保持结构化字段面。
- 更新 `addons/smart_core/v2/contracts/results/meta_describe_model_result.py`
  - `fields` 契约类型收敛为 `Dict[str, Any]`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1681.yaml` ✅
- `python3 scripts/verify/v2_meta_describe_model_execution_audit.py --json` ✅
- `python3 scripts/verify/v2_meta_describe_model_contract_audit.py --json` ✅
- `python3 scripts/verify/v2_primary_minimum_business_smoke.py --json` ✅
- `python3 scripts/verify/v2_rollback_readiness_recheck.py --json` ✅
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅
- `python3 -m py_compile addons/smart_core/v2/services/meta_service.py addons/smart_core/v2/services/meta_describe_model_service.py addons/smart_core/v2/builders/meta_describe_model_response_builder.py addons/smart_core/v2/contracts/results/meta_describe_model_result.py` ✅

## 1680 recheck summary
- smoke: PASS
- rollback recheck: PASS
- governance gate: PASS (27/27)
- `docs/ops/ITER-1680-business-usability-validation.md` updated to `GO`.

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅修复 focus-intent contract 字段供给，不触达 ACL/财务/模型结构。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/meta_service.py addons/smart_core/v2/services/meta_describe_model_service.py addons/smart_core/v2/builders/meta_describe_model_response_builder.py addons/smart_core/v2/contracts/results/meta_describe_model_result.py`

## Next suggestion
- 进入 `ITER-1682`：前端交付恢复批次（消费 v2_primary 下已通过的 1680 可用性基线）。
