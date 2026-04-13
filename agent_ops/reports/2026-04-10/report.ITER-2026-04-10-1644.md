# ITER-2026-04-10-1644 Report

## Batch
- Batch: `C/4`
- Mode: `implement`
- Stage: `api.onchange boundary closure`

## Architecture declaration
- Layer Target: `Platform kernel independent rebuild layer`
- Module: `smart_core v2 api onchange boundary closure`
- Module Ownership: `smart_core`
- Kernel or Scenario: `kernel`
- Reason: 按 C 批次将 api.onchange 固化为 service/result/builder 边界样板。

## Change summary
- 更新：`addons/smart_core/v2/handlers/api/onchange.py`
  - handler 改为依赖 `ApiOnchangeServiceV2 + ApiOnchangeResponseBuilderV2`
- 新增：`addons/smart_core/v2/services/api_onchange_service.py`
  - service 负责生成 `ApiOnchangeResultV2`
- 新增：`addons/smart_core/v2/contracts/results/api_onchange_result.py`
  - 固定 api.onchange 结果对象字段
- 新增：`addons/smart_core/v2/builders/api_onchange_response_builder.py`
  - builder 负责响应 data 组装
- 更新导出：
  - `addons/smart_core/v2/services/__init__.py`
  - `addons/smart_core/v2/builders/__init__.py`
  - `addons/smart_core/v2/contracts/results/__init__.py`
- 新增：`scripts/verify/v2_api_onchange_boundary_audit.py`
  - 审计 handler/service/builder 依赖与输出边界
- 更新：`scripts/verify/v2_api_onchange_execution_audit.py`
  - 增加 `phase=boundary_closure` 断言

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1644.yaml` ✅
- `python3 scripts/verify/v2_api_onchange_execution_audit.py --json` ✅
- `python3 scripts/verify/v2_api_onchange_failure_path_audit.py --json` ✅
- `python3 scripts/verify/v2_api_onchange_boundary_audit.py --json` ✅
- `python3 -m py_compile ...` ✅
- `rg -n "ApiOnchangeServiceV2|ApiOnchangeResultV2|ApiOnchangeResponseBuilderV2|return self._builder.build" addons/smart_core/v2/handlers/api/onchange.py` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：本批仅收口分层边界，不引入真实 onchange 联动语义变更。

## Rollback suggestion
- `git restore addons/smart_core/v2/handlers/api/onchange.py addons/smart_core/v2/services/api_onchange_service.py addons/smart_core/v2/services/__init__.py addons/smart_core/v2/builders/api_onchange_response_builder.py addons/smart_core/v2/builders/__init__.py addons/smart_core/v2/contracts/results/api_onchange_result.py addons/smart_core/v2/contracts/results/__init__.py scripts/verify/v2_api_onchange_boundary_audit.py scripts/verify/v2_api_onchange_execution_audit.py`

## Next suggestion
- 进入 `1645`（D/4）：冻结 api.onchange 契约快照并接入治理门禁。
