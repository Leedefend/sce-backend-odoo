# E2E Journey Matrix

Generated from `test_inventory.csv` E2E-classified assets.

## Summary

- E2E-classified assets: `38`
- Strong or near-strong coverage: `10`
- Partial coverage: `2`
- Gaps: `0`

## Coverage Matrix

| Journey | Status | Existing Assets | Gap to Close |
| --- | --- | --- | --- |
| E2E-01: Project administrator creates a project and configures members. | partial_to_strong | `scripts/verify/direct_project_business_browser_acceptance.js`<br>`scripts/verify/project_legacy_fact_browser_acceptance.js`<br>`scripts/verify/scbsly_direct_project_browser_menu_acceptance.js`<br>`scripts/verify/scbsly_direct_project_browser_visible_headers_acceptance.js`<br>`scripts/verify/user_entry_delivery_browser_acceptance.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-02: Cost engineer imports BOQ. | strong | `make test.e2e.fixed_data.odoo`<br>`scripts/e2e/e2e_boq_import_fixed_data_preflight.py`<br>`scripts/e2e/e2e_boq_to_wbs_task_preflight.py` | Keep Odoo fixed-data gate green; add role/browser evidence before release if this journey is user-facing. |
| E2E-03: Project manager generates WBS or tasks from BOQ. | strong | `make test.e2e.fixed_data.odoo`<br>`scripts/e2e/e2e_boq_import_fixed_data_preflight.py`<br>`scripts/e2e/e2e_boq_to_wbs_task_preflight.py` | Keep Odoo fixed-data gate green; add role/browser evidence before release if this journey is user-facing. |
| E2E-04: Commercial user creates budget and contract. | partial_to_strong | `scripts/e2e/e2e_contract_smoke.py`<br>`scripts/verify/unified_page_contract_lite_all_tree_browser_smoke.js`<br>`scripts/verify/unified_page_contract_lite_all_tree_legacy_browser_smoke.js`<br>`scripts/verify/unified_page_contract_lite_all_tree_matrix_browser_smoke.js`<br>`scripts/verify/unified_page_contract_lite_frontend_pilot_browser_smoke.js`<br>`scripts/verify/web_contract_v2_form_shadow_browser_smoke.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-05: Project user starts variation or site instruction workflow. | partial_to_strong | `scripts/verify/direct_acceptance_formal_browser_probe.js`<br>`scripts/verify/direct_acceptance_full_formal_browser_coverage.js`<br>`scripts/verify/workflow_create_statusbar_browser_acceptance.js`<br>`scripts/verify/workflow_evidence_gate_browser_acceptance.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-06: Finance user starts payment request. | partial | `scripts/verify/payment_request_receipt_type_browser_group_smoke.js` | Confirm fixed data, role assertions, failure artifacts, and link to nightly/release gate. |
| E2E-07: Finance user records receipt/payment and invoice. | partial_to_strong | `scripts/ops/validate_finance_browser_acceptance.sh`<br>`scripts/verify/finance_handling_browser_acceptance.js`<br>`scripts/verify/finance_interfund_product_menu_browser_acceptance.js`<br>`scripts/verify/invoice_entry_fact_browser_smoke.js`<br>`scripts/verify/invoice_output_detail_browser_smoke.js`<br>`scripts/verify/payment_request_receipt_type_browser_group_smoke.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-08: Settlement user creates and approves settlement. | strong | `make test.e2e.fixed_data.odoo`<br>`scripts/e2e/e2e_settlement_approval_preflight.py` | Keep Odoo fixed-data gate green; add role/browser evidence before release if this journey is user-facing. |
| E2E-09: Management reviews operating dashboard. | partial_to_strong | `frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs`<br>`scripts/verify/company_operation_summary_browser_acceptance.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-10: Ordinary member is blocked from unauthorized project access. | partial | `scripts/verify/project_legacy_fact_browser_acceptance.js` | Confirm fixed data, role assertions, failure artifacts, and link to nightly/release gate. |
| E2E-11: System administrator adjusts role permissions. | partial_to_strong | `scripts/verify/business_config_runtime_routes_browser_acceptance.mjs`<br>`scripts/verify/finance_interfund_product_menu_browser_acceptance.js`<br>`scripts/verify/scbsly_direct_project_browser_menu_acceptance.js` | Map assertions to acceptance points and add missing business data checks if needed. |
| E2E-12: Release user upgrades and rolls back version. | partial_to_strong | `frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs`<br>`scripts/verify/user_form_preference_full_browser_acceptance.mjs` | Map assertions to acceptance points and add missing business data checks if needed. |

## Required Next Actions

1. Promote only mapped and repeatable scenarios into the release gate.
2. Count a journey as strong only when fixed data and an executable gate are both present.
3. Store screenshot, browser log, server log, and request/response evidence on failure.
4. Keep PR smoke E2E small; run the full 12-journey matrix nightly and before release.
