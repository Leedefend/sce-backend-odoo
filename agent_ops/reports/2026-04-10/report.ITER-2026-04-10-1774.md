# ITER-2026-04-10-1774 Report

## Batch
- Batch: `P1-Batch-Import-Dispatch`
- Mode: `implement`
- Stage: `metrics business-model decomposition`

## Architecture declaration
- Layer Target: `Backend data import semantic mapping layer`
- Module: `project metrics import model dispatch`
- Module Ownership: `scripts/ops + project.project + project.cost.ledger`
- Kernel or Scenario: `scenario`
- Reason: 用户要求将导入指标分解到对应业务模型，避免仅写项目名称/描述。

## Change summary
- 更新 `scripts/ops/import_project_metrics_txt_to_xml_and_db.py`
  - 继续产出 XML：`tmp/customer_project_metrics_import.xml`
  - 将字段按业务语义分发到两个业务模型：
    - `project.project`：`budget_total / cost_actual / cost_committed / actual_percent / plan_percent / description`
    - `project.cost.ledger`：导入 `cost_actual` 与 `cost_committed` 为台账金额（按 `source_model/source_id/source_line_id` 幂等 upsert）
  - 新增成本科目自愈（若不存在则创建）：
    - `IMP_ACTUAL`（导入实际成本）
    - `IMP_COMMIT`（导入承诺成本）
  - 回滚快照扩展支持：`project.cost.ledger` 的 created/updated 回滚恢复

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1774.yaml` ✅
- `python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --dry-run` ✅
  - `row_count=694`
  - `mapped_field_coverage`:
    - `budget_total_non_empty=642`
    - `cost_actual_non_empty=607`
    - `cost_committed_non_empty=6`
    - `actual_percent_non_empty=579`
    - `plan_percent_non_empty=579`
- `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo` ✅
  - `processed=694`
  - `project.project updated_count=694`
  - `project.cost.ledger ledger_created_count=613`
- odoo shell 抽样验证 ✅
  - `project_imported=694`
  - `ledger_imported=613`
  - 示例台账：`source_model=customer.metrics.import`，`cost_code=IMP_ACTUAL`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：
  - 当前已将核心指标分发到现有可写业务模型；
  - 部分字段仍仅保留在 `description.metrics`（如税金细项），如需进一步拆分需新批次定义更多目标模型映射与约束。

## Rollback suggestion
- 执行：
  - `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --rollback-tag customer_metrics_import`
- 回滚范围：
  - 回滚本批 `project.project` 字段更新
  - 删除/恢复本批 `project.cost.ledger` 导入记录

## Next suggestion
- 如需继续“对应模型分解”，下一批可新增：
  - 合同口径映射到 `construction.contract`（需定义 partner/tax/状态策略）
  - 进度口径映射到 `project.progress.entry`（需定义 WBS 对齐策略）
