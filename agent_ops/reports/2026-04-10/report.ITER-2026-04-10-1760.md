# ITER-2026-04-10-1760 Report

## Batch
- Batch: `FORM-Batch1`
- Mode: `implement`
- Stage: `form contract truth-source closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `ui.contract form truth source governance`
- Module Ownership: `smart_core + contract builders + verify scripts`
- Kernel or Scenario: `kernel`
- Reason: 收敛 form 布局唯一真值源，消除 `views.form.layout` 与 `semantic_page.form_semantics.layout` 双树并存。

## Change summary
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - 移除 `semantic_page.form_semantics.layout` 整树复制。
  - 改为设置引用语义：`layout_source=views.form.layout`，并保留 `layout_section_count`。
- 更新 `addons/smart_core/handlers/load_contract.py`
  - `form_semantics` 不再输出 `layout` 整树，改为 `layout_source=views.form.layout`。
- 新增 `scripts/verify/form_layout_single_source_audit.py`
  - 输出 `artifacts/contract/form_layout_single_source_v1.json`。
  - 同时校验：
    - payload 是否仍有重复 layout
    - 代码侧是否已移除复制并设置 `layout_source`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1760.yaml` ✅
- `python3 scripts/verify/form_layout_single_source_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `snapshot_outdated=true`（当前 `tmp/json/form.json` 为旧快照，尚未反映新代码输出）

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：审计发现输入快照为改动前数据；代码侧门禁通过，待你重启后端并重新抓取 `form.json` 做运行态复核。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore addons/smart_core/handlers/load_contract.py`
- `git restore scripts/verify/form_layout_single_source_audit.py`

## Next suggestion
- 继续 `FORM-Batch1 / Task 101-2`：字段真值源统一（`fields` canonical + `layout.fieldInfo` 轻量化）。
