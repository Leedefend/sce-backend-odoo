# ITER-2026-04-10-1775 Report

## Batch
- Batch: `P1-Batch-Import-Dispatch+Gap`
- Mode: `implement`
- Stage: `multi-model dispatch with explicit mapping gaps`

## Architecture declaration
- Layer Target: `Backend import orchestration layer`
- Module: `customer metrics model dispatch + gap audit`
- Module Ownership: `scripts/ops + project.project + project.cost.ledger`
- Kernel or Scenario: `scenario`
- Reason: 用户要求“真实业务承接”：可映射字段必须落地，不可映射字段必须明确报告缺口。

## Change summary
- 更新 `scripts/ops/import_project_metrics_txt_to_xml_and_db.py`
  - 新增双模型分发：
    - `project.project`: `budget_total/cost_actual/cost_committed/actual_percent/plan_percent/description`
    - `project.cost.ledger`: `cost_actual` + `材料/劳务/租赁/分包/其他合同` 分量金额
  - 新增成本科目自愈：`IMP_ACTUAL/IMP_MATERIAL/IMP_LABOR/IMP_RENT/IMP_SUBCON/IMP_OTHER`
  - 新增字段级缺口报告输出：`--gap-report artifacts/import/customer_metrics_mapping_gap_v1.json`
  - 回滚能力扩展到 `project.cost.ledger`（created + updated 恢复）

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1775.yaml` ✅
- `python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --dry-run --gap-report artifacts/import/customer_metrics_mapping_gap_v1.json` ✅
  - `row_count=694`
  - `mapped_source_fields=13`
  - `unmapped_source_fields=25`
- `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --gap-report artifacts/import/customer_metrics_mapping_gap_v1.json` ✅
  - `project.project updated_count=694`
  - `project.cost.ledger ledger_created_count=703`
  - `project.cost.ledger ledger_updated_count=614`
- 抽样验证（odoo shell）✅
  - `project_imported=694`
  - `ledger_imported=1317`
  - 存在 `source_model=customer.metrics.import` 且按 `source_line_id` 幂等更新

## Gap report
- 产物：`artifacts/import/customer_metrics_mapping_gap_v1.json`
- 口径：
  - 已映射字段：13
  - 未映射字段：25
- 主要缺口类型：
  - `NEEDS_ACCOUNTING_CONTEXT`：开票/税额类字段需会计凭证上下文
  - `DERIVED_FUNDING_FIELD`：资金余额/退回类字段为流程派生结果
  - `COMPUTED_METRIC`：利润/收支/差额类字段为计算指标
  - `NO_SAFE_WRITABLE_TARGET`：当前授权范围内无语义等价可写字段

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：
  - 已映射字段均落在现有可写模型与可追溯来源标记下；
  - 未映射字段已给出明确缺口与建议承接模型，避免错误落库。

## Rollback suggestion
- `COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev python3 scripts/ops/import_project_metrics_txt_to_xml_and_db.py --txt tmp/项目业务关键信息提取.txt --xml tmp/customer_project_metrics_import.xml --db sc_demo --rollback-tag customer_metrics_import`

## Next suggestion
- 若你同意进入会计/资金域专线批次，可基于 gap 报告逐项建立 `account.*` 与资金流程模型映射（需独立高风险授权任务）。
