# Legacy DB Business Fact Completeness Screen v1

Status: `PASS`

Source: `legacy-sqlserver:LegacyDb`

This screen connects directly to the legacy SQL Server database and runs
read-only aggregate queries. It classifies source business fact lanes by core
fact completeness before choosing the next migration assetization order.

## Lane Completeness

| Lane | Source table | Asset status | Raw | Active | Core complete | Core complete / active | Classification |
|---|---|---|---:|---:|---:|---:|---|
| project | BASE_SYSTEM_PROJECT | assetized | 755 | 694 | 694 | 100.0% | core_master_already_assetized |
| user | BASE_SYSTEM_USER | assetized | 101 | 41 | 41 | 100.0% | authority_anchor_already_assetized |
| project_member | BASE_SYSTEM_PROJECT_USER | assetized | 21390 | 21390 | 21390 | 100.0% | relation_already_assetized_with_user_gap |
| revenue_contract | T_ProjectContract_Out | assetized | 1694 | 1629 | 1629 | 100.0% | business_header_already_assetized_with_residual_blockers |
| receipt | C_JFHKLR | assetized | 7412 | 7363 | 5445 | 73.95% | business_request_already_assetized |
| outflow_request | C_ZFSQGL | assetized | 13646 | 13483 | 13256 | 98.32% | business_request_already_assetized |
| actual_outflow | T_FK_Supplier | not_assetized | 13629 | 13573 | 13350 | 98.36% | high_completeness_next_core_fact |
| supplier_contract | T_GYSHT_INFO | not_assetized | 5535 | 5442 | 5442 | 100.0% | high_completeness_contract_fact |
| outflow_request_line | C_ZFSQGL_CB | not_assetized | 17413 | 17413 | 16566 | 95.14% | detail_fact_with_parent_anchor |
| receipt_invoice | C_JFHKLR_CB | not_assetized | 4491 | 4491 | 4481 | 99.78% | high_completeness_auxiliary_fact |
| attachment | BASE_SYSTEM_FILE | not_assetized | 126967 | 125213 | 125213 | 100.0% | evidence_auxiliary_large_volume |
| workflow | S_Execute_Approval | not_assetized | 163245 | 163245 | 163245 | 100.0% | runtime_process_fact_high_volume |

## Recommended Next Order

| priority | lane | source table | complete facts | complete / active | strategy |
|---:|---|---|---:|---:|---|
| 1 | actual_outflow | T_FK_Supplier | 13350 | 98.36% | screen_then_assetize |
| 2 | supplier_contract | T_GYSHT_INFO | 5442 | 100.0% | screen_mapping_model_then_assetize |
| 3 | receipt_invoice | C_JFHKLR_CB | 4481 | 99.78% | assetize_as_auxiliary_fact |
| 4 | outflow_request_line | C_ZFSQGL_CB | 16566 | 95.14% | assetize_after_parent_request |
| 5 | attachment | BASE_SYSTEM_FILE | 125213 | 100.0% | defer_until_parent_assets_stable |
| 6 | workflow | S_Execute_Approval | 163245 | 100.0% | defer_or_summarize |

## Reasoning

- `1. actual_outflow`: 实际付款具备项目、对方、金额、日期，且多数可关联支出申请，是下一个最有价值事实层。
- `2. supplier_contract`: 供应商合同量大且项目/供应商/金额完整度高，应在实际付款前后尽快建立合同锚点。
- `3. receipt_invoice`: 收款发票明细几乎完整，但属于票据辅助事实，不应早于核心付款/供应商合同。
- `4. outflow_request_line`: 支出申请明细大部分有父单和金额，适合作为 outflow request 的 detail/辅助事实层。
- `5. attachment`: 附件有较完整 BILLID/path，但体量大且依赖父业务单据稳定，后置。
- `6. workflow`: 审批流事实完整但属于运行过程轨迹；先迁核心事实，再按摘要/审计策略处理。

## Decision

`prioritize_supplier_contract_and_actual_outflow_before_auxiliary_invoice_attachment_workflow`

## Boundary

- DB writes: `0`
- Odoo shell: `false`
- No asset generation in this screen
- Workflow, attachment, settlement, ledger, and accounting semantics stay out
  of the next core fact batch unless opened by a dedicated task.
