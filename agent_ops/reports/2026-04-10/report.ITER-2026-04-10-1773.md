# ITER-2026-04-10-1773 Report

## Batch
- Batch: `P1-Batch-Import`
- Mode: `implement`
- Stage: `txt -> xml -> db import`

## Architecture declaration
- Layer Target: `Data import execution layer`
- Module: `customer project metrics import utility`
- Module Ownership: `scripts/ops + project.project data`
- Kernel or Scenario: `scenario`
- Reason: 用户要求将 `tmp/项目业务关键信息提取.txt` 导入为有业务意义的字段，而非仅项目名称/描述。

## Change summary
- 更新 `scripts/ops/import_project_metrics_txt_to_xml_and_db.py`
  - 修复表头识别（避免读到字段说明伪表头）
  - 修复 shell 环境继承与事务提交（`env.cr.commit()`）
  - 保留 XML 产出，同时将数据映射到 `project.project` 业务字段：
    - `budget_total` ← `施工合同金额` / `施工合同价_应收应付`
    - `cost_actual` ← `进项上报金额` / `已付款` / `已付款_应收应付`
    - `cost_committed` ← `材料合同+劳务合同+租赁合同+分包合同+其他合同`
    - `actual_percent` / `plan_percent` ← 合同额口径下的进度/收款比例
  - `description` 中保留全量原始 metrics JSON（用于追溯）
  - 回滚快照新增上述字段的旧值保存与恢复
- 产物：
  - `tmp/customer_project_metrics_import.xml`
  - `tmp/customer_metrics_import.rollback.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1773.yaml` ✅
- `python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --dry-run` ✅
  - `header_count=39`
  - `row_count=694`
  - `import_row_count=694`
  - `mapped_field_coverage`:
    - `budget_total_non_empty=642`
    - `cost_actual_non_empty=607`
    - `cost_committed_non_empty=6`
    - `actual_percent_non_empty=579`
    - `plan_percent_non_empty=579`
- `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo` ✅
  - `processed=694`
  - `created_count=0`
  - `updated_count=694`
- 抽样核验（odoo shell）✅：
  - `project.project(1414)` 已写入：
    - `budget_total=3274454.06`
    - `cost_actual=2287794.71`
    - `actual_percent=72.8513`
    - `plan_percent=72.8513`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 说明：
  - 当前映射落在 `project.project` 的可写业务字段；
  - 明细口径（例如税额/开票分层）仍保留在 `description.metrics`，若要拆到更多业务模型需新批次授权。

## Rollback suggestion
- `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --rollback-tag customer_metrics_import`

## Next suggestion
- 若你确认要“多模型落地”（如 `project.cost.ledger` / `construction.contract`），我下一批按你授权范围做模型级分发表与导入（含字段级可写性审计）。
