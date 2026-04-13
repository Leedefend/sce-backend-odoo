# ITER-2026-04-10-1765 Report

## Batch
- Batch: `FORM-Batch2`
- Mode: `implement`
- Stage: `form stat button separation closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `form surface regions / stat button semantics`
- Module Ownership: `smart_core v2 service + verify script`
- Kernel or Scenario: `kernel`
- Reason: 修复运行态中 `button_box` 与 `stat_buttons` 混用，提供前端稳定可消费统计按钮语义。

## Change summary
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 新增统计按钮识别与规范化：
    - `_field_token_index`
    - `_looks_like_stat_button`
    - `_build_stat_button_payload`
  - 调整 `_dedupe_form_action_surfaces`：
    - 从 `button_box` 中识别并迁移统计按钮到 `stat_buttons`
    - 保证两区去重无重叠
    - 为 stat button 补齐 `label/clickable/payload/stat_field/widget`
- 新增 `scripts/verify/form_stat_button_audit.py`
  - 校验 `button_box/stat_buttons` 不重叠
  - 校验 stat button 语义完整
  - 输出 `artifacts/contract/form_stat_buttons_v1.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1765.yaml` ✅
- `python3 -m py_compile addons/smart_core/v2/services/ui_contract_service.py scripts/verify/form_stat_button_audit.py` ✅
- `make restart` ✅
- 重新抓取运行态快照：`tmp/json/form.json` ✅
- `python3 scripts/verify/form_stat_button_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `button_box_count=0`
  - `stat_buttons_count=2`
  - `overlap_count=0`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：当前统计按钮识别包含规则推断，后续可在 parser 提供更强 `oe_stat_button/widget` 元语义后进一步收窄启发式。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/ui_contract_service.py`
- `git restore scripts/verify/form_stat_button_audit.py`

## Next suggestion
- 继续 `FORM-Batch2 / 102-3`：补齐 chatter / attachments surface 承载与关闭原因语义。
