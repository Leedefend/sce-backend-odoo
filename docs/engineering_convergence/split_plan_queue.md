# Split Plan Queue

Generated from `complexity_budget_report.md` split-plan-required files.

## Summary

- Split-plan files: `43`
- P0: `1`
- P1: `23`
- P2: `19`

## Queue

| Priority | Lines | Owner | File | Decomposition Direction |
| --- | ---: | --- | --- | --- |
| P0 | 7975 | Frontend owner | `frontend/apps/web/src/pages/ContractFormPage.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P1 | 4820 | Platform owner | `addons/smart_core/utils/contract_governance.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 4491 | Platform owner | `addons/smart_core/handlers/ui_contract_v2.py` | Extract parsing, validation, assembly, and response mapping into owned services. |
| P1 | 4400 | Construction backend owner | `addons/smart_construction_core/core_extension.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 3831 | Frontend owner | `frontend/apps/web/src/views/ActionView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P1 | 3747 | Frontend owner | `frontend/apps/web/src/views/MenuConfigView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P1 | 3633 | Platform owner | `addons/smart_core/handlers/form_field_configuration.py` | Extract parsing, validation, assembly, and response mapping into owned services. |
| P1 | 3525 | Frontend owner | `frontend/apps/web/src/views/HomeView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P1 | 3323 | Construction backend owner | `addons/smart_construction_core/tests/test_p0_state_closure.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P1 | 3317 | Frontend owner | `frontend/apps/web/src/pages/ListPage.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P1 | 3202 | Platform owner | `addons/smart_core/tests/test_form_field_configuration_params.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P1 | 3092 | Construction backend owner | `addons/smart_construction_core/models/support/p1_daily_business_visible_alias_fields.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P1 | 3041 | Platform owner | `addons/smart_core/core/workspace_home_contract_builder.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 3013 | Platform owner | `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py` | Separate parser/assembler/dispatcher responsibilities and preserve backend source-of-truth boundary. |
| P1 | 2903 | Platform owner | `addons/smart_core/tests/test_menu_configuration_audit.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P1 | 2452 | Platform owner | `addons/smart_core/core/unified_page_contract_v2_assembler.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 2306 | Platform owner | `addons/smart_core/handlers/system_init.py` | Extract parsing, validation, assembly, and response mapping into owned services. |
| P1 | 2196 | Platform owner | `addons/smart_core/handlers/api_data.py` | Extract parsing, validation, assembly, and response mapping into owned services. |
| P1 | 2039 | Platform owner | `addons/smart_core/tests/test_ui_contract_v2_boundaries.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P1 | 1850 | Platform owner | `addons/smart_core/handlers/menu_configuration.py` | Extract parsing, validation, assembly, and response mapping into owned services. |
| P1 | 1741 | Platform owner | `addons/smart_core/core/page_contracts_builder.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 1634 | Platform owner | `addons/smart_core/core/scene_ready_contract_builder.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P1 | 1566 | Platform owner | `addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py` | Separate parser/assembler/dispatcher responsibilities and preserve backend source-of-truth boundary. |
| P1 | 1552 | Platform owner | `addons/smart_core/tests/test_odoo_native_alignment_boundaries.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P2 | 2830 | Construction backend owner | `addons/smart_construction_core/models/core/material_acceptance.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 2594 | Frontend owner | `frontend/apps/web/src/views/MyWorkView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P2 | 2585 | Construction backend owner | `addons/smart_construction_core/tests/test_user_feedback_business_views.py` | Split fixtures, scenario builders, and assertion groups by behavior area. |
| P2 | 2529 | Construction backend owner | `addons/smart_construction_core/views/menu_business_taxonomy.xml` | Split data/view records by product domain and manifest load order. |
| P2 | 2385 | Frontend owner | `frontend/apps/web/src/layouts/AppShell.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P2 | 2289 | Construction backend owner | `addons/smart_construction_core/models/core/project_core.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 2051 | DevOps owner | `scripts/verify/backend_business_fact_model_audit.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P2 | 2005 | Frontend owner | `frontend/apps/web/src/stores/session.ts` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P2 | 1974 | Construction backend owner | `addons/smart_construction_core/models/core/payment_request.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 1847 | Construction backend owner | `addons/smart_construction_core/models/support/product_policy_sync.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 1844 | DevOps owner | `scripts/migration/scbs_55_legacy_visible_field_full_reconcile_probe.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P2 | 1739 | Frontend owner | `frontend/apps/web/src/views/SceneView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P2 | 1689 | DevOps owner | `scripts/verify/industry_module_product_boundary_guard.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P2 | 1597 | Construction backend owner | `addons/smart_construction_core/models/support/direct_acceptance_formal_visible_fields.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 1558 | Construction backend owner | `addons/smart_construction_core/models/support/contract_center.py` | Extract service methods for cross-model workflow, amount, and policy logic. |
| P2 | 1525 | Frontend owner | `frontend/apps/web/src/views/RecordView.vue` | Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell. |
| P2 | 1523 | Construction backend owner | `addons/smart_construction_core/wizard/project_boq_import_wizard.py` | Define owner-specific decomposition plan before adding unrelated behavior. |
| P2 | 599 | DevOps owner | `scripts/audit/smoke_role_matrix.sh` | Move reusable logic into small scripts and keep shell as thin entrypoint. |
| P2 | 551 | DevOps owner | `scripts/ops/audit_project_actions.sh` | Move reusable logic into small scripts and keep shell as thin entrypoint. |

## Enforcement Rule

- P0 files require a split plan before accepting non-defect feature additions.
- P1 files require owner review when touched.
- P2 files may be handled opportunistically, but should not grow without reason.
