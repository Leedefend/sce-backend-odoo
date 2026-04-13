# ITER-2026-04-10-1742 Report

## Batch
- Batch: `P1-Batch65`
- Mode: `implement`
- Stage: `FORM-007 render profile backend split remediation`

## Architecture declaration
- Layer Target: `backend scene-orchestration contract supply`
- Module: `ui.contract render profile routing`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: 修复 1741 阻断，打通 create/edit/readonly 三态参数到后端 contract 分流链路。

## Change summary
- 更新 `addons/smart_core/handlers/ui_contract.py`
  - `action_open` 支持 `profile/mode/render_profile` 参数归一。
  - 将 `record_id/render_profile` 透传到 model contract dispatch。
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - `inject_render_hints` 支持 `profile/mode` 别名。
  - 注入三态 `permissions.effective.rights` 与 `render_profile`。
  - `readonly` 强制字段只读；`create` 清除 `res_id` 且降写权限。
- 更新 `addons/smart_core/v2/intents/schemas/ui_contract_schema.py`
  - 保留 `record_id` 与 `render_profile`（含别名）进入 v2 处理链。
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 实现 v2 链路的 render profile 分流应用逻辑。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1742.yaml` ✅
- `python3 scripts/verify/form_render_profiles_audit.py --json` ✅

## Audit conclusion
- 审计状态：`PASS`
- 关键结果：
  - `distinct_profile_labels=3`
  - `has_meaningful_diff=true`
  - `create/edit/readonly` 三态标签与权限差异已可观测

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：仅调整 contract 组织语义与三态输出，不涉及业务事实/ACL/财务语义。

## Rollback suggestion
- `git restore addons/smart_core/handlers/ui_contract.py`
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore addons/smart_core/v2/intents/schemas/ui_contract_schema.py`
- `git restore addons/smart_core/v2/services/ui_contract_service.py`

## Next suggestion
- 进入前端消费对齐批：在详情页消费端根据 `render_profile` 驱动按钮可见性与编辑态切换。
